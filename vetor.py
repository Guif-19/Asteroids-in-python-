import math

class Vetor2D:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __add__(self, outro):
        return Vetor2D(self.x + outro.x, self.y + outro.y)

    def __sub__(self, outro):
        return Vetor2D(self.x - outro.x, self.y - outro.y)

    def __mul__(self, escalar):
        return Vetor2D(self.x * escalar, self.y * escalar)
    
    def __rmul__(self, scalar: float) -> 'Vetor2D':
        # Este método lida com: número * vetor
        return self.__mul__(scalar)

    def __neg__(self):
        return Vetor2D(-self.x, -self.y)

    def __truediv__(self, escalar):
        return Vetor2D(self.x / escalar, self.y / escalar)

    def magnitude(self):
        return math.hypot(self.x, self.y)

    def normalizar(self):
        mag = self.magnitude()
        if mag == 0:
            return Vetor2D(0, 0)
        return Vetor2D(self.x / mag, self.y / mag)

    def rotacionar(self, angulo_rad):
        x = self.x * math.cos(angulo_rad) - self.y * math.sin(angulo_rad)
        y = self.x * math.sin(angulo_rad) + self.y * math.cos(angulo_rad)
        return Vetor2D(x, y)
    
    def distancia_ate(self, outro: 'Vetor2D') -> float:
        """Calcula a distância euclidiana entre este vetor (ponto) e outro."""
        # A distância é a magnitude do vetor que representa a diferença entre os dois pontos.
        return (self - outro).magnitude()
    
    def dot(self, outro: 'Vetor2D') -> float:
        return self.x * outro.x + self.y * outro.y

    def to_dict(self):
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data):
        return cls(data["x"], data["y"])
    
    def para_tupla(self):
        return (int(self.x), int(self.y))