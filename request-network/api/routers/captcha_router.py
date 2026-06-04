import base64
import uuid
import random
import string
from io import BytesIO
import redis
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from captcha.image import ImageCaptcha

from core.config import settings

router = APIRouter(prefix="/captcha", tags=["auth"])

image_captcha = ImageCaptcha(width=280, height=90, fonts=None)

class CaptchaResponse(BaseModel):
    captcha_id: str
    image_base64: str

@router.get("/", response_model=CaptchaResponse)
async def generate_captcha():
    # Generate random text (4-5 chars, uppercase and numbers to avoid confusion)
    chars = string.ascii_uppercase + string.digits
    chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
    captcha_text = ''.join(random.choices(chars, k=5))
    
    # Generate image
    image_bytes = BytesIO()
    image_captcha.generate_image(captcha_text).save(image_bytes, format='PNG')
    image_b64 = base64.b64encode(image_bytes.getvalue()).decode('utf-8')
    
    # Generate ID and save to Redis with 5 minutes expiration
    captcha_id = str(uuid.uuid4())
    redis_client = redis.from_url(str(settings.REDIS_URL), decode_responses=True)
    try:
        redis_client.setex(f"captcha:{captcha_id}", 300, captcha_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to connect to Redis")
        
    return CaptchaResponse(
        captcha_id=captcha_id,
        image_base64=f"data:image/png;base64,{image_b64}"
    )

def verify_captcha(captcha_id: str, solution: str) -> bool:
    if not captcha_id or not solution:
        return False
        
    redis_client = redis.from_url(str(settings.REDIS_URL), decode_responses=True)
    try:
        key = f"captcha:{captcha_id}"
        stored = redis_client.get(key)
        
        if stored and stored.lower() == solution.lower():
            redis_client.delete(key) # Single use
            return True
            
        return False
    except Exception:
        return False
