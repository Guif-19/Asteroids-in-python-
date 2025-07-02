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
        self._posicao = posicao
        self._velocidade = velocidade
        self._raio = raio
        self._ativo = True
        self.image: pygame.Surface | None = None
        self.rect: pygame.Rect | None = None

    def get_posicao(self) -> Vetor2D: return self._posicao
    def get_velocidade(self) -> Vetor2D: return self._velocidade
    def get_raio(self) -> float: return self._raio
    def is_ativo(self) -> bool: return self._ativo

    def set_posicao(self, nova_posicao: Vetor2D): self._posicao = nova_posicao
    def set_velocidade(self, nova_velocidade: Vetor2D): self._velocidade = nova_velocidade
    def set_ativo(self, estado: bool): self._ativo = estado

    def atualizar(self, delta_tempo: float) -> None:
        # wrap-arounda
        self._posicao += self._velocidade * delta_tempo * FPS
        if self._posicao.get_x() < -self._raio: self._posicao.set_x(LARGURA_TELA + self._raio)
        elif self._posicao.get_x() > LARGURA_TELA + self._raio: self._posicao.set_x(-self._raio)
        if self._posicao.get_y() < -self._raio: self._posicao.set_y(ALTURA_TELA + self._raio)
        elif self._posicao.get_y() > ALTURA_TELA + self._raio: self._posicao.set_y(-self._raio)

        if self.rect:
            self.rect.center = self._posicao.para_tupla()

    def desenhar(self, tela: pygame.Surface) -> None:
        if self._ativo and self.image and self.rect:
            tela.blit(self.image, self.rect)

    def colide_com(self, outro_objeto: 'GameObject') -> bool:
        if not self.is_ativo() or not outro_objeto.is_ativo(): return False
        return self.get_posicao().distancia_ate(outro_objeto.get_posicao()) < self.get_raio() + outro_objeto.get_raio()

    # --- Métodos de Save/Load ---
    def to_dict_base(self) -> dict:
        return {
            "classe_tipo": self.__class__.__name__,
            "posicao": self._posicao.to_dict(),
            "velocidade": self._velocidade.to_dict(),
            "raio": self._raio,
            "ativo": self._ativo
        }

    @classmethod
    def from_dict_base_data(cls, data: dict) -> dict:
        return {
            "posicao": Vetor2D.from_dict(data["posicao"]),
            "velocidade": Vetor2D.from_dict(data["velocidade"]),
            "raio": data.get("raio", 10.0)
        }

    def restaurar_estado_base(self, data: dict):
        self._ativo = data.get("ativo", True)


class Nave(GameObject):
    def __init__(self, posicao: Vetor2D):
        super().__init__(posicao, Vetor2D(), 15)
        self._angulo_graus = 0.0
        self.rotacionando_esquerda = False
        self.rotacionando_direita = False
        self.acelerando = False
        self.ultimo_tiro_tempo = 0
        self.tem_tiro_triplo = False
        self.tempo_fim_tiro_triplo = 0
        self.tempo_invulneravel_fim = 0
        self.original_image = pygame.image.load(IMAGEM_NAVE).convert_alpha()
        self.image = self.original_image
        self.rect = self.image.get_rect(center=self._posicao.para_tupla())

    def get_angulo(self) -> float: return self._angulo_graus
    def set_angulo(self, angulo: float): self._angulo_graus = angulo

    def desenhar(self, tela: pygame.Surface) -> None:
        if not self.is_ativo(): return
        
        if pygame.time.get_ticks() < self.tempo_invulneravel_fim:
            if (pygame.time.get_ticks() // 100) % 2 == 0:
                tela.blit(self.image, self.rect)
        else:
            tela.blit(self.image, self.rect)

    def atualizar(self, delta_tempo: float) -> None:
        tempo_atual = pygame.time.get_ticks()
        if self.tem_tiro_triplo and tempo_atual >= self.tempo_fim_tiro_triplo: self.tem_tiro_triplo = False
        
        # Lógica de Rotação
        if self.rotacionando_esquerda: self._angulo_graus -= VELOCIDADE_ROTACAO_NAVE
        if self.rotacionando_direita: self._angulo_graus += VELOCIDADE_ROTACAO_NAVE
        self._angulo_graus %= 360
        
        # Lógica de Aceleração
        if self.acelerando:
            angulo_rad = math.radians(self._angulo_graus - 90)
            direcao = Vetor2D(math.cos(angulo_rad), math.sin(angulo_rad))
            self._velocidade += direcao * ACELERACAO_NAVE
            
        self._velocidade *= FRICCAO_NAVE
        
        # ---- Bloco de atualização do Sprite ----
        self.image = pygame.transform.rotate(self.original_image, -self._angulo_graus)
        self.rect = self.image.get_rect(center=self._posicao.para_tupla())

        super().atualizar(delta_tempo)

    def atirar(self) -> list['Projetil']:
        tempo_atual = pygame.time.get_ticks()
        projeteis_criados = []
        if tempo_atual - self.ultimo_tiro_tempo > COOLDOWN_TIRO:
            self.ultimo_tiro_tempo = tempo_atual
            angulo_base_rad = math.radians(self._angulo_graus - 90)
            direcao_base = Vetor2D(math.cos(angulo_base_rad), math.sin(angulo_base_rad))
            pos_base = self._posicao + direcao_base * self._raio
            vel_base = direcao_base * VELOCIDADE_PROJETIL + self._velocidade
            projeteis_criados.append(Projetil(pos_base, vel_base))
            if self.tem_tiro_triplo and tempo_atual < self.tempo_fim_tiro_triplo:
                angulo_lateral_rad = math.radians(ANGULO_TIRO_TRIPLO_GRAUS)
                for offset in [-angulo_lateral_rad, angulo_lateral_rad]:
                    direcao = direcao_base.rotacionar(offset)
                    pos = self._posicao + direcao * self._raio
                    vel = direcao * VELOCIDADE_PROJETIL + self._velocidade
                    projeteis_criados.append(Projetil(pos, vel))
        return projeteis_criados

    def ativar_tiro_triplo(self, duracao_segundos: int) -> None:
        if self.is_ativo():
            self.tem_tiro_triplo = True
            self.tempo_fim_tiro_triplo = pygame.time.get_ticks() + duracao_segundos * 1000

    def to_dict(self) -> dict:  
        data = self.to_dict_base()
        data.update({"angulo_graus": self._angulo_graus, "tem_tiro_triplo": self.tem_tiro_triplo, "tempo_fim_tiro_triplo_restante_ms": max(0, self.tempo_fim_tiro_triplo - pygame.time.get_ticks()) if self.tem_tiro_triplo else 0})
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Nave':
        obj = cls(Vetor2D.from_dict(data["posicao"]))
        obj.set_velocidade(Vetor2D.from_dict(data["velocidade"]))
        obj.restaurar_estado_base(data)
        obj.set_angulo(data.get("angulo_graus", 0.0))
        obj.tem_tiro_triplo = data.get("tem_tiro_triplo", False)
        if obj.tem_tiro_triplo:
            obj.tempo_fim_tiro_triplo = pygame.time.get_ticks() + data.get("tempo_fim_tiro_triplo_restante_ms", 0)
        return obj

class Projetil(GameObject):
    def __init__(self, posicao: Vetor2D, velocidade: Vetor2D):
        super().__init__(posicao, velocidade, 3)
        self._frames_vividos = 0
        
        # Carrega a imagem original do projétil
        self.original_image = pygame.image.load(IMAGEM_PROJETIL_JOGADOR).convert_alpha()

        # Calcula o ângulo a partir do vetor de velocidade
        angulo = math.degrees(math.atan2(-velocidade.get_y(), velocidade.get_x()))

        # Rotaciona a imagem
        self.image = pygame.transform.rotate(self.original_image, angulo)
        
        self.rect = self.image.get_rect(center=posicao.para_tupla())

    def atualizar(self, delta_tempo: float) -> None:
        super().atualizar(delta_tempo)
        
        # Lógica de tempo de vida do projétil
        self._frames_vividos += 1
        if self._frames_vividos > DURACAO_PROJETIL:
            self.set_ativo(False)

    # --- Métodos para Save/Load ---
    def to_dict(self) -> dict:
        data = self.to_dict_base()
        data["frames_vividos"] = self.get_frames_vividos()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Projetil':
        obj = cls(Vetor2D.from_dict(data["posicao"]), Vetor2D.from_dict(data["velocidade"]))
        obj.restaurar_estado_base(data)
        obj._frames_vividos = data.get("frames_vividos", 0)
        return obj

    def get_frames_vividos(self) -> int:
        """Retorna o número de frames que o projétil já viveu."""
        return self._frames_vividos
        
    def set_frames_vividos(self, frames: int):
        """Define o número de frames vividos (usado principalmente ao carregar um jogo)."""
        self._frames_vividos = frames
    

class Asteroide(GameObject):
    TAMANHOS = {
        "grande": (35, PONTOS_ASTEROIDE_GRANDE),
        "medio": (25, PONTOS_ASTEROIDE_MEDIO),
        "pequeno": (12, PONTOS_ASTEROIDE_PEQUENO)
    }

    def __init__(self, posicao: Vetor2D, tamanho_str="grande", velocidade: Vetor2D = None):
        raio, pontos = self.TAMANHOS[tamanho_str]
        vel = velocidade if velocidade is not None else Vetor2D(
            random.uniform(VEL_MIN_ASTEROIDE, VEL_MAX_ASTEROIDE) * random.choice([-1, 1]),
            random.uniform(VEL_MIN_ASTEROIDE, VEL_MAX_ASTEROIDE) * random.choice([-1, 1])
        )
        super().__init__(posicao, vel, raio)

        self._tamanho_str = tamanho_str
        self._pontos = pontos
        self._angulo_rotacao = random.uniform(0, 360) # Rotação inicial aleatória
        self._velocidade_rotacao = random.uniform(-1, 1)

        # Carrega e escala a imagem do asteroide de acordo com o tamanho
        if tamanho_str == "grande":
            self.original_image = pygame.image.load(IMAGEM_ASTEROIDE_GRANDE).convert_alpha()
        elif tamanho_str == "medio":
            img_base = pygame.image.load(IMAGEM_ASTEROIDE_MEDIO).convert_alpha()
            novo_tamanho = int(raio * 2.5) # Fator para o sprite parecer bom
            self.original_image = pygame.transform.scale(img_base, (novo_tamanho, novo_tamanho))
        else:
            self.original_image = pygame.image.load(IMAGEM_ASTEROIDE_PEQUENO).convert_alpha()
            
        self.image = self.original_image
        self.rect = self.image.get_rect(center=posicao.para_tupla())

    def atualizar(self, delta_tempo: float) -> None:
        # Atualiza o ângulo de rotação visual
        self._angulo_rotacao = (self._angulo_rotacao + self._velocidade_rotacao) % 360
        
        # Aplica a rotação ao sprite e atualiza o rect
        self.image = pygame.transform.rotate(self.original_image, self._angulo_rotacao)
        self.rect = self.image.get_rect(center=self._posicao.para_tupla())
        
        super().atualizar(delta_tempo)

    def dividir(self) -> list['Asteroide']:
        novos_asteroides = []
        proximo_tamanho_map = {"grande": "medio", "medio": "pequeno"}
        
        if self.get_tamanho_str() in proximo_tamanho_map:
            proximo_tamanho = proximo_tamanho_map[self.get_tamanho_str()]
            for i in range(2):
                offset_direcao = self.get_velocidade().normalizar() if self.get_velocidade().magnitude() > 0 else Vetor2D(1, 0)
                offset = offset_direcao * (self.get_raio() / 2) * (1 if i == 0 else -1)
                pos_fragmento = self.get_posicao() + offset
                vel_fragmento = self.get_velocidade().rotacionar(math.radians(random.uniform(-45, 45))) * random.uniform(0.8, 1.2)
                novos_asteroides.append(Asteroide(pos_fragmento, proximo_tamanho, velocidade=vel_fragmento))
        
        self.set_ativo(False)
        return novos_asteroides

    # --- Getters e Métodos de Save/Load ---
    def get_tamanho_str(self) -> str:
        return self._tamanho_str

    def get_pontos(self) -> int:
        return self._pontos

    def to_dict(self) -> dict:
        data = self.to_dict_base()
        data.update({
            "tamanho_str": self.get_tamanho_str(),
            "pontos": self.get_pontos(),
            "angulo_rotacao": self._angulo_rotacao,
            "velocidade_rotacao": self._velocidade_rotacao,
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Asteroide':
        obj = cls(
            Vetor2D.from_dict(data["posicao"]),
            data.get("tamanho_str", "grande"),
            Vetor2D.from_dict(data["velocidade"])
        )
        obj.restaurar_estado_base(data)
        obj._pontos = data.get("pontos", cls.TAMANHOS[obj.get_tamanho_str()][1])
        obj._angulo_rotacao = data.get("angulo_rotacao", 0)
        obj._velocidade_rotacao = data.get("velocidade_rotacao", random.uniform(-1, 1))
        return obj

class OVNIProjetil(GameObject):
    def __init__(self, posicao: Vetor2D, velocidade: Vetor2D, imagem_path: str):
        super().__init__(posicao, velocidade, 4)
        self._tempo_criacao = pygame.time.get_ticks()
        self.imagem_path = imagem_path # Guarda o caminho para o save/load
        
        self.original_image = pygame.image.load(self.imagem_path).convert_alpha()
        angulo = math.degrees(math.atan2(-velocidade.get_y(), velocidade.get_x()))
        self.image = pygame.transform.rotate(self.original_image, angulo)
        self.rect = self.image.get_rect(center=posicao.para_tupla())

    def atualizar(self, delta_tempo: float) -> None:
        super().atualizar(delta_tempo)
        if pygame.time.get_ticks() - self._tempo_criacao > 2000:
            self.set_ativo(False)

    def to_dict(self) -> dict:
        data = self.to_dict_base()
        data["tempo_criacao_relativo_ms"] = pygame.time.get_ticks() - self._tempo_criacao
        data["imagem_path"] = self.imagem_path
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'OVNIProjetil':
        obj = cls(
            Vetor2D.from_dict(data["posicao"]), 
            Vetor2D.from_dict(data["velocidade"]),
            data["imagem_path"] 
        )
        obj.restaurar_estado_base(data)
        tempo_vivido = data.get("tempo_criacao_relativo_ms", 0)
        obj._tempo_criacao = pygame.time.get_ticks() - tempo_vivido
        return obj



class OVNI(GameObject):
    def __init__(self, posicao: Vetor2D = None, velocidade: Vetor2D = None):
        raio_ovni = 20
        if posicao is None or velocidade is None:
            # Comportamento de spawn padrão
            direcao = random.choice([-1, 1])
            pos_x = -raio_ovni if direcao == 1 else LARGURA_TELA + raio_ovni
            pos_y = random.uniform(ALTURA_TELA * 0.1, ALTURA_TELA * 0.6)
            posicao_final = Vetor2D(pos_x, pos_y)
            velocidade_final = Vetor2D(VELOCIDADE_OVNI * direcao, 0)
            super().__init__(posicao_final, velocidade_final, raio_ovni)
        else:
            # Carregando de um save
            super().__init__(posicao, velocidade, raio_ovni)
        
        self._direcao_horizontal = 1 if self.get_velocidade().get_x() > 0 else -1
        self._tempo_em_tela_ms = 0
        self._ultimo_tiro_tempo_ms = pygame.time.get_ticks()

    def atualizar(self, delta_tempo: float) -> None:
        self._tempo_em_tela_ms += delta_tempo * 1000
        super().atualizar(delta_tempo) # Chama a lógica de movimento da classe mãe
        # Verifica se saiu da tela para desativar
        pos_x = self.get_posicao().get_x()
        raio = self.get_raio()
        if (self._direcao_horizontal == 1 and pos_x > LARGURA_TELA + raio) or \
           (self._direcao_horizontal == -1 and pos_x < -raio):
            self.set_ativo(False)

    # --- Getters, Setters e métodos de Save/Load ---
    def get_tempo_em_tela(self) -> float:
        return self._tempo_em_tela_ms

    def get_ultimo_tiro_tempo(self) -> int:
        return self._ultimo_tiro_tempo_ms

    def set_ultimo_tiro_tempo(self, tempo: int):
        self._ultimo_tiro_tempo_ms = tempo

    def tentar_atirar(self, posicao_nave: Vetor2D) -> list:
        return []

    def to_dict(self) -> dict:
        data = self.to_dict_base()
        data.update({
            "direcao_horizontal": self._direcao_horizontal,
            "tempo_em_tela_ms": self._tempo_em_tela_ms,
            "ultimo_tiro_tempo_ms_relativo": max(0, pygame.time.get_ticks() - self._ultimo_tiro_tempo_ms)
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'OVNI':
        obj = cls(Vetor2D.from_dict(data["posicao"]), Vetor2D.from_dict(data["velocidade"]))
        obj.restaurar_estado_base(data)
        obj._tempo_em_tela_ms = data.get("tempo_em_tela_ms", 0)
        obj._ultimo_tiro_tempo_ms = pygame.time.get_ticks() - data.get("ultimo_tiro_tempo_ms_relativo", 0)
        return obj

class OvniX(OVNI):
    def __init__(self, posicao: Vetor2D = None, velocidade: Vetor2D = None):
        super().__init__(posicao, velocidade)
        self.image = pygame.image.load(IMAGEM_OVNI_X).convert_alpha()
        self.rect = self.image.get_rect(center=self._posicao.para_tupla())

    def tentar_atirar(self, posicao_nave: Vetor2D) -> list['OVNIProjetil']:
        tempo_atual = pygame.time.get_ticks()
        pode_atirar_por_tempo = self.get_tempo_em_tela() > TEMPO_OVNI_ANTES_ATIRAR_SEGUNDOS * 1000
        cooldown_acabou = tempo_atual - self.get_ultimo_tiro_tempo() > COOLDOWN_TIRO_OVNI_MS
        
        if pode_atirar_por_tempo and cooldown_acabou:
            self.set_ultimo_tiro_tempo(tempo_atual)
            projeteis = []
            direcoes = [Vetor2D(1, 1).normalizar(), Vetor2D(-1, 1).normalizar(), Vetor2D(1, -1).normalizar(), Vetor2D(-1, -1).normalizar()]
            
            for direcao in direcoes:
                pos_tiro = self.get_posicao() + direcao * self.get_raio()
                vel_tiro = direcao * VELOCIDADE_PROJETIL_OVNI
                projeteis.append(OVNIProjetil(pos_tiro, vel_tiro, IMAGEM_PROJETIL_OVNI_X))
            return projeteis
        return []

class OvniCruz(OVNI):
    def __init__(self, posicao: Vetor2D = None, velocidade: Vetor2D = None):
        super().__init__(posicao, velocidade)
        self.image = pygame.image.load(IMAGEM_OVNI_CRUZ).convert_alpha()
        self.rect = self.image.get_rect(center=self._posicao.para_tupla())


    def tentar_atirar(self, posicao_nave: Vetor2D) -> list['OVNIProjetil']:
        tempo_atual = pygame.time.get_ticks()
        pode_atirar_por_tempo = self.get_tempo_em_tela() > TEMPO_OVNI_ANTES_ATIRAR_SEGUNDOS * 1000
        cooldown_acabou = tempo_atual - self.get_ultimo_tiro_tempo() > COOLDOWN_TIRO_OVNI_MS
        
        if pode_atirar_por_tempo and cooldown_acabou:
            self.set_ultimo_tiro_tempo(tempo_atual)
            projeteis = []
            direcoes = [Vetor2D(1, 0), Vetor2D(-1, 0), Vetor2D(0, 1), Vetor2D(0, -1)]
            
            for direcao in direcoes:
                pos_tiro = self.get_posicao() + direcao * self.get_raio()
                vel_tiro = direcao * VELOCIDADE_PROJETIL_OVNI
                projeteis.append(OVNIProjetil(pos_tiro, vel_tiro, IMAGEM_PROJETIL_OVNI_CRUZ))
            return projeteis
        return []
    
class LaserFantasma(GameObject):
    """Representa o raio laser disparado pela Nave Fantasma."""
    def __init__(self, pos_inicio: Vetor2D, direcao: Vetor2D):
        velocidade = direcao * VELOCIDADE_LASER_FANTASMA
        super().__init__(pos_inicio, velocidade, 5) 
        
        self.direcao = direcao # Salva para o Save/Load

        # Carrega, rotaciona e escala o sprite do laser
        self.original_image = pygame.image.load(IMAGEM_LASER_FANTASMA).convert_alpha()
        angulo = math.degrees(math.atan2(-direcao.get_y(), direcao.get_x()))
        
        self.image = pygame.transform.rotozoom(self.original_image, angulo, 1.0) 
        self.rect = self.image.get_rect(center=pos_inicio.para_tupla())

    def atualizar(self, delta_tempo: float) -> None:
        
        self._posicao += self._velocidade * delta_tempo * FPS
        if self.rect:
            self.rect.center = self._posicao.para_tupla()

        tela_rect = pygame.Rect(0, 0, LARGURA_TELA, ALTURA_TELA)
        if not self.rect.colliderect(tela_rect):
            self.set_ativo(False)

    def colide_com(self, outro_objeto: GameObject) -> bool:
        if not self.is_ativo() or not outro_objeto.is_ativo() or not self.rect or not outro_objeto.rect:
            return False
        return self.rect.colliderect(outro_objeto.rect)

    def to_dict(self) -> dict:
        data = self.to_dict_base()
        data.update({
            "direcao": self.direcao.to_dict(),
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'LaserFantasma':
        obj = cls(
            Vetor2D.from_dict(data["posicao"]), 
            Vetor2D.from_dict(data["direcao"])
        )
        obj.restaurar_estado_base(data)
        return obj

class EstadoFantasma(Enum):
    """Enum para gerenciar os estados da Nave Fantasma."""
    INVISIVEL = auto()
    CARREGANDO = auto()
    DISPARANDO = auto()

class NaveFantasma(GameObject):
    """Um inimigo que aparece, carrega um ataque e desaparece."""
    def __init__(self):
        super().__init__(Vetor2D(-100, -100), Vetor2D(), 18)
        
        self._estado = EstadoFantasma.INVISIVEL
        self._tempo_proxima_acao = pygame.time.get_ticks() + random.randint(2000, DURACAO_FANTASMA_INVISIVEL_MS)
        self._alvo_disparo: Optional[Vetor2D] = None
        
        self.set_ativo(False)

        self.image = pygame.image.load(IMAGEM_FANTASMA).convert_alpha()
        self.rect = self.image.get_rect(center=self._posicao.para_tupla())

    def atualizar(self, delta_tempo: float, posicao_nave: Optional[Vetor2D] = None) -> Optional['LaserFantasma']:
        """Atualiza a máquina de estados da Nave Fantasma."""
        tempo_atual = pygame.time.get_ticks()
        laser_criado = None
        estado_atual = self.get_estado()

        if estado_atual == EstadoFantasma.INVISIVEL:
            if tempo_atual >= self.get_tempo_proxima_acao():
                self.set_estado(EstadoFantasma.CARREGANDO)
                self.set_ativo(True)
                nova_pos = Vetor2D(random.randrange(50, LARGURA_TELA - 50), random.randrange(50, ALTURA_TELA - 50))
                self.set_posicao(nova_pos)
                # Atualiza a posição do rect quando a nave aparece
                if self.rect: self.rect.center = nova_pos.para_tupla()
                self.set_tempo_proxima_acao(tempo_atual + DURACAO_FANTASMA_CARREGANDO_MS)
                if posicao_nave:
                    self.set_alvo_disparo(posicao_nave)

        elif estado_atual == EstadoFantasma.CARREGANDO:
            if tempo_atual >= self.get_tempo_proxima_acao() and self.get_alvo_disparo():
                self.set_estado(EstadoFantasma.DISPARANDO)
                self.set_tempo_proxima_acao(tempo_atual + DURACAO_LASER_FANTASMA_MS)
                direcao = (self.get_alvo_disparo() - self.get_posicao()).normalizar()
                laser_criado = LaserFantasma(self.get_posicao(), direcao)

        elif estado_atual == EstadoFantasma.DISPARANDO:
            if tempo_atual >= self.get_tempo_proxima_acao():
                self.set_estado(EstadoFantasma.INVISIVEL)
                self.set_ativo(False)
                self.set_tempo_proxima_acao(tempo_atual + DURACAO_FANTASMA_INVISIVEL_MS)
                self.set_alvo_disparo(None)

        super().atualizar(delta_tempo)
        return laser_criado

    def desenhar(self, tela: pygame.Surface) -> None:
        # A Nave Fantasma só é visível quando está carregando o ataque
        if not self.is_ativo() or self.get_estado() != EstadoFantasma.CARREGANDO:
            return

        if self.image and self.rect:
            tela.blit(self.image, self.rect)

        tempo_atual = pygame.time.get_ticks()
        progresso = 1 - max(0, (self.get_tempo_proxima_acao() - tempo_atual)) / DURACAO_FANTASMA_CARREGANDO_MS
        raio_indicador = self.get_raio() * 2 * progresso
        
        if raio_indicador > 2:
            pygame.draw.circle(tela, COR_FANTASMA_CARREGANDO, self._posicao.para_tupla(), int(raio_indicador), 2)

    # --- Getters, Setters e Save/Load ---
    def get_estado(self) -> EstadoFantasma: return self._estado
    def set_estado(self, novo_estado: EstadoFantasma): self._estado = novo_estado
    def get_tempo_proxima_acao(self) -> int: return self._tempo_proxima_acao
    def set_tempo_proxima_acao(self, tempo: int): self._tempo_proxima_acao = tempo
    def get_alvo_disparo(self) -> Optional[Vetor2D]: return self._alvo_disparo
    def set_alvo_disparo(self, alvo: Optional[Vetor2D]): self._alvo_disparo = alvo
    
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
        estado_nome = data.get("estado", "INVISIVEL")
        obj.set_estado(EstadoFantasma[estado_nome])
        tempo_restante = data.get("tempo_proxima_acao_restante_ms", 0)
        obj.set_tempo_proxima_acao(pygame.time.get_ticks() + tempo_restante)
        alvo_data = data.get("alvo_disparo")
        obj.set_alvo_disparo(Vetor2D.from_dict(alvo_data) if alvo_data else None)
        return obj
    
CLASSE_MAP = {
    'Nave': Nave,   
    'Projetil': Projetil,
    'Asteroide': Asteroide,
    'OVNIProjetil': OVNIProjetil,
    'OVNI': OVNI,
    'OvniX': OvniX,
    'OvniCruz': OvniCruz,
    'NaveFantasma': NaveFantasma,
    'LaserFantasma': LaserFantasma
}

