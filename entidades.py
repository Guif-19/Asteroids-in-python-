# entidades.py (VERSÃO FINAL, CORRIGIDA E COMPLETA)

from typing import Optional
import pygame
import math
import random
from enum import Enum, auto
from config import *
from vetor import Vetor2D

CLASSE_MAP = {}

class GameObject:
    def __init__(self, posicao: Vetor2D, velocidade: Vetor2D, raio: float):
        self.__posicao = posicao
        self.__velocidade = velocidade
        self.__raio = raio
        self.__ativo = True
        self.image: pygame.Surface | None = None
        self.rect: pygame.Rect | None = None
        self.mask: pygame.mask.Mask | None = None

    def get_posicao(self) -> Vetor2D: return self.__posicao
    def get_velocidade(self) -> Vetor2D: return self.__velocidade
    def get_raio(self) -> float: return self.__raio
    def is_ativo(self) -> bool: return self.__ativo
    def get_rect(self) -> Optional[pygame.Rect]: return self.rect

    def set_posicao(self, nova_posicao: Vetor2D): self.__posicao = nova_posicao
    def set_velocidade(self, nova_velocidade: Vetor2D): self.__velocidade = nova_velocidade
    def set_ativo(self, estado: bool): self.__ativo = estado

    def atualizar(self, delta_tempo: float) -> None:
        # Pega os valores atuais usando os getters
        posicao_atual = self.get_posicao()
        velocidade_atual = self.get_velocidade()
        raio = self.get_raio()

        # Calcula a nova posição em uma nova variável
        nova_posicao = posicao_atual + velocidade_atual * delta_tempo * FPS
        
        # --- LINHA DA CORREÇÃO ---
        # Atribui a nova posição de volta ao objeto usando o setter
        self.set_posicao(nova_posicao)
        
        # A lógica de "wrap-around" agora usa a nova posição
        if nova_posicao.get_x() < -raio: nova_posicao.set_x(LARGURA_TELA + raio)
        elif nova_posicao.get_x() > LARGURA_TELA + raio: nova_posicao.set_x(-raio)
        if nova_posicao.get_y() < -raio: nova_posicao.set_y(ALTURA_TELA + raio)
        elif nova_posicao.get_y() > ALTURA_TELA + raio: nova_posicao.set_y(-raio)

        # Atualiza a posição do retângulo do sprite
        if self.rect:
            self.rect.center = nova_posicao.para_tupla()

    def desenhar(self, tela: pygame.Surface) -> None:
        if self.is_ativo() and self.image and self.rect:
            tela.blit(self.image, self.rect)

    def colide_com(self, outro_objeto: 'GameObject') -> bool:
        if not self.is_ativo() or not outro_objeto.is_ativo(): return False
        r1, r2 = self.get_rect(), outro_objeto.get_rect()
        if not r1 or not r2: return False
        if not r1.colliderect(r2): return False
        
        mask_self, mask_outro = getattr(self, 'mask', None), getattr(outro_objeto, 'mask', None)
        if not mask_self or not mask_outro: return False
        
        offset = (r2.x - r1.x, r2.y - r1.y)
        return mask_self.overlap(mask_outro, offset) is not None

    def to_dict_base(self) -> dict:
        return {"classe_tipo": self.__class__.__name__, "posicao": self.get_posicao().to_dict(), "velocidade": self.get_velocidade().to_dict(), "raio": self.get_raio(), "ativo": self.is_ativo()}

    def restaurar_estado_base(self, data: dict):
        self.set_ativo(data.get("ativo", True))

class Nave(GameObject):
    def __init__(self, posicao: Vetor2D):
        super().__init__(posicao, Vetor2D(), 15)
        self.__angulo_graus = 0.0
        self.__rotacionando_esquerda, self.__rotacionando_direita, self.__acelerando = False, False, False
        self.__ultimo_tiro_tempo, self.__tem_tiro_triplo, self.__tempo_fim_tiro_triplo, self.__tempo_invulneravel_fim = 0, False, 0, 0
        try:
            self.original_image = pygame.image.load(IMAGEM_NAVE).convert_alpha()
        except pygame.error:
            self.original_image = pygame.Surface((self.get_raio() * 2, self.get_raio() * 2), pygame.SRCALPHA)

        # --- CORREÇÃO APLICADA AQUI ---
        self.image = self.original_image
        self.rect = self.image.get_rect(center=self.get_posicao().para_tupla())
        self.mask = pygame.mask.from_surface(self.image)

    def get_angulo(self) -> float: return self.__angulo_graus
    def set_angulo(self, angulo: float): self.__angulo_graus = angulo
    def set_rotacao(self, direcao: str, estado: bool):
        if direcao == 'esquerda': self.__rotacionando_esquerda = estado
        elif direcao == 'direita': self.__rotacionando_direita = estado
    def set_acelerando(self, estado: bool): self.__acelerando = estado
    def get_invulneravel_fim(self) -> int: return self.__tempo_invulneravel_fim
    def set_invulneravel_fim(self, tempo: int): self.__tempo_invulneravel_fim = tempo
    def tem_tiro_triplo(self) -> bool: return self.__tem_tiro_triplo
    def set_tem_tiro_triplo(self, estado: bool): self.__tem_tiro_triplo = estado
    def set_tempo_fim_tiro_triplo(self, tempo: int): self.__tempo_fim_tiro_triplo = tempo
    def is_invulneravel(self) -> bool: return pygame.time.get_ticks() < self.get_invulneravel_fim()

    def desenhar(self, tela: pygame.Surface) -> None:
        if not self.is_ativo(): return
        if self.is_invulneravel() and (pygame.time.get_ticks() // 100) % 2 == 0: return
        super().desenhar(tela)
        if self.__acelerando:
            angulo_rad = math.radians(self.get_angulo())
            pos, raio = self.get_posicao(), self.get_raio()
            tras, esq, dir_ = Vetor2D(0, raio * 1.2).rotacionar(angulo_rad), Vetor2D(-raio * 0.3, raio * 0.8).rotacionar(angulo_rad), Vetor2D(raio * 0.3, raio * 0.8).rotacionar(angulo_rad)
            fogo = [(pos + tras).para_tupla(), (pos + esq).para_tupla(), (pos + dir_).para_tupla()]
            pygame.draw.polygon(tela, VERMELHO, fogo, 0)

    def atualizar(self, delta_tempo: float) -> None:
        if self.tem_tiro_triplo() and pygame.time.get_ticks() >= self.__tempo_fim_tiro_triplo: self.set_tem_tiro_triplo(False)
        if self.__rotacionando_esquerda: self.set_angulo(self.get_angulo() - VELOCIDADE_ROTACAO_NAVE)
        if self.__rotacionando_direita: self.set_angulo(self.get_angulo() + VELOCIDADE_ROTACAO_NAVE)
        if self.__acelerando:
            angulo_rad = math.radians(self.get_angulo() - 90)
            direcao = Vetor2D(math.cos(angulo_rad), math.sin(angulo_rad))
            self.set_velocidade(self.get_velocidade() + direcao * ACELERACAO_NAVE)
        self.set_velocidade(self.get_velocidade() * FRICCAO_NAVE)
        self.image = pygame.transform.rotate(self.original_image, -self.get_angulo())
        self.rect = self.image.get_rect(center=self.get_posicao().para_tupla())
        self.mask = pygame.mask.from_surface(self.image)
        super().atualizar(delta_tempo)

    def atirar(self) -> list['Projetil']:
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.__ultimo_tiro_tempo <= COOLDOWN_TIRO: return []
        self.__ultimo_tiro_tempo = tempo_atual
        angulo_rad = math.radians(self.get_angulo() - 90)
        direcao = Vetor2D(math.cos(angulo_rad), math.sin(angulo_rad))
        pos = self.get_posicao() + direcao * self.get_raio()
        vel = direcao * VELOCIDADE_PROJETIL + self.get_velocidade()
        projeteis = [Projetil(pos, vel)]
        if self.tem_tiro_triplo() and tempo_atual < self.__tempo_fim_tiro_triplo:
            for offset in [-ANGULO_TIRO_TRIPLO_GRAUS, ANGULO_TIRO_TRIPLO_GRAUS]:
                d = direcao.rotacionar(math.radians(offset))
                projeteis.append(Projetil(self.get_posicao() + d * self.get_raio(), d * VELOCIDADE_PROJETIL + self.get_velocidade()))
        return projeteis

    def ativar_tiro_triplo(self, duracao_segundos: int) -> None:
        if self.is_ativo(): self.set_tem_tiro_triplo(True); self.set_tempo_fim_tiro_triplo(pygame.time.get_ticks() + duracao_segundos * 1000)
    
    def to_dict(self) -> dict:  
        data = self.to_dict_base()
        data.update({"angulo_graus": self.get_angulo(), "tem_tiro_triplo": self.tem_tiro_triplo(), "tempo_fim_tiro_triplo_restante_ms": max(0, self.__tempo_fim_tiro_triplo - pygame.time.get_ticks()) if self.tem_tiro_triplo() else 0, "invulneravel_fim_restante_ms": max(0, self.get_invulneravel_fim() - pygame.time.get_ticks())})
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Nave':
        obj = cls(Vetor2D.from_dict(data["posicao"]))
        obj.set_velocidade(Vetor2D.from_dict(data["velocidade"])); obj.restaurar_estado_base(data); obj.set_angulo(data.get("angulo_graus", 0.0))
        obj.set_tem_tiro_triplo(data.get("tem_tiro_triplo", False))
        if obj.tem_tiro_triplo(): obj.set_tempo_fim_tiro_triplo(pygame.time.get_ticks() + data.get("tempo_fim_tiro_triplo_restante_ms", 0))
        tempo_inv_restante = data.get("invulneravel_fim_restante_ms", 0)
        if tempo_inv_restante > 0: obj.set_invulneravel_fim(pygame.time.get_ticks() + tempo_inv_restante)
        return obj

class Projetil(GameObject):
# Em entidades.py, substitua o __init__ da classe Projetil:
    def __init__(self, posicao: Vetor2D, velocidade: Vetor2D):
        super().__init__(posicao, velocidade, 3)
        self.__frames_vividos = 0
        try:
            self.original_image = pygame.image.load(IMAGEM_PROJETIL_JOGADOR).convert_alpha()
        except pygame.error:
            self.original_image = pygame.Surface((5, 10), pygame.SRCALPHA)
            pygame.draw.rect(self.original_image, BRANCO, (0, 0, 5, 10))
        angulo = math.degrees(math.atan2(-velocidade.get_y(), velocidade.get_x())) + 90
        
        # --- CORREÇÃO APLICADA AQUI ---
        self.image = pygame.transform.rotate(self.original_image, -angulo)
        self.rect = self.image.get_rect(center=posicao.para_tupla())
        self.mask = pygame.mask.from_surface(self.image)

    def atualizar(self, delta_tempo: float) -> None:
        super().atualizar(delta_tempo); self.__frames_vividos += 1
        if self.__frames_vividos > DURACAO_PROJETIL: self.set_ativo(False)

    def to_dict(self) -> dict:
        """Converte o estado do Projétil para um dicionário salvável."""
        data = self.to_dict_base()
        data["frames_vividos"] = self.__frames_vividos
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Projetil':
        """Cria uma instância de Projetil a partir de um dicionário."""
        obj = cls(
            Vetor2D.from_dict(data["posicao"]),
            Vetor2D.from_dict(data["velocidade"])
        )
        obj.restaurar_estado_base(data)
        # Acessa o atributo privado diretamente para restaurar o estado
        obj.__frames_vividos = data.get("frames_vividos", 0)
        return obj


class Asteroide(GameObject):
    TAMANHOS = {"grande": (35, PONTOS_ASTEROIDE_GRANDE), "medio": (25, PONTOS_ASTEROIDE_MEDIO), "pequeno": (12, PONTOS_ASTEROIDE_PEQUENO)}
    def __init__(self, posicao: Vetor2D, tamanho_str="grande", velocidade: Vetor2D = None):
        raio, pontos = self.TAMANHOS[tamanho_str]
        vel = velocidade if velocidade is not None else Vetor2D(random.uniform(VEL_MIN_ASTEROIDE, VEL_MAX_ASTEROIDE) * random.choice([-1, 1]), random.uniform(VEL_MIN_ASTEROIDE, VEL_MAX_ASTEROIDE) * random.choice([-1, 1]))
        super().__init__(posicao, vel, raio)
        self.__tamanho_str, self.__pontos, self.__angulo_rotacao, self.__velocidade_rotacao = tamanho_str, pontos, random.uniform(0, 360), random.uniform(-1, 1)
        
        imagem_path = {"grande": IMAGEM_ASTEROIDE_GRANDE, "medio": IMAGEM_ASTEROIDE_MEDIO, "pequeno": IMAGEM_ASTEROIDE_PEQUENO}[tamanho_str]
        try:
            self.original_image = pygame.image.load(imagem_path).convert_alpha()
        except pygame.error:
            self.original_image = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
            pygame.draw.circle(self.original_image, CINZA_CLARO, (raio, raio), raio, 1)
        
        # --- CORREÇÃO APLICADA AQUI ---
        self.image = self.original_image
        self.rect = self.image.get_rect(center=posicao.para_tupla())
        self.mask = pygame.mask.from_surface(self.image)

    def get_tamanho_str(self) -> str: return self.__tamanho_str
    def get_pontos(self) -> int: return self.__pontos

    def atualizar(self, delta_tempo: float) -> None:
        self.__angulo_rotacao = (self.__angulo_rotacao + self.__velocidade_rotacao) % 360
        self.image = pygame.transform.rotate(self.original_image, self.__angulo_rotacao)
        self.rect = self.image.get_rect(center=self.get_posicao().para_tupla())
        self.mask = pygame.mask.from_surface(self.image)
        super().atualizar(delta_tempo)

    def dividir(self) -> list['Asteroide']:
        if self.get_tamanho_str() == "pequeno": self.set_ativo(False); return []
        self.set_ativo(False)
        proximo_tamanho = "medio" if self.get_tamanho_str() == "grande" else "pequeno"
        novos = []
        for i in range(2):
            vel_base = self.get_velocidade()
            if vel_base.magnitude() < 0.1: vel_base = Vetor2D(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5))
            offset_dir = vel_base.normalizar().rotacionar(math.radians(90))
            offset = offset_dir * (self.get_raio() / 1.5) * (1 if i == 0 else -1)
            pos_frag = self.get_posicao() + offset
            vel_frag = vel_base.rotacionar(math.radians(random.uniform(20, 50) * (1 if i == 0 else -1)))
            novos.append(Asteroide(pos_frag, proximo_tamanho, vel_frag))
        return novos

    def to_dict(self) -> dict:
        """Converte o estado do Asteroide para um dicionário salvável."""
        data = self.to_dict_base()
        data.update({
            "tamanho_str": self.get_tamanho_str(),
            "pontos": self.get_pontos(),
            "angulo_rotacao": self.__angulo_rotacao,
            "velocidade_rotacao": self.__velocidade_rotacao
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Asteroide':
        """Cria uma instância de Asteroide a partir de um dicionário."""
        obj = cls(
            Vetor2D.from_dict(data["posicao"]),
            data.get("tamanho_str", "grande"),
            Vetor2D.from_dict(data["velocidade"])
        )
        obj.restaurar_estado_base(data)
        
        # Restaura os atributos privados específicos do Asteroide
        obj.__pontos = data.get("pontos", cls.TAMANHOS[obj.get_tamanho_str()][1])
        obj.__angulo_rotacao = data.get("angulo_rotacao", 0)
        obj.__velocidade_rotacao = data.get("velocidade_rotacao", random.uniform(-1, 1))
        
        return obj

class OVNIProjetil(GameObject):
    def __init__(self, posicao: Vetor2D, velocidade: Vetor2D, imagem_path: str):
        super().__init__(posicao, velocidade, 4)
        self.__tempo_criacao = pygame.time.get_ticks()
        self.__imagem_path = imagem_path
        try:
            self.original_image = pygame.image.load(self.__imagem_path).convert_alpha()
        except pygame.error:
            self.original_image = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(self.original_image, VERMELHO, (4, 4), 4)
        angulo = math.degrees(math.atan2(-velocidade.get_y(), velocidade.get_x())) + 90
        self.image = pygame.transform.rotate(self.original_image, -angulo)
        self.rect = self.image.get_rect(center=posicao.para_tupla())
        self.mask = pygame.mask.from_surface(self.image)

    def atualizar(self, delta_tempo: float) -> None:
        super().atualizar(delta_tempo)
        if pygame.time.get_ticks() - self.__tempo_criacao > 3000:
            self.set_ativo(False)

    def to_dict(self) -> dict:
        data = self.to_dict_base()
        data["tempo_criacao_relativo_ms"] = pygame.time.get_ticks() - self.__tempo_criacao
        data["imagem_path"] = self.__imagem_path
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'OVNIProjetil':
        obj = cls(Vetor2D.from_dict(data["posicao"]), Vetor2D.from_dict(data["velocidade"]), data["imagem_path"])
        obj.restaurar_estado_base(data)
        obj.__tempo_criacao = pygame.time.get_ticks() - data.get("tempo_criacao_relativo_ms", 0)
        return obj


class OVNI(GameObject):
    def __init__(self, imagem_path: str, posicao: Optional[Vetor2D] = None, velocidade: Optional[Vetor2D] = None):
        raio_ovni = 20
        if posicao is None or velocidade is None:
            direcao = random.choice([-1, 1])
            pos_x = -raio_ovni if direcao == 1 else LARGURA_TELA + raio_ovni
            pos_y = random.uniform(ALTURA_TELA * 0.1, ALTURA_TELA * 0.6)
            posicao_final = Vetor2D(pos_x, pos_y)
            velocidade_final = Vetor2D(VELOCIDADE_OVNI * direcao, 0)
        else:
            posicao_final, velocidade_final = posicao, velocidade
        
        super().__init__(posicao_final, velocidade_final, raio_ovni)
        
        self.__direcao_horizontal = 1 if self.get_velocidade().get_x() > 0 else -1
        self.__ultimo_tiro_tempo_ms = pygame.time.get_ticks()
        
        try:
            self.image = pygame.image.load(imagem_path).convert_alpha()
            self.rect = self.image.get_rect(center=self.get_posicao().para_tupla())
            self.mask = pygame.mask.from_surface(self.image)
        except pygame.error:
            self.image, self.rect, self.mask = None, None, None

    def atualizar(self, delta_tempo: float) -> None:
        super().atualizar(delta_tempo)
        pos_x = self.get_posicao().get_x()
        raio = self.get_raio()
        if (self.__direcao_horizontal == 1 and pos_x > LARGURA_TELA + raio) or \
           (self.__direcao_horizontal == -1 and pos_x < -raio):
            self.set_ativo(False)

    def tentar_atirar(self, posicao_nave: Vetor2D) -> list: return []

    def to_dict(self) -> dict:
        data = self.to_dict_base()
        data.update({"ultimo_tiro_tempo_ms_relativo": max(0, pygame.time.get_ticks() - self.__ultimo_tiro_tempo_ms)})
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'OVNI':
        # --- CORREÇÃO APLICADA AQUI ---
        # Acessa a classe correta (OvniX ou OvniCruz) a partir do CLASSE_MAP
        # e a instancia com os argumentos corretos.
        classe_correta = CLASSE_MAP[data["classe_tipo"]]
        obj = classe_correta(
            Vetor2D.from_dict(data["posicao"]),
            Vetor2D.from_dict(data["velocidade"])
        )
        
        obj.restaurar_estado_base(data)
        
        # Restaura os atributos privados específicos do OVNI
        obj._OVNI__ultimo_tiro_tempo_ms = pygame.time.get_ticks() - data.get("ultimo_tiro_tempo_ms_relativo", 0)
        
        return obj


class OvniX(OVNI):
    def __init__(self, posicao: Optional[Vetor2D] = None, velocidade: Optional[Vetor2D] = None):
        super().__init__(IMAGEM_OVNI_X, posicao, velocidade)

    def tentar_atirar(self, posicao_nave: Vetor2D) -> list[OVNIProjetil]:
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self._OVNI__ultimo_tiro_tempo_ms > COOLDOWN_TIRO_OVNI_MS:
            self._OVNI__ultimo_tiro_tempo_ms = tempo_atual
            projeteis = []
            direcoes = [Vetor2D(1, 1).normalizar(), Vetor2D(-1, 1).normalizar(), Vetor2D(1, -1).normalizar(), Vetor2D(-1, -1).normalizar()]
            for direcao in direcoes:
                projeteis.append(OVNIProjetil(self.get_posicao() + direcao * self.get_raio(), direcao * VELOCIDADE_PROJETIL_OVNI, IMAGEM_PROJETIL_OVNI_X))
            return projeteis
        return []


class OvniCruz(OVNI):
    def __init__(self, posicao: Optional[Vetor2D] = None, velocidade: Optional[Vetor2D] = None):
        super().__init__(IMAGEM_OVNI_CRUZ, posicao, velocidade)

    def tentar_atirar(self, posicao_nave: Vetor2D) -> list[OVNIProjetil]:
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self._OVNI__ultimo_tiro_tempo_ms > COOLDOWN_TIRO_OVNI_MS:
            self._OVNI__ultimo_tiro_tempo_ms = tempo_atual
            projeteis = []
            direcoes = [Vetor2D(1, 0), Vetor2D(-1, 0), Vetor2D(0, 1), Vetor2D(0, -1)]
            for direcao in direcoes:
                projeteis.append(OVNIProjetil(self.get_posicao() + direcao * self.get_raio(), direcao * VELOCIDADE_PROJETIL_OVNI, IMAGEM_PROJETIL_OVNI_CRUZ))
            return projeteis
        return []

class EstadoFantasma(Enum):
    INVISIVEL = auto()
    CARREGANDO = auto()

class NaveFantasma(GameObject):
    def __init__(self):
        super().__init__(Vetor2D(-100, -100), Vetor2D(), 18)
        self.__estado = EstadoFantasma.INVISIVEL
        self.__tempo_proxima_acao = pygame.time.get_ticks() + random.randint(4000, 8000)
        self.__alvo_disparo: Optional[Vetor2D] = None
        self.set_ativo(False)
        try:
            self.original_image = pygame.image.load(IMAGEM_FANTASMA).convert_alpha()
            self.image = self.original_image
            self.rect = self.image.get_rect(center=self.get_posicao().para_tupla())
            self.mask = pygame.mask.from_surface(self.image)
        except pygame.error:
            self.image, self.rect, self.mask, self.original_image = None, None, None, None
            print("AVISO: Falha ao carregar sprite da NaveFantasma.")

    # --- Getters e Setters ---
    def get_estado(self) -> EstadoFantasma: return self.__estado
    def set_estado(self, e: EstadoFantasma): self.__estado = e
    def get_tempo_proxima_acao(self) -> int: return self.__tempo_proxima_acao
    def set_tempo_proxima_acao(self, t: int): self.__tempo_proxima_acao = t
    def get_alvo_disparo(self) -> Optional[Vetor2D]: return self.__alvo_disparo
    def set_alvo_disparo(self, a: Optional[Vetor2D]): self.__alvo_disparo = a

    def atualizar(self, delta_tempo: float, posicao_nave: Optional[Vetor2D] = None) -> Optional['LaserFantasma']:
        tempo_atual = pygame.time.get_ticks()
        laser_criado = None
        
        if self.get_estado() == EstadoFantasma.INVISIVEL and tempo_atual >= self.get_tempo_proxima_acao():
            print("[FANTASMA DEBUG] Timer INVISÍVEL terminou. Tentando aparecer...")
            if posicao_nave:
                print("[FANTASMA DEBUG] Alvo encontrado! Mudando para o estado CARREGANDO.")
                self.set_estado(EstadoFantasma.CARREGANDO)
                self.set_ativo(True)
                nova_pos = Vetor2D(random.randrange(50, LARGURA_TELA - 50), random.randrange(50, ALTURA_TELA - 50))
                self.set_posicao(nova_pos)
                if self.rect: self.rect.center = nova_pos.para_tupla()
                self.set_tempo_proxima_acao(tempo_atual + DURACAO_FANTASMA_CARREGANDO_MS)
                self.set_alvo_disparo(posicao_nave.copia())
            else:
                print("[FANTASMA DEBUG] Alvo NÃO encontrado. Esperando mais 2 segundos.")
                self.set_tempo_proxima_acao(tempo_atual + 2000)

        elif self.get_estado() == EstadoFantasma.CARREGANDO and tempo_atual >= self.get_tempo_proxima_acao():
            print("[FANTASMA DEBUG] Timer CARREGANDO terminou. Tentando atirar...")
            if self.get_alvo_disparo():
                print("[FANTASMA DEBUG] SUCESSO! Atirando.")
                direcao = (self.get_alvo_disparo() - self.get_posicao()).normalizar()
                laser_criado = LaserFantasma(self.get_posicao(), direcao)
            else:
                print("[FANTASMA DEBUG] FALHA! Sem alvo para atirar. Desaparecendo.")

            self.set_estado(EstadoFantasma.INVISIVEL)
            self.set_ativo(False)
            self.set_tempo_proxima_acao(tempo_atual + DURACAO_FANTASMA_INVISIVEL_MS)
            self.set_alvo_disparo(None)
            
        return laser_criado

    def desenhar(self, tela: pygame.Surface) -> None:
        # A nave fantasma só é visível e tem o círculo quando está no estado CARREGANDO
        if not self.is_ativo() or self.get_estado() != EstadoFantasma.CARREGANDO:
            return

        # Desenha o sprite da nave primeiro
        super().desenhar(tela)
        
        # Calcula o tempo que ainda falta para o ataque terminar
        tempo_restante = max(0, self.get_tempo_proxima_acao() - pygame.time.get_ticks())
        
        # Calcula o progresso como uma fração do tempo total (este valor vai de 1.0 a 0.0)
        progresso_contracao = tempo_restante / DURACAO_FANTASMA_CARREGANDO_MS
        
        # O raio do círculo começa grande e diminui junto com o progresso
        raio_maximo_indicador = self.get_raio() * 2.5  # Um pouco maior que o sprite da nave
        raio_atual = int(raio_maximo_indicador * progresso_contracao)
        
        # Só desenha o círculo se ele ainda for visível
        if raio_atual > 2:
            pygame.draw.circle(
                tela,
                COR_FANTASMA_CARREGANDO,
                self.get_posicao().para_tupla(),
                raio_atual,
                2  # Espessura da linha do círculo
            )
    
    def to_dict(self) -> dict:
        data = self.to_dict_base()
        alvo = self.get_alvo_disparo()
        data.update({
            "estado": self.get_estado().name,
            "tempo_proxima_acao_restante_ms": max(0, self.get_tempo_proxima_acao() - pygame.time.get_ticks()),
            "alvo_disparo": alvo.to_dict() if alvo else None
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'NaveFantasma':
        obj = cls()
        obj.restaurar_estado_base(data)
        obj.set_posicao(Vetor2D.from_dict(data["posicao"]))
        obj.set_velocidade(Vetor2D.from_dict(data["velocidade"]))
        obj.set_estado(EstadoFantasma[data.get("estado", "INVISIVEL")])
        obj.set_tempo_proxima_acao(pygame.time.get_ticks() + data.get("tempo_proxima_acao_restante_ms", 0))
        alvo_data = data.get("alvo_disparo")
        obj.set_alvo_disparo(Vetor2D.from_dict(alvo_data) if alvo_data else None)
        return obj

class LaserFantasma(GameObject):
    def __init__(self, pos_inicio: Vetor2D, direcao: Vetor2D):
        super().__init__(pos_inicio, direcao * VELOCIDADE_LASER_FANTASMA, 5)
        self.__direcao = direcao
        try:
            self.original_image = pygame.image.load(IMAGEM_LASER_FANTASMA).convert_alpha()
        except pygame.error:
            self.original_image = pygame.Surface((4, 12), pygame.SRCALPHA)
            pygame.draw.rect(self.original_image, COR_FANTASMA_LASER, (0,0,4,12))
        
        angulo = math.degrees(math.atan2(-direcao.get_y(), direcao.get_x())) + 90
        
        # --- CORREÇÃO APLICADA AQUI ---
        # A atribuição foi separada em 3 linhas para evitar o erro de 'None'
        self.image = pygame.transform.rotozoom(self.original_image, -angulo, 1.0)
        self.rect = self.image.get_rect(center=pos_inicio.para_tupla())
        self.mask = pygame.mask.from_surface(self.image)

    def atualizar(self, delta_tempo: float) -> None:
        pos = self.get_posicao() + self.get_velocidade() * delta_tempo * FPS
        self.set_posicao(pos)
        if self.rect: self.rect.center = pos.para_tupla()
        
        tela_rect = pygame.Rect(0, 0, LARGURA_TELA, ALTURA_TELA)
        if self.rect and not self.rect.colliderect(tela_rect):
            self.set_ativo(False)

    def to_dict(self) -> dict:
        data = self.to_dict_base()
        data.update({"direcao": self.__direcao.to_dict()})
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'LaserFantasma':
        obj = cls(Vetor2D.from_dict(data["posicao"]), Vetor2D.from_dict(data["direcao"]))
        obj.restaurar_estado_base(data)
        return obj

CLASSE_MAP = {
        'Nave': Nave,   
        'Projetil': Projetil,
        'Asteroide': Asteroide,
        'OVNIProjetil': OVNIProjetil,
        'OvniX': OvniX,
        'OvniCruz': OvniCruz,
        'NaveFantasma': NaveFantasma,
        'LaserFantasma': LaserFantasma
    }
