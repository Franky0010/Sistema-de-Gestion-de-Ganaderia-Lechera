"""Cookies de sesión y CSRF (detalle de transporte HTTP)."""
import os

from fastapi import Request, Response


def cookie_segura(request: Request) -> bool:
    """Secure en HTTPS. Detrás de un proxy, arrancar uvicorn con --proxy-headers o
    definir POC_COOKIE_SECURE=1."""
    return request.url.scheme == "https" or os.getenv("POC_COOKIE_SECURE", "").lower() in {"1", "true"}


def poner_cookie(response: Response, request: Request, nombre: str, valor: str) -> None:
    response.set_cookie(nombre, valor, httponly=True, secure=cookie_segura(request), samesite="lax", path="/")


def borrar_cookie(response: Response, request: Request, nombre: str) -> None:
    response.delete_cookie(nombre, path="/", httponly=True, secure=cookie_segura(request), samesite="lax")
