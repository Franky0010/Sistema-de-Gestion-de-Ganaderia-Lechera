"""Límite de intentos de login en memoria (un solo proceso; suficiente para el prototipo)."""
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta


class LimitadorIntentos:
    def __init__(self, maximo: int = 5, ventana: timedelta = timedelta(minutes=15)):
        self.maximo = maximo
        self.ventana = ventana
        self._fallos = defaultdict(deque)
        self._lock = threading.Lock()

    def _purgar(self, clave, instante):
        fallos = self._fallos[clave]
        while fallos and instante - fallos[0] >= self.ventana:
            fallos.popleft()
        if not fallos:
            del self._fallos[clave]

    def segundos_de_espera(self, clave: str, instante: datetime) -> int:
        """0 si puede intentar; si no, segundos hasta que se libere un intento."""
        with self._lock:
            self._purgar(clave, instante)
            fallos = self._fallos.get(clave)
            if fallos and len(fallos) >= self.maximo:
                restante = fallos[0] + self.ventana - instante
                return max(1, int(restante.total_seconds()) + 1)
            return 0

    def registrar_fallo(self, clave: str, instante: datetime) -> None:
        with self._lock:
            self._fallos[clave].append(instante)

    def limpiar(self, clave: str) -> None:
        with self._lock:
            self._fallos.pop(clave, None)

    def reiniciar(self) -> None:
        with self._lock:
            self._fallos.clear()


limitador_login = LimitadorIntentos()
