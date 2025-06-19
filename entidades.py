import pygame
import math
import random
from enum import Enum, auto

# Importações locais (ajuste conforme estrutura do seu projeto)
from config import *
from vetor import Vetor2D

# O mapa de classes será preenchido no final deste arquivo
CLASSE_MAP = {}

class GameObject:
    """ Classe base para todos os objetos do jogo (Nave, Asteroide, Projétil). """
    def __init__(self, posicao: Vetor2D, velocidade: Vetor2D, raio: float, cor: tuple):
        self.posicao = posicao
        self.velocidade = velocidade
        self.raio = raio
        self.cor = cor
        self.ativo = True

    def atualizar(self, delta_tempo: float) -> None:
        """
        Lógica de atualização genérica: apenas movimento baseado na velocidade e wrap-around.
        As classes filhas devem chamar super().atualizar(delta_tempo) para usar este comportamento.
        """
        self.posicao += self.velocidade * delta_tempo * FPS # Usa delta_tempo para movimento consistente
        # Lógica de "wrap-around" na tela
        if self.posicao.x < -self.raio:
            self.posicao.x = LARGURA_TELA + self.raio
        elif self.posicao.x > LARGURA_TELA + self.raio:
            self.posicao.x = -self.raio
        
        if self.posicao.y < -self.raio:
            self.posicao.y = ALTURA_TELA + self.raio
        elif self.posicao.y > ALTURA_TELA + self.raio:
            self.posicao.y = -self.raio

    def desenhar(self, tela: pygame.Surface) -> None:
        """ Desenha o objeto na tela (um círculo por padrão). """
        if self.ativo:
            pygame.draw.circle(tela, self.cor,
                               (int(self.posicao.x), int(self.posicao.y)),
                               int(self.raio))

    def colide_com(self, outro_objeto: 'GameObject') -> bool:
        """ Verifica colisão com outro GameObject (baseado em raio). """
        if not self.ativo or not outro_objeto.ativo:
            return False
        dx = self.posicao.x - outro_objeto.posicao.x
        dy = self.posicao.y - outro_objeto.posicao.y
        dist_quadrada = dx * dx + dy * dy
        raios_soma = self.raio + outro_objeto.raio
        return dist_quadrada < raios_soma * raios_soma

    def to_dict_base(self) -> dict:
        """Converte os atributos base para um dicionário serializável."""
        return {
            "classe_tipo": self.__class__.__name__,
            "posicao": self.posicao.to_dict(),
            "velocidade": self.velocidade.to_dict(),
            "raio": self.raio,
            "cor_rgb": list(self.cor),
            "ativo": self.ativo
        }

    @classmethod
    def from_dict_base_data(cls, data: dict) -> dict:
        """Retorna os dados básicos para o __init__ da classe filha."""
        return {
            "posicao": Vetor2D.from_dict(data["posicao"]),
            "velocidade": Vetor2D.from_dict(data["velocidade"]),
            "raio": data.get("raio", 10.0),
            "cor": tuple(data.get("cor_rgb", [255, 255, 255]))
        }

    def restaurar_estado_base(self, data: dict):
        """Restaura atributos comuns após a criação do objeto."""
        self.ativo = data.get("ativo", True)


class Nave(GameObject):
    def __init__(self, posicao: Vetor2D):
        super().__init__(posicao, Vetor2D(), 15, VERDE)
        self.angulo_graus = 0.0
        self.rotacionando_esquerda = False
        self.rotacionando_direita = False
        self.acelerando = False
        self.ultimo_tiro_tempo = 0
        self.tem_tiro_triplo = False
        self.tempo_fim_tiro_triplo = 0
        self.tempo_invulneravel_fim = 0

    def desenhar(self, tela: pygame.Surface) -> None:
        if not self.ativo:
            return

        cor_atual = self.cor
        # Se estiver invulnerável, pisca em branco
        if pygame.time.get_ticks() < self.tempo_invulneravel_fim:
             cor_atual = BRANCO if (pygame.time.get_ticks() // 100) % 2 == 0 else self.cor
        # Se tiver tiro triplo (e não estiver invulnerável), pisca em azul
        elif self.tem_tiro_triplo and pygame.time.get_ticks() < self.tempo_fim_tiro_triplo:
            cor_atual = AZUL if (pygame.time.get_ticks() // 200) % 2 == 0 else self.cor

        angulo_rad = math.radians(self.angulo_graus)
        ponta = Vetor2D(0, -self.raio).rotacionar(angulo_rad)
        base_esq = Vetor2D(-self.raio * 0.6, self.raio * 0.6).rotacionar(angulo_rad)
        base_dir = Vetor2D(self.raio * 0.6, self.raio * 0.6).rotacionar(angulo_rad)

        pontos = [
            (self.posicao + ponta).para_tupla(),
            (self.posicao + base_esq).para_tupla(),
            (self.posicao + base_dir).para_tupla()
        ]
        pygame.draw.polygon(tela, cor_atual, pontos, 1)

        if self.acelerando:
            tras = Vetor2D(0, self.raio * 1.2).rotacionar(angulo_rad)
            esq = Vetor2D(-self.raio * 0.3, self.raio * 0.8).rotacionar(angulo_rad)
            dir_ = Vetor2D(self.raio * 0.3, self.raio * 0.8).rotacionar(angulo_rad)
            fogo = [
                (self.posicao + tras).para_tupla(),
                (self.posicao + esq).para_tupla(),
                (self.posicao + dir_).para_tupla()
            ]
            pygame.draw.polygon(tela, VERMELHO, fogo, 0)

    def atualizar(self, delta_tempo: float) -> None:
        tempo_atual = pygame.time.get_ticks()
        if self.tem_tiro_triplo and tempo_atual >= self.tempo_fim_tiro_triplo:
            self.tem_tiro_triplo = False

        if self.rotacionando_esquerda:
            self.angulo_graus -= VELOCIDADE_ROTACAO_NAVE
        if self.rotacionando_direita:
            self.angulo_graus += VELOCIDADE_ROTACAO_NAVE
        self.angulo_graus %= 360

        if self.acelerando:
            angulo_rad = math.radians(self.angulo_graus - 90)
            direcao = Vetor2D(math.cos(angulo_rad), math.sin(angulo_rad))
            self.velocidade += direcao * ACELERACAO_NAVE

        self.velocidade *= FRICCAO_NAVE
        super().atualizar(delta_tempo) # Chama o método da classe mãe para mover

    def atirar(self) -> list['Projetil']:
        tempo_atual = pygame.time.get_ticks()
        projeteis_criados = []
        if tempo_atual - self.ultimo_tiro_tempo > COOLDOWN_TIRO:
            self.ultimo_tiro_tempo = tempo_atual
            angulo_base_rad = math.radians(self.angulo_graus - 90)
            direcao_base = Vetor2D(math.cos(angulo_base_rad), math.sin(angulo_base_rad))
            pos_base = self.posicao + direcao_base * self.raio
            vel_base = direcao_base * VELOCIDADE_PROJETIL + self.velocidade
            projeteis_criados.append(Projetil(pos_base, vel_base))

            if self.tem_tiro_triplo and tempo_atual < self.tempo_fim_tiro_triplo:
                angulo_lateral_rad = math.radians(ANGULO_TIRO_TRIPLO_GRAUS)
                for offset in [-angulo_lateral_rad, angulo_lateral_rad]:
                    direcao = direcao_base.rotacionar(offset)
                    pos = self.posicao + direcao * self.raio
                    vel = direcao * VELOCIDADE_PROJETIL + self.velocidade
                    projeteis_criados.append(Projetil(pos, vel))
        return projeteis_criados

    def ativar_tiro_triplo(self, duracao_segundos: int) -> None:
        if self.ativo:
            self.tem_tiro_triplo = True
            self.tempo_fim_tiro_triplo = pygame.time.get_ticks() + duracao_segundos * 1000

    def to_dict(self) -> dict:
        data = super().to_dict_base()
        data.update({
            "angulo_graus": self.angulo_graus,
            "tem_tiro_triplo": self.tem_tiro_triplo,
            "tempo_fim_tiro_triplo_restante_ms": max(0, self.tempo_fim_tiro_triplo - pygame.time.get_ticks()) if self.tem_tiro_triplo else 0
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Nave':
        obj = cls(Vetor2D.from_dict(data["posicao"]))
        obj.velocidade = Vetor2D.from_dict(data["velocidade"])
        obj.restaurar_estado_base(data)
        obj.angulo_graus = data.get("angulo_graus", 0.0)
        obj.tem_tiro_triplo = data.get("tem_tiro_triplo", False)
        if obj.tem_tiro_triplo:
            obj.tempo_fim_tiro_triplo = pygame.time.get_ticks() + data.get("tempo_fim_tiro_triplo_restante_ms", 0)
        else:
            obj.tempo_fim_tiro_triplo = 0
        return obj

class Projetil(GameObject):
    def __init__(self, posicao: Vetor2D, velocidade: Vetor2D):
        super().__init__(posicao, velocidade, 3, BRANCO)
        self.frames_vividos = 0

    def atualizar(self, delta_tempo: float) -> None:
        super().atualizar(delta_tempo)
        self.frames_vividos += 1
        if self.frames_vividos > DURACAO_PROJETIL:
            self.ativo = False

    def to_dict(self) -> dict:
        data = super().to_dict_base()
        data["frames_vividos"] = self.frames_vividos
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Projetil':
        obj = cls(Vetor2D.from_dict(data["posicao"]), Vetor2D.from_dict(data["velocidade"]))
        obj.restaurar_estado_base(data)
        obj.frames_vividos = data.get("frames_vividos", 0)
        return obj

class Asteroide(GameObject):
    TAMANHOS = {
        "grande": (35, PONTOS_ASTEROIDE_GRANDE),
        "medio": (25, PONTOS_ASTEROIDE_MEDIO),
        "pequeno": (12, PONTOS_ASTEROIDE_PEQUENO)
    }

    def __init__(self, posicao: Vetor2D, tamanho_str="grande", velocidade: Vetor2D = None):
        raio, self.pontos = self.TAMANHOS[tamanho_str]
        vel = velocidade if velocidade is not None else Vetor2D(
            random.uniform(VEL_MIN_ASTEROIDE, VEL_MAX_ASTEROIDE) * random.choice([-1, 1]),
            random.uniform(VEL_MIN_ASTEROIDE, VEL_MAX_ASTEROIDE) * random.choice([-1, 1])
        )
        super().__init__(posicao, vel, raio, CINZA_CLARO)
        self.tamanho_str = tamanho_str
        self.angulo_rotacao = random.uniform(0, 360)
        self.velocidade_rotacao = random.uniform(-1, 1)
        self.offsets_vertices = []

        num_vertices = random.randint(7, 12)
        for _ in range(num_vertices):
            angulo = random.uniform(0, 2 * math.pi)
            dist_raio = random.uniform(self.raio * 0.7, self.raio * 1.3)
            self.offsets_vertices.append(Vetor2D(math.cos(angulo) * dist_raio, math.sin(angulo) * dist_raio))
        self.offsets_vertices.sort(key=lambda v: math.atan2(v.y, v.x))

    def desenhar(self, tela: pygame.Surface) -> None:
        if self.ativo:
            pontos = []
            for offset in self.offsets_vertices:
                rot_offset = offset.rotacionar(math.radians(self.angulo_rotacao))
                ponto_absoluto = self.posicao + rot_offset
                pontos.append(ponto_absoluto.para_tupla())
            if len(pontos) >= 3:
                pygame.draw.polygon(tela, self.cor, pontos, 1)

    def atualizar(self, delta_tempo: float) -> None:
        super().atualizar(delta_tempo)
        self.angulo_rotacao = (self.angulo_rotacao + self.velocidade_rotacao) % 360

    def dividir(self) -> list['Asteroide']:
        novos_asteroides = []
        proximo_tamanho_map = {"grande": "medio", "medio": "pequeno"}
        if self.tamanho_str in proximo_tamanho_map:
            proximo_tamanho = proximo_tamanho_map[self.tamanho_str]
            for i in range(2):
                offset_direcao = self.velocidade.normalizar() if self.velocidade.magnitude() > 0 else Vetor2D(1, 0)
                offset = offset_direcao * (self.raio / 2)
                
                # Inverte a direção do empurrão para o segundo fragmento
                if i == 1:
                    offset = -offset

                pos_fragmento = self.posicao + offset

                # Adiciona uma pequena variação na velocidade para parecer mais natural
                vel_fragmento = self.velocidade.rotacionar(math.radians(random.uniform(-45, 45))) * random.uniform(0.8, 1.2)
                
                novos_asteroides.append(Asteroide(pos_fragmento, proximo_tamanho, velocidade=vel_fragmento))
        
        self.ativo = False
        return novos_asteroides


    def to_dict(self) -> dict:
        data = super().to_dict_base()
        data.update({"tamanho_str": self.tamanho_str, "pontos": self.pontos, "angulo_rotacao": self.angulo_rotacao, "velocidade_rotacao": self.velocidade_rotacao, "offsets_vertices": [v.to_dict() for v in self.offsets_vertices]})
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Asteroide':
        obj = cls(Vetor2D.from_dict(data["posicao"]), data.get("tamanho_str", "grande"), Vetor2D.from_dict(data["velocidade"]))
        obj.restaurar_estado_base(data)
        obj.pontos = data.get("pontos", cls.TAMANHOS[obj.tamanho_str][1])
        obj.angulo_rotacao = data.get("angulo_rotacao", 0)
        obj.velocidade_rotacao = data.get("velocidade_rotacao", random.uniform(-1, 1))
        obj.offsets_vertices = [Vetor2D.from_dict(v_dict) for v_dict in data.get("offsets_vertices", [])]
        return obj

class OVNI(GameObject):
    def __init__(self, posicao: Vetor2D = None, velocidade: Vetor2D = None):
        if posicao is None or velocidade is None:
            self.direcao_horizontal = random.choice([-1, 1])
            raio_ovni = 20
            pos_x_inicial = -raio_ovni if self.direcao_horizontal == 1 else LARGURA_TELA + raio_ovni
            pos_y_inicial = random.uniform(ALTURA_TELA * 0.1, ALTURA_TELA * 0.6)
            posicao_final = Vetor2D(pos_x_inicial, pos_y_inicial)
            velocidade_final = Vetor2D(VELOCIDADE_OVNI * self.direcao_horizontal, 0)
            super().__init__(posicao_final, velocidade_final, raio_ovni, COR_OVNI)
        else:
            super().__init__(posicao, velocidade, 20, COR_OVNI)
            self.direcao_horizontal = 1 if velocidade.x > 0 else -1
        
        self.tempo_em_tela_ms = 0
        self.ultimo_tiro_tempo_ms = pygame.time.get_ticks()
        print("DEBUG: OVNI Base criado.")

    def atualizar(self, delta_tempo: float) -> None:
        self.tempo_em_tela_ms += delta_tempo * 1000
        super().atualizar(delta_tempo)
        if (self.direcao_horizontal == 1 and self.posicao.x > LARGURA_TELA + self.raio) or \
           (self.direcao_horizontal == -1 and self.posicao.x < -self.raio):
            self.ativo = False

    def tentar_atirar(self, posicao_nave: Vetor2D) -> list['OVNIProjetil']:
        tempo_atual = pygame.time.get_ticks()
        if self.tempo_em_tela_ms > TEMPO_OVNI_ANTES_ATIRAR_SEGUNDOS * 1000 and \
           tempo_atual - self.ultimo_tiro_tempo_ms > COOLDOWN_TIRO_OVNI_MS:
            self.ultimo_tiro_tempo_ms = tempo_atual
            print("DEBUG: OVNI Base tentando atirar.")
            direcao_tiro = (posicao_nave - self.posicao).normalizar()
            pos_tiro = self.posicao + direcao_tiro * self.raio
            vel_tiro = direcao_tiro * VELOCIDADE_PROJETIL_OVNI
            return [OVNIProjetil(pos_tiro, vel_tiro)]
        return []

    def to_dict(self) -> dict:
        data = super().to_dict_base()
        data.update({"direcao_horizontal": self.direcao_horizontal, "tempo_em_tela_ms": self.tempo_em_tela_ms, "ultimo_tiro_tempo_ms_relativo": max(0, pygame.time.get_ticks() - self.ultimo_tiro_tempo_ms)})
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'OVNI':
        obj = cls(Vetor2D.from_dict(data["posicao"]), Vetor2D.from_dict(data["velocidade"]))
        obj.restaurar_estado_base(data)
        obj.tempo_em_tela_ms = data.get("tempo_em_tela_ms", 0)
        obj.ultimo_tiro_tempo_ms = pygame.time.get_ticks() - data.get("ultimo_tiro_tempo_ms_relativo", 0)
        return obj

class OVNIProjetil(GameObject):
    def __init__(self, posicao: Vetor2D, velocidade: Vetor2D, cor=None):
        super().__init__(posicao, velocidade, 4, cor or COR_PROJETIL_OVNI)
        self.tempo_criacao = pygame.time.get_ticks()

    def atualizar(self, delta_tempo: float) -> None:
        super().atualizar(delta_tempo)
        if pygame.time.get_ticks() - self.tempo_criacao > 2000:
            self.ativo = False

    def to_dict(self) -> dict:
        data = super().to_dict_base()
        data["tempo_criacao_relativo_ms"] = pygame.time.get_ticks() - self.tempo_criacao
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'OVNIProjetil':
        obj = cls(Vetor2D.from_dict(data["posicao"]), Vetor2D.from_dict(data["velocidade"]))
        obj.restaurar_estado_base(data)
        obj.tempo_criacao = pygame.time.get_ticks() - data.get("tempo_criacao_relativo_ms", 0)
        return obj

class OvniX(OVNI):
    def __init__(self, posicao: Vetor2D = None, velocidade: Vetor2D = None):
        super().__init__(posicao, velocidade)
        self.cor = AZUL
        print("DEBUG: OVNI do tipo X criado.")

    def tentar_atirar(self, posicao_nave: Vetor2D) -> list['OVNIProjetil']:
        tempo_atual = pygame.time.get_ticks()
        if self.tempo_em_tela_ms > TEMPO_OVNI_ANTES_ATIRAR_SEGUNDOS * 1000 and \
           tempo_atual - self.ultimo_tiro_tempo_ms > COOLDOWN_TIRO_OVNI_MS:
            self.ultimo_tiro_tempo_ms = tempo_atual
            print("DEBUG: OvniX atirando em X.")
            projeteis = []
            direcoes = [Vetor2D(1, 1).normalizar(), Vetor2D(-1, 1).normalizar(), Vetor2D(1, -1).normalizar(), Vetor2D(-1, -1).normalizar()]
            for direcao in direcoes:
                projeteis.append(OVNIProjetil(self.posicao + direcao * self.raio, direcao * VELOCIDADE_PROJETIL_OVNI, cor=COR_PROJETIL_OVNI_X))
            return projeteis
        return []

    def desenhar(self, tela: pygame.Surface) -> None:
        if not self.ativo: return
        pygame.draw.circle(tela, self.cor, self.posicao.para_tupla(), int(self.raio), 1)
        offset = Vetor2D(self.raio, self.raio).normalizar() * self.raio
        p1 = self.posicao + offset.rotacionar(math.radians(45)); p2 = self.posicao - offset.rotacionar(math.radians(45))
        p3 = self.posicao + offset.rotacionar(math.radians(135)); p4 = self.posicao - offset.rotacionar(math.radians(135))
        pygame.draw.line(tela, self.cor, p1.para_tupla(), p2.para_tupla(), 2)
        pygame.draw.line(tela, self.cor, p3.para_tupla(), p4.para_tupla(), 2)

class OvniCruz(OVNI):
    def __init__(self, posicao: Vetor2D = None, velocidade: Vetor2D = None):
        super().__init__(posicao, velocidade)
        self.cor = VERDE
        print("DEBUG: OVNI do tipo Cruz criado.")

    def tentar_atirar(self, posicao_nave: Vetor2D) -> list['OVNIProjetil']:
        tempo_atual = pygame.time.get_ticks()
        if self.tempo_em_tela_ms > TEMPO_OVNI_ANTES_ATIRAR_SEGUNDOS * 1000 and \
           tempo_atual - self.ultimo_tiro_tempo_ms > COOLDOWN_TIRO_OVNI_MS:
            self.ultimo_tiro_tempo_ms = tempo_atual
            print("DEBUG: OvniCruz atirando em cruz.")
            projeteis = []
            direcoes = [Vetor2D(1, 0), Vetor2D(-1, 0), Vetor2D(0, 1), Vetor2D(0, -1)]
            for direcao in direcoes:
                projeteis.append(OVNIProjetil(self.posicao + direcao * self.raio, direcao * VELOCIDADE_PROJETIL_OVNI, cor=COR_PROJETIL_OVNI_CRUZ))
            return projeteis
        return []

    def desenhar(self, tela: pygame.Surface) -> None:
        if not self.ativo: return
        pygame.draw.circle(tela, self.cor, self.posicao.para_tupla(), int(self.raio), 1)
        offset = Vetor2D(self.raio, 0)
        p1 = self.posicao - offset; p2 = self.posicao + offset
        p3 = self.posicao - Vetor2D(0, self.raio); p4 = self.posicao + Vetor2D(0, self.raio)
        pygame.draw.line(tela, self.cor, p1.para_tupla(), p2.para_tupla(), 2)
        pygame.draw.line(tela, self.cor, p3.para_tupla(), p4.para_tupla(), 2)

class LaserFantasma(GameObject):
    def __init__(self, pos_inicio: Vetor2D, pos_fim: Vetor2D):
        super().__init__(pos_inicio, Vetor2D(), 0, COR_FANTASMA_LASER)
        self.pos_inicio = pos_inicio
        self.pos_fim = pos_fim
        self.tempo_criacao = pygame.time.get_ticks()

    def atualizar(self, delta_tempo: float) -> None:
        if pygame.time.get_ticks() - self.tempo_criacao > DURACAO_LASER_FANTASMA_MS:
            self.ativo = False

    def desenhar(self, tela: pygame.Surface) -> None:
        if self.ativo:
            pygame.draw.line(tela, self.cor, self.pos_inicio.para_tupla(), self.pos_fim.para_tupla(), 4)

    def colide_com(self, outro_objeto: GameObject) -> bool:
        if not self.ativo or not outro_objeto.ativo: return False
        return pygame.Rect(self.pos_inicio.x, self.pos_inicio.y, self.pos_fim.x - self.pos_inicio.x, self.pos_fim.y - self.pos_inicio.y).clipline((outro_objeto.posicao - Vetor2D(outro_objeto.raio, outro_objeto.raio)).para_tupla(), (outro_objeto.posicao + Vetor2D(outro_objeto.raio, outro_objeto.raio)).para_tupla())

    def to_dict(self) -> dict:
        data = super().to_dict_base()
        data.update({
            "pos_inicio": self.pos_inicio.to_dict(),
            "pos_fim": self.pos_fim.to_dict(),
            "tempo_criacao_relativo_ms": pygame.time.get_ticks() - self.tempo_criacao
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'LaserFantasma':
        obj = cls(Vetor2D.from_dict(data["pos_inicio"]), Vetor2D.from_dict(data["pos_fim"]))
        obj.restaurar_estado_base(data)
        obj.tempo_criacao = pygame.time.get_ticks() - data.get("tempo_criacao_relativo_ms", DURACAO_LASER_FANTASMA_MS)
        return obj

class EstadoFantasma(Enum):
    INVISIVEL = auto()
    CARREGANDO = auto()
    DISPARANDO = auto()

class NaveFantasma(GameObject):
    def __init__(self):
        super().__init__(Vetor2D(-100, -100), Vetor2D(), 18, COR_FANTASMA)
        self.estado = EstadoFantasma.INVISIVEL
        self.ativo = False
        self.tempo_proxima_acao = pygame.time.get_ticks() + random.randint(2000, DURACAO_FANTASMA_INVISIVEL_MS)
        self.alvo_disparo: Vetor2D | None = None

    def atualizar(self, delta_tempo: float, posicao_nave: Vetor2D = None) -> LaserFantasma | None:
        """Atualiza o estado da Nave Fantasma. Pode retornar um objeto LaserFantasma se disparar."""
        tempo_atual = pygame.time.get_ticks()
        laser_criado = None

        if self.estado == EstadoFantasma.INVISIVEL:
            # Print para debugar o timer
            print(f"FANTASMA CHECK: Atual={tempo_atual}, PróximaAção={self.tempo_proxima_acao}, Diferença={self.tempo_proxima_acao - tempo_atual}")

            if tempo_atual >= self.tempo_proxima_acao:
                self.estado = EstadoFantasma.CARREGANDO
                self.ativo = True
                self.posicao = Vetor2D(random.randrange(50, LARGURA_TELA - 50), random.randrange(50, ALTURA_TELA - 50))
                self.tempo_proxima_acao = tempo_atual + DURACAO_FANTASMA_CARREGANDO_MS
                if posicao_nave:
                    self.alvo_disparo = posicao_nave
                print("DEBUG: Nave Fantasma apareceu e está carregando.")

        elif self.estado == EstadoFantasma.CARREGANDO:
            if tempo_atual >= self.tempo_proxima_acao:
                self.estado = EstadoFantasma.DISPARANDO
                self.tempo_proxima_acao = tempo_atual + DURACAO_LASER_FANTASMA_MS
                if self.alvo_disparo:
                    direcao = (self.alvo_disparo - self.posicao).normalizar()
                    pos_fim_laser = self.posicao + direcao * 2000
                    laser_criado = LaserFantasma(self.posicao, pos_fim_laser)
                    print("DEBUG: Nave Fantasma disparou laser.")

        elif self.estado == EstadoFantasma.DISPARANDO:
            if tempo_atual >= self.tempo_proxima_acao:
                self.estado = EstadoFantasma.INVISIVEL
                self.ativo = False
                self.tempo_proxima_acao = tempo_atual + DURACAO_FANTASMA_INVISIVEL_MS
                self.alvo_disparo = None
                print("DEBUG: Nave Fantasma desapareceu.")

        return laser_criado
    
    def to_dict(self) -> dict:
        data = super().to_dict_base()
        data.update({
            "estado": self.estado.name, # Salva o nome do estado (ex: "INVISIVEL")
            "tempo_proxima_acao_restante_ms": max(0, self.tempo_proxima_acao - pygame.time.get_ticks()),
            "alvo_disparo": self.alvo_disparo.to_dict() if self.alvo_disparo else None
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'NaveFantasma':
        obj = cls() # Cria uma instância
        obj.restaurar_estado_base(data) # Restaura atributos base como ativo, posição, velocidade
        obj.posicao = Vetor2D.from_dict(data["posicao"])
        obj.velocidade = Vetor2D.from_dict(data["velocidade"])

        # Restaura o estado a partir do nome salvo
        estado_nome = data.get("estado", "INVISIVEL")
        obj.estado = EstadoFantasma[estado_nome] # Converte string de volta para o Enum

        # Recalcula o tempo da próxima ação
        tempo_restante = data.get("tempo_proxima_acao_restante_ms", 0)
        obj.tempo_proxima_acao = pygame.time.get_ticks() + tempo_restante
        
        # Restaura o alvo se ele existia
        alvo_data = data.get("alvo_disparo")
        if alvo_data:
            obj.alvo_disparo = Vetor2D.from_dict(alvo_data)
        else:
            obj.alvo_disparo = None
        
        return obj


    def desenhar(self, tela: pygame.Surface) -> None:
        if not self.ativo or self.estado != EstadoFantasma.CARREGANDO: return
        p1 = Vetor2D(0, -self.raio) + self.posicao
        p2 = Vetor2D(self.raio * 0.6, 0) + self.posicao
        p3 = Vetor2D(0, self.raio) + self.posicao
        p4 = Vetor2D(-self.raio * 0.6, 0) + self.posicao
        pygame.draw.polygon(tela, self.cor, [p1.para_tupla(), p2.para_tupla(), p3.para_tupla(), p4.para_tupla()], 2)
        tempo_atual = pygame.time.get_ticks()
        progresso = max(0, (self.tempo_proxima_acao - tempo_atual) / DURACAO_FANTASMA_CARREGANDO_MS)
        raio_indicador = self.raio * 1.5 * progresso
        if raio_indicador > 2:
            pygame.draw.circle(tela, COR_FANTASMA_CARREGANDO, self.posicao.para_tupla(), int(raio_indicador), 1)

for cls in [Nave, Projetil, Asteroide, OVNI, OVNIProjetil, LaserFantasma, NaveFantasma, OvniX, OvniCruz]:
    if hasattr(cls, '__name__'):
        CLASSE_MAP[cls.__name__] = cls