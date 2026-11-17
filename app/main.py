"""API: rutas versionadas /api/v1 (sesión y usuarios, Sprint 1) y las rutas del PoC
(/animales, /ordenos), que siguen usando X-Usuario como sustituto de la sesión hasta el Sprint 2.

Este módulo solo compone la aplicación: crea FastAPI, instala los manejadores de error,
registra los routers y define el arranque. No contiene rutas ni reglas de negocio."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.manejadores_errores import instalar_manejadores
from app.api.poc import animales as poc_animales
from app.api.poc import ordenos as poc_ordenos
from app.api.v1.router import api_router
from app.db.inicializacion import inicializar_base
from app.db.session import engine


@asynccontextmanager
async def lifespan(_app: FastAPI):
    inicializar_base(engine)
    yield


app = FastAPI(title="PoC - Registro de ordeños sin duplicados", lifespan=lifespan)
instalar_manejadores(app)
app.include_router(api_router)
app.include_router(poc_animales.router)
app.include_router(poc_ordenos.router)
