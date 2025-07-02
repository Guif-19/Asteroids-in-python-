# vetor.py (VERSÃO FINAL COM GETTERS E SETTERS)

import math

class Vetor2D:
    def __init__(self, x=0.0, y=0.0):
        self._x = float(x)
        self._y = float(y)

    # --- Getters e Setters ---
    def get_x(self) -> float:
        """Retorna o valor do componente x."""
        return self._x

    def get_y(self) -> float:
        """Retorna o valor do componente y."""
        return self._y

    def set_x(self, novo_x: float):
        """Define um novo valor para o componente x."""
        self._x = float(novo_x)

    def set_y(self, novo_y: float):
        """Define um novo valor para o componente y."""
        self._y = float(novo_y)

    # --- Métodos de Operação (atualizados para usar _x e _y) ---
    def __add__(self, outro: 'Vetor2D') -> 'Vetor2D':
        return Vetor2D(self._x + outro.get_x(), self._y + outro.get_y())

    def __sub__(self, outro: 'Vetor2D') -> 'Vetor2D':
        return Vetor2D(self._x - outro.get_x(), self._y - outro.get_y())

    def __mul__(self, escalar: float) -> 'Vetor2D':
        return Vetor2D(self._x * escalar, self._y * escalar)
    
    def __rmul__(self, escalar: float) -> 'Vetor2D':
        return self.__mul__(escalar)

    def __neg__(self):
        return Vetor2D(-self._x, -self._y)

    def __truediv__(self, escalar: float) -> 'Vetor2D':
        if escalar == 0:
            raise ZeroDivisionError("Divisão de Vetor2D por zero.")
        return Vetor2D(self._x / escalar, self._y / escalar)

    def magnitude(self) -> float:
        return math.hypot(self._x, self._y)

    def normalizar(self) -> 'Vetor2D':
        mag = self.magnitude()
        if mag == 0:
            return Vetor2D(0, 0)
        return self / mag

    def rotacionar(self, angulo_rad: float) -> 'Vetor2D':
        cos_a = math.cos(angulo_rad)
        sin_a = math.sin(angulo_rad)
        novo_x = self._x * cos_a - self._y * sin_a
        novo_y = self._x * sin_a + self._y * cos_a
        return Vetor2D(novo_x, novo_y)
    
    def distancia_ate(self, outro: 'Vetor2D') -> float:
        return (self - outro).magnitude()
    
    def dot(self, outro: 'Vetor2D') -> float:
        return self._x * outro.get_x() + self._y * outro.get_y()

    # --- Métodos de Conversão ---
    def to_dict(self) -> dict:
        return {"x": self._x, "y": self._y}

    @classmethod
    def from_dict(cls, data: dict) -> 'Vetor2D':
        return cls(data["x"], data["y"])
    
    def para_tupla(self) -> tuple[int, int]:
        return (int(self._x), int(self._y))

    def copia(self) -> 'Vetor2D':
        """Retorna uma cópia deste vetor."""
        return Vetor2D(self._x, self._y)