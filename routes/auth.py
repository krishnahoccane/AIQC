from fastapi import APIRouter, Request
from middleware.rate_limit import limiter
from schemas.user_schema import LoginSchema

router = APIRouter()

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, data: LoginSchema):
    return {"message": "Login logic here"}