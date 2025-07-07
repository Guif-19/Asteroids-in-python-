# arquivo: vetor.py
import math

class Vetor2D:
    def __init__(self, x=0.0, y=0.0):
        self.__x = float(x)
        self.__y = float(y)

    # --- Getters e Setters ---
    def get_x(self) -> float: return self.__x
    def get_y(self) -> float: return self.__y
    def set_x(self, novo_x: float): self.__x = float(novo_x)
    def set_y(self, novo_y: float): self.__y = float(novo_y)

    # --- Métodos de Operação ---
    def __add__(self, outro: 'Vetor2D') -> 'Vetor2D':
        return Vetor2D(self.__x + outro.get_x(), self.__y + outro.get_y())

    def __sub__(self, outro: 'Vetor2D') -> 'Vetor2D':
        return Vetor2D(self.__x - outro.get_x(), self.__y - outro.get_y())

    def __mul__(self, escalar: float) -> 'Vetor2D':
        return Vetor2D(self.__x * escalar, self.__y * escalar)
    
    def __rmul__(self, escalar: float) -> 'Vetor2D':
        return self.__mul__(escalar)

    def __neg__(self):
        return Vetor2D(-self.__x, -self.__y)

    # --- MÉTODO ADICIONADO ---
    def __truediv__(self, escalar: float) -> 'Vetor2D':
        """ Define o comportamento do operador de divisão (/). """
        if escalar == 0:
            raise ZeroDivisionError("Divisão de Vetor2D por zero.")
        return Vetor2D(self.__x / escalar, self.__y / escalar)

    def magnitude(self) -> float:
        return math.hypot(self.__x, self.__y)

    def normalizar(self) -> 'Vetor2D':
        """ Retorna um vetor com a mesma direção, mas com magnitude 1. """
        mag = self.magnitude()
        # Agora a operação abaixo funcionará
        return self / mag if mag != 0 else Vetor2D(0, 0)

    def rotacionar(self, angulo_rad: float) -> 'Vetor2D':
        cos_a = math.cos(angulo_rad)
        sin_a = math.sin(angulo_rad)
        novo_x = self.__x * cos_a - self.__y * sin_a
        novo_y = self.__x * sin_a + self.__y * cos_a
        return Vetor2D(novo_x, novo_y)
    
    def distancia_ate(self, outro: 'Vetor2D') -> float:
        return (self - outro).magnitude()
    
    def dot(self, outro: 'Vetor2D') -> float:
        return self.__x * outro.get_x() + self.__y * outro.get_y()

    # --- Métodos de Conversão ---
    def to_dict(self) -> dict:
        return {"x": self.__x, "y": self.__y}

    @classmethod
    def from_dict(cls, data: dict) -> 'Vetor2D':
        return cls(data["x"], data["y"])
    
    def para_tupla(self) -> tuple[int, int]:
        return (int(self.__x), int(self.__y))

    def copia(self) -> 'Vetor2D':
        return Vetor2D(self.__x, self.__y)