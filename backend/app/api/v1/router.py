from fastapi import APIRouter

from app.api.v1.health.routes import router as health_router
from app.api.v1.auth.routes import router as auth_router
from app.api.v1.users.routes import router as users_router


api_router_v1 = APIRouter(tags=["api-v1"])

api_router_v1.include_router(health_router)
api_router_v1.include_router(auth_router)
api_router_v1.include_router(users_router)

