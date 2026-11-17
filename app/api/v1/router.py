"""Agrupa los routers de la versión 1 bajo el prefijo /api/v1."""
from fastapi import APIRouter

from app.api.v1 import animales, auditoria, auth, usuarios

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(usuarios.router)
api_router.include_router(auditoria.router)
api_router.include_router(animales.router)
