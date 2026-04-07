from fastapi import APIRouter

from app.api.endpoints import auth, users, transactions, analytics, admin

api_router = APIRouter()
api_router.include_router(auth.router,         prefix="/auth",         tags=["auth"])
api_router.include_router(users.router,        prefix="/users",        tags=["users"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(analytics.router,    prefix="/analytics",    tags=["analytics"])
api_router.include_router(admin.router,        prefix="/admin",        tags=["admin"])
