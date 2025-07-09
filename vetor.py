import math

class Vetor2D:
    def __init__(self, x=0.0, y=0.0):
        # O construtor agora usa os setters para definir os valores iniciais
        self.set_x(x)
        self.set_y(y)

    # --- Getters e Setters ---
    def get_x(self) -> float: 
        return self.__x

    def get_y(self) -> float: 
        return self.__y

    def set_x(self, novo_x: float): 
        self.__x = float(novo_x)

    def set_y(self, novo_y: float): 
        self.__y = float(novo_y)

    # --- Métodos de Operação ---
    def __add__(self, outro: 'Vetor2D') -> 'Vetor2D':
        # Acessar os valores de ambos os vetores
        return Vetor2D(self.get_x() + outro.get_x(), self.get_y() + outro.get_y())

    def __sub__(self, outro: 'Vetor2D') -> 'Vetor2D':
        return Vetor2D(self.get_x() - outro.get_x(), self.get_y() - outro.get_y())

    def __mul__(self, escalar: float) -> 'Vetor2D':
        return Vetor2D(self.get_x() * escalar, self.get_y() * escalar)
    
    def __rmul__(self, escalar: float) -> 'Vetor2D':
        # Esta chamada já usa o __mul__ modificado
        return self.__mul__(escalar)

    def __neg__(self):
        return Vetor2D(-self.get_x(), -self.get_y())

    def __truediv__(self, escalar: float) -> 'Vetor2D':
        if escalar == 0:
            raise ZeroDivisionError("Divisão de Vetor2D por zero.")
        return Vetor2D(self.get_x() / escalar, self.get_y() / escalar)

    def magnitude(self) -> float:
        return math.hypot(self.get_x(), self.get_y())

    def normalizar(self) -> 'Vetor2D':
        mag = self.magnitude()
        return self / mag if mag != 0 else Vetor2D(0, 0)

    def rotacionar(self, angulo_rad: float) -> 'Vetor2D':
        cos_a = math.cos(angulo_rad)
        sin_a = math.sin(angulo_rad)
        # Ccálculos de rotação
        novo_x = self.get_x() * cos_a - self.get_y() * sin_a
        novo_y = self.get_x() * sin_a + self.get_y() * cos_a
        return Vetor2D(novo_x, novo_y)
    
    def distancia_ate(self, outro: 'Vetor2D') -> float:
        return (self - outro).magnitude()
    
    def dot(self, outro: 'Vetor2D') -> float:
        # Produto escalar
        return self.get_x() * outro.get_x() + self.get_y() * outro.get_y()

    # --- Métodos de Conversão ---
    def to_dict(self) -> dict:
        return {"x": self.get_x(), "y": self.get_y()}

    @classmethod
    def from_dict(cls, data: dict) -> 'Vetor2D':
        return cls(data["x"], data["y"])
    
    def para_tupla(self) -> tuple[int, int]:
        return (int(self.get_x()), int(self.get_y()))

    def copia(self) -> 'Vetor2D':
        return Vetor2D(self.get_x(), self.get_y())
