"""
Rate Limit Grace Period Middleware
برای اضافه کردن headers و هشدارات به پاسخ‌ها
"""

from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

from rate_limiter import RateLimiter, LimitLevel
from db.redis_client import get_redis_client
from db.session import AsyncSessionFactory
from models import User, SubUser
from sqlalchemy import select


logger = logging.getLogger(__name__)


class RateLimitGracePeriodMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling rate limit grace period
    
    - Adds rate limit headers to all responses
    - Checks for 80% warning threshold
    - Handles soft block (110%) with 5-minute grace
    - Enforces hard block (100%)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        بررسی Rate Limit و اضافه کردن headers
        """
        
        # Skip rate limiting برای بعضی endpoints
        if request.url.path in ["/health", "/health/ready", "/health/detailed", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # فقط برای authenticated requests
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await call_next(request)
            
        token = auth_header.split(" ")[1]
        
        try:
            # We import here to avoid circular imports if any
            from auth.security import decode_access_token
            token_data = decode_access_token(token)
            if not token_data or not token_data.user_id:
                return await call_next(request)
            user_id = str(token_data.user_id)
        except Exception:
            return await call_next(request)
            
        # Unify Sub-User ID header
        sub_user_id = request.headers.get("X-Sub-User-Id")
        
        try:
            redis_client = await get_redis_client()
            rate_limiter = RateLimiter(redis_client.client)

            async with AsyncSessionFactory() as db:
                # Fetch Enterprise User to get profile and limits
                stmt = select(User).where(User.id == user_id)
                result = await db.execute(stmt)
                enterprise_user = result.scalars().first()

                if not enterprise_user:
                    return await call_next(request)
                
                profile = enterprise_user.profile_type

                # SubUser Logic
                if sub_user_id:
                    subuser_limits = {
                        "minute": enterprise_user.subuser_rate_limit_per_minute,
                        "hour": enterprise_user.subuser_rate_limit_per_hour,
                        "day": enterprise_user.subuser_rate_limit_per_day,
                    }

                    # JIT Provisioning
                    stmt_sub = select(SubUser).where(
                        SubUser.enterprise_user_id == enterprise_user.id,
                        SubUser.external_user_id == sub_user_id
                    )
                    sub_result = await db.execute(stmt_sub)
                    sub_user = sub_result.scalars().first()

                    if not sub_user:
                        # Check Max Subusers Limit
                        max_subusers = getattr(enterprise_user, 'max_subusers', 10)
                        count_stmt = select(db.func.count(SubUser.id)).where(SubUser.enterprise_user_id == enterprise_user.id)
                        current_subusers = await db.scalar(count_stmt)
                        
                        if current_subusers >= max_subusers:
                            return JSONResponse(
                                status_code=403,
                                content={"detail": f"Maximum number of sub-users ({max_subusers}) reached for this enterprise account."},
                            )
                        
                        # Validate sub_user_id format
                        import re
                        if not re.match(r'^[\w\-]{1,255}$', sub_user_id):
                            return JSONResponse(
                                status_code=400,
                                content={"detail": "Invalid X-Sub-User-Id format. Use 1-255 alphanumeric characters, dashes, or underscores."},
                            )
                            
                        sub_user = SubUser(
                            enterprise_user_id=enterprise_user.id,
                            external_user_id=sub_user_id
                        )
                        db.add(sub_user)
                        await db.commit()

                    # Update last request stats for sub-user
                    sub_user.last_request_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown").split(",")[0].strip()
                    sub_user.last_request_at = db.func.now()
                    sub_user.request_count = (sub_user.request_count or 0) + 1
                    db.add(sub_user)
                    await db.commit()

                    # Check Sub-user Rate Limit
                    sub_level, sub_details = await rate_limiter.check_subuser_limit(
                        str(enterprise_user.id), sub_user_id, subuser_limits
                    )

                    if sub_level == LimitLevel.EXCEEDED:
                        logger.warning(f"Subuser {sub_user_id} exceeded rate limit")
                        return JSONResponse(
                            status_code=429,
                            content={
                                "detail": f"Subuser Rate limit exceeded for {sub_details['hit_limit']}",
                                "retry_after": 60,
                                "limit_exceeded": sub_details["hit_limit"],
                            },
                            headers={"X-RateLimit-Status": "EXCEEDED"}
                        )

            # بررسی Rate Limit اصلی اینترپرایز
            limit_level, details = await rate_limiter.check_limit(user_id, profile)
            
            # ✅ OK - ادامه عادی
            if limit_level == LimitLevel.OK:
                response = await call_next(request)
                
                # اضافه کردن headers
                response.headers["X-RateLimit-Limit-Minute"] = str(details.get("hit_limit", "∞"))
                response.headers["X-RateLimit-Remaining-Minute"] = str(details["remaining_minute"])
                response.headers["X-RateLimit-Remaining-Hour"] = str(details["remaining_hour"])
                response.headers["X-RateLimit-Remaining-Day"] = str(details["remaining_day"])
                
                # Increment counter بعد از پاسخ
                await rate_limiter.increment_counter(user_id)
                if sub_user_id:
                    await rate_limiter.increment_subuser_counter(user_id, sub_user_id)
                
                return response

            
            # ⚠️ WARNING (80%) - اجازه دارد اما هشدار
            elif limit_level == LimitLevel.WARNING:
                # فعال‌سازی soft block برای 5 دقیقه
                await rate_limiter.activate_soft_block(user_id, details.get("hit_limit", "hour"))
                
                response = await call_next(request)
                
                # Add warning headers
                response.headers["X-RateLimit-Status"] = "WARNING"
                response.headers["X-RateLimit-Message"] = details["message"]
                response.headers["X-RateLimit-Remaining-Minute"] = str(details["remaining_minute"])
                response.headers["X-RateLimit-Remaining-Hour"] = str(details["remaining_hour"])
                response.headers["X-RateLimit-Remaining-Day"] = str(details["remaining_day"])
                
                # Increment counter
                await rate_limiter.increment_counter(user_id)
                if sub_user_id:
                    await rate_limiter.increment_subuser_counter(user_id, sub_user_id)

                
                logger.warning(f"User {user_id} reached {details['hit_limit']} warning threshold")
                
                return response
            
            # 🔶 SOFT BLOCK (110%, grace period فعال) - اجازه دارد اما محدود
            elif limit_level == LimitLevel.SOFT_BLOCK:
                response = await call_next(request)
                
                # Add soft block headers
                response.headers["X-RateLimit-Status"] = "SOFT_BLOCK"
                response.headers["X-RateLimit-Message"] = "Soft block active - grace period enabled (5 min)"
                response.headers["X-RateLimit-Grace-Period-Ends"] = details.get("grace_period_ends_at", "")
                response.headers["X-RateLimit-Remaining-Minute"] = str(max(0, details["remaining_minute"]))
                response.headers["X-RateLimit-Remaining-Hour"] = str(max(0, details["remaining_hour"]))
                response.headers["X-RateLimit-Remaining-Day"] = str(max(0, details["remaining_day"]))
                
                # Increment counter
                await rate_limiter.increment_counter(user_id)
                if sub_user_id:
                    await rate_limiter.increment_subuser_counter(user_id, sub_user_id)

                
                logger.warning(f"User {user_id} in soft block grace period for {details['hit_limit']}")
                
                return response
            
            # ❌ EXCEEDED (100%, hard block) - مسدود شود
            elif limit_level == LimitLevel.EXCEEDED:
                logger.warning(f"User {user_id} exceeded rate limit for {details['hit_limit']}")
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Rate limit exceeded for {details['hit_limit']}",
                        "retry_after": 60 if details["hit_limit"] == "minute" else 300,
                        "remaining": {
                            "minute": details["remaining_minute"],
                            "hour": details["remaining_hour"],
                            "day": details["remaining_day"],
                        },
                        "limit_exceeded": details["hit_limit"],
                    },
                    headers={
                        "X-RateLimit-Status": "EXCEEDED",
                        "X-RateLimit-Message": details["message"],
                        "Retry-After": str(60 if details["hit_limit"] == "minute" else 300),
                        "X-RateLimit-Remaining-Minute": str(details["remaining_minute"]),
                        "X-RateLimit-Remaining-Hour": str(details["remaining_hour"]),
                        "X-RateLimit-Remaining-Day": str(details["remaining_day"]),
                    }
                )
            
        except Exception as e:
            logger.error(f"Rate limit middleware error: {e}")
            # در صورت error، ادامه بدهید
            response = await call_next(request)
            return response
        
        # Default: ادامه عادی
        response = await call_next(request)
        return response
