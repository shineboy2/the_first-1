import base64
import uuid
import random
import string
from io import BytesIO
import redis
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from captcha.image import ImageCaptcha

from core.config import settings

router = APIRouter(prefix="/captcha", tags=["Authentication"])

image_captcha = ImageCaptcha(width=280, height=90, fonts=None)

CAPTCHA_TTL = 300  # 5 minutes


class CaptchaResponse(BaseModel):
    captcha_id: str
    image_base64: str
    image_url: str


def _get_redis():
    return redis.from_url(str(settings.REDIS_URL), decode_responses=False)


@router.get(
    "/",
    response_model=CaptchaResponse,
    summary="Generate Captcha",
    description=(
        "یک کپچا جدید تولید می‌کند. "
        "`captcha_id` را نگه دارید و برای مشاهده تصویر از `GET /captcha/image/{captcha_id}` استفاده کنید. "
        "پس از خواندن تصویر، `captcha_id` و متن را در `/auth/login` ارسال کنید."
    ),
)
async def generate_captcha():
    # Generate random text — remove easily confused chars
    chars = string.ascii_uppercase + string.digits
    chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
    captcha_text = ''.join(random.choices(chars, k=5))

    # Generate image
    image_bytes_io = BytesIO()
    image_captcha.generate_image(captcha_text).save(image_bytes_io, format='PNG')
    raw_bytes = image_bytes_io.getvalue()
    image_b64 = base64.b64encode(raw_bytes).decode('utf-8')

    captcha_id = str(uuid.uuid4())
    try:
        rc = _get_redis()
        pipe = rc.pipeline()
        # Store text (for verification) — decode_responses=False so store as bytes
        pipe.setex(f"captcha:{captcha_id}", CAPTCHA_TTL, captcha_text.encode())
        # Store raw image bytes (for /image endpoint)
        pipe.setex(f"captcha_img:{captcha_id}", CAPTCHA_TTL, raw_bytes)
        pipe.execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to connect to Redis")

    return CaptchaResponse(
        captcha_id=captcha_id,
        image_base64=f"data:image/png;base64,{image_b64}",
        image_url=f"/api/v1/captcha/image/{captcha_id}",
    )


@router.get(
    "/image/{captcha_id}",
    response_class=Response,
    summary="View Captcha Image",
    description=(
        "تصویر کپچا را به صورت PNG برمی‌گرداند. "
        "این آدرس را مستقیم در مرورگر باز کنید تا تصویر کپچا را ببینید. "
        "مشاهده تصویر کپچا را حذف **نمی‌کند** — فقط ارسال صحیح در `/auth/login` آن را باطل می‌کند."
    ),
    responses={
        200: {"content": {"image/png": {}}, "description": "تصویر PNG کپچا"},
        404: {"description": "کپچا یافت نشد یا منقضی شده است"},
    },
)
async def get_captcha_image(captcha_id: str):
    try:
        rc = _get_redis()
        raw_bytes = rc.get(f"captcha_img:{captcha_id}")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to connect to Redis")

    if not raw_bytes:
        raise HTTPException(status_code=404, detail="Captcha not found or expired")

    return Response(content=raw_bytes, media_type="image/png")


def verify_captcha(captcha_id: str, solution: str) -> bool:
    if not captcha_id or not solution:
        return False

    try:
        rc = _get_redis()
        key = f"captcha:{captcha_id}"
        stored = rc.get(key)

        if stored:
            # stored may be bytes or str depending on decode_responses
            stored_str = stored.decode() if isinstance(stored, bytes) else stored
            if stored_str.lower() == solution.lower():
                # Invalidate both keys on success
                rc.delete(key, f"captcha_img:{captcha_id}")
                return True

        return False
    except Exception:
        return False
