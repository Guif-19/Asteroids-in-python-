# gerenciador.py (VERSÃO FINAL, CORRIGIDA E COMPLETA)

import pygame
import pygame_menu
import os
import json
import random
from enum import Enum, auto
from config import *
from entidades import * # Ajuste o nome se seu arquivo for diferente
from vetor import Vetor2D

class EstadoJogoLoop(Enum):
    CONTINUAR_JOGO = auto()
    VOLTAR_AO_MENU_SEM_SALVAR = auto()
    VOLTAR_AO_MENU_COM_SAVE = auto()
    VOLTAR_AO_MENU_GAME_OVER = auto()

class FundoEstrelado:
    def __init__(self):
        self.__estrelas_lentas = [[random.randrange(LARGURA_TELA), random.randrange(ALTURA_TELA), 1] for _ in range(NUM_ESTRELAS_LENTAS)]
        self.__estrelas_rapidas = [[random.randrange(LARGURA_TELA), random.randrange(ALTURA_TELA), 2] for _ in range(NUM_ESTRELAS_RAPIDAS)]

    def atualizar(self, delta_tempo: float):
        for estrela in self.__estrelas_lentas: estrela[1] = (estrela[1] + VELOCIDADE_ESTRELAS_LENTA * delta_tempo * FPS) % ALTURA_TELA
        for estrela in self.__estrelas_rapidas: estrela[1] = (estrela[1] + VELOCIDADE_ESTRELAS_RAPIDA * delta_tempo * FPS) % ALTURA_TELA

    def desenhar(self, tela: pygame.Surface):
        for x, y, tamanho in self.__estrelas_lentas: pygame.draw.circle(tela, (150, 150, 150), (int(x), int(y)), max(1, tamanho // 2))
        for x, y, tamanho in self.__estrelas_rapidas: pygame.draw.circle(tela, COR_ESTRELA, (int(x), int(y)), tamanho)

class GerenciadorJogo:
    """
    Orquestra todos os elementos do jogo, incluindo o loop principal,
    lógica de atualização, colisões, e gerenciamento de estado.
    """
    def __init__(self, tela: pygame.Surface, clock: pygame.time.Clock, gerenciador_som):
        self.__tela = tela
        self.__clock = clock
        self.__gerenciador_som = gerenciador_som
        self.__nave: Optional[Nave] = None
        self.__asteroides: list[Asteroide] = []
        self.__projeteis: list[Projetil] = []
        self.__ovnis: list[OVNI] = []
        self.__ovni_projeteis: list[OVNIProjetil] = []
        self.__fantasmas: list[NaveFantasma] = []
        self.__lasers_fantasma: list[LaserFantasma] = []
        self.__fundo_estrelado = FundoEstrelado()
        self.__pontuacao = 0
        self.__vidas = VIDAS_INICIAIS
        self.__game_over = False
        self.__nivel_atual = 0
        self.__fonte_hud = pygame.font.Font(None, 36)
        self.__fonte_game_over = pygame.font.Font(None, 72)
        self.__jogo_pausado = False
        self.__acao_menu_pausa: Optional[EstadoJogoLoop] = None
        self.__tempo_para_respawn = 0

    def reiniciar_jogo_completo(self):
        """
        Reseta o jogo para um estado inicial limpo.
        """
        if os.path.exists(ARQUIVO_SAVE_GAME):
            try:
                os.remove(ARQUIVO_SAVE_GAME)
            except OSError as e:
                print(f"Erro ao remover save antigo: {e}")
        
        self.__nave = Nave(Vetor2D(LARGURA_TELA / 2, ALTURA_TELA / 2))
        self.__asteroides, self.__projeteis, self.__ovnis, self.__ovni_projeteis, self.__fantasmas, self.__lasers_fantasma = [], [], [], [], [], []
        self.__pontuacao, self.__vidas, self.__game_over, self.__nivel_atual = 0, VIDAS_INICIAIS, False, 0
        self._spawn_asteroides_nivel()
        
        tempo_final_inv = pygame.time.get_ticks() + (TEMPO_INVENCIBILIDADE_SEGUNDOS * 1000)
        if self.__nave:
            self.__nave.set_invulneravel_fim(tempo_final_inv)

    def _spawn_asteroides_nivel(self):
        """
        Cria uma nova leva de asteroides para o nível atual.
        """
        num_asteroides = ASTEROIDES_INICIAIS + self.__nivel_atual * 2
        for _ in range(num_asteroides):
            while True:
                pos = Vetor2D(random.randint(0, LARGURA_TELA), random.randint(0, ALTURA_TELA))
                if self.__nave and pos.distancia_ate(self.__nave.get_posicao()) > self.__nave.get_raio() * 7:
                    self.__asteroides.append(Asteroide(pos, "grande"))
                    break
    
    def _verificar_proximo_nivel(self):
        """
        Verifica se as condições para avançar de nível foram atendidas.
        """
        if self.__game_over or not self.__nave or not self.__nave.is_ativo():
            return
        if not self.__asteroides and not self.__ovnis:
            self.__nivel_atual += 1
            self.__pontuacao += 1000 * self.__nivel_atual
            self.__nave.ativar_tiro_triplo(DURACAO_TIRO_TRIPLO_SEGUNDOS)
            pygame.time.wait(1000)
            self._spawn_asteroides_nivel()
            self.__nave.set_posicao(Vetor2D(LARGURA_TELA / 2, ALTURA_TELA / 2))
            self.__nave.set_velocidade(Vetor2D(0, 0))

    def _processar_input_jogo(self):
        """
        Processa inputs contínuos (teclas pressionadas) para movimento da nave.
        """
        if not self.__nave or not self.__nave.is_ativo() or self.__game_over or self.__jogo_pausado:
            return
        teclas = pygame.key.get_pressed()
        self.__nave.set_rotacao('esquerda', teclas[pygame.K_a] or teclas[pygame.K_LEFT])
        self.__nave.set_rotacao('direita', teclas[pygame.K_d] or teclas[pygame.K_RIGHT])
        self.__nave.set_acelerando(teclas[pygame.K_w] or teclas[pygame.K_UP])


    def _atualizar_objetos(self, delta_tempo: float):
        self.__fundo_estrelado.atualizar(delta_tempo)
        
        # 1. Atualiza todas as entidades, EXCETO a NaveFantasma
        entidades_gerais = [self.__nave] + self.__asteroides + self.__projeteis + self.__ovnis + self.__ovni_projeteis + self.__lasers_fantasma
        for entidade in filter(None, entidades_gerais):
            entidade.atualizar(delta_tempo)

        # 2. Atualiza a NaveFantasma de forma separada, passando o alvo
        alvo_jogador = self.__nave.get_posicao() if self.__nave and self.__nave.is_ativo() else None
        
        for fantasma in self.__fantasmas:
            laser = fantasma.atualizar(delta_tempo, alvo_jogador)
            if laser:
                self.__lasers_fantasma.append(laser)
        
        # Lógica de tiro dos OVNIs
        if alvo_jogador:
            for ovni in self.__ovnis:
                if ovni.is_ativo():
                    novos_tiros = ovni.tentar_atirar(alvo_jogador)
                    if novos_tiros: self.__ovni_projeteis.extend(novos_tiros)
        
        # Lógica de SPAWN
        if not self.__fantasmas and random.random() < CHANCE_SPAWN_FANTASMA:
            self.__fantasmas.append(NaveFantasma())
            
        if random.random() < CHANCE_SPAWN_OVNI_X and len(self.__ovnis) < MAX_OVNIS_TELA:
            self.__ovnis.append(OvniX())
            
        if random.random() < CHANCE_SPAWN_OVNI_CRUZ and len(self.__ovnis) < MAX_OVNIS_TELA:
            self.__ovnis.append(OvniCruz())

        # Limpeza de objetos inativos
        self.__projeteis = [p for p in self.__projeteis if p.is_ativo()]
        self.__ovni_projeteis = [p for p in self.__ovni_projeteis if p.is_ativo()]
        self.__lasers_fantasma = [l for l in self.__lasers_fantasma if l.is_ativo()]
        self.__asteroides = [a for a in self.__asteroides if a.is_ativo()]
        self.__ovnis = [o for o in self.__ovnis if o.is_ativo()]
        self.__fantasmas = [f for f in self.__fantasmas if f.is_ativo() or f.get_estado() == EstadoFantasma.INVISIVEL]
    
    def _checar_colisoes(self):
        """
        Verifica e processa todas as colisões entre os objetos do jogo.
        """
        if not self.__nave: return

        # Colisão dos projéteis do jogador
        for p in list(self.__projeteis):
            if not p.is_ativo(): continue
            for a in list(self.__asteroides):
                if a.is_ativo() and p.colide_com(a):
                    p.set_ativo(False); self.__pontuacao += a.get_pontos(); self.__asteroides.extend(a.dividir()); break
            for o in list(self.__ovnis):
                if p.is_ativo() and o.is_ativo() and p.colide_com(o):
                    p.set_ativo(False); o.set_ativo(False); self.__pontuacao += PONTOS_OVNI; break
            for f in list(self.__fantasmas):
                if p.is_ativo() and f.is_ativo() and p.colide_com(f):
                    p.set_ativo(False); f.set_ativo(False); self.__pontuacao += PONTOS_FANTASMA; break
        
        # Colisão da nave do jogador
        if self.__nave.is_invulneravel() or not self.__nave.is_ativo():
            return

        for inimigo in self.__asteroides + self.__ovnis + self.__ovni_projeteis + self.__lasers_fantasma:
            if inimigo.is_ativo() and self.__nave.colide_com(inimigo):
                if isinstance(inimigo, Asteroide): self.__asteroides.extend(inimigo.dividir())
                inimigo.set_ativo(False)
                self._nave_destruida()
                return

    def _nave_destruida(self):
        """
        Lida com a destruição da nave do jogador.
        """
        if not self.__nave or self.__nave.is_invulneravel(): return
        self.__gerenciador_som.tocar_som('explosao_nave')
        self.__nave.set_ativo(False)
        self.__vidas -= 1
        if self.__vidas < 0:
            self.__game_over = True
        else:
            self.__tempo_para_respawn = pygame.time.get_ticks() + 2000

    def _respawn_nave_se_necessario(self):
        """
        Verifica se a nave deve reaparecer após ser destruída.
        """
        if self.__nave and not self.__nave.is_ativo() and self.__vidas >= 0 and self.__tempo_para_respawn > 0 and pygame.time.get_ticks() >= self.__tempo_para_respawn:
            self.__nave.set_posicao(Vetor2D(LARGURA_TELA/2, ALTURA_TELA/2))
            self.__nave.set_velocidade(Vetor2D(0,0))
            self.__nave.set_angulo(0)
            self.__nave.set_ativo(True)
            tempo_final = pygame.time.get_ticks() + (TEMPO_INVENCIBILIDADE_SEGUNDOS * 1000)
            self.__nave.set_invulneravel_fim(tempo_final)
            self.__tempo_para_respawn = 0

    def _desenhar_hud(self):
        """
        Desenha as informações na tela, como pontuação e vidas.
        """
        self.__tela.blit(self.__fonte_hud.render(f"Pontos: {self.__pontuacao}", True, BRANCO), (10, 10))
        for i in range(self.__vidas):
            p1 = (LARGURA_TELA - 30 - i * 25, 17)
            p2 = (LARGURA_TELA - 30 - i * 25 - 8 * 0.6, 17 + 8 * 1.6)
            p3 = (LARGURA_TELA - 30 - i * 25 + 8 * 0.6, 17 + 8 * 1.6)
            pygame.draw.polygon(self.__tela, VERDE, [p1, p2, p3], 1)

    def _desenhar_tela_game_over(self):
        """
        Desenha a tela de "Fim de Jogo".
        """
        texto_go = self.__fonte_game_over.render("GAME OVER", True, VERMELHO)
        self.__tela.blit(texto_go, texto_go.get_rect(center=(LARGURA_TELA//2, ALTURA_TELA//2 - 50)))
        texto_pont = self.__fonte_hud.render(f"Pontuação Final: {self.__pontuacao}", True, BRANCO)
        self.__tela.blit(texto_pont, texto_pont.get_rect(center=(LARGURA_TELA//2, ALTURA_TELA//2 + 20)))

    def _mostrar_menu_pausa(self):
        """
        Mostra o menu de pausa e gerencia suas interações.
        """
        self.__jogo_pausado = True
        # ... (A implementação do menu de pausa pode ser adicionada aqui se necessário) ...
        self.__jogo_pausado = False # Simplificado por enquanto

    def salvar_estado_jogo(self):
        """
        Salva o estado atual do jogo em um arquivo JSON.
        """
        if self.__game_over:
            if os.path.exists(ARQUIVO_SAVE_GAME):
                try: os.remove(ARQUIVO_SAVE_GAME)
                except OSError: pass
            return
            
        estado = {
            "pontuacao": self.__pontuacao, "vidas": self.__vidas, "nivel_atual": self.__nivel_atual, "game_over": self.__game_over,
            "nave": self.__nave.to_dict() if self.__nave else None,
            "asteroides": [a.to_dict() for a in self.__asteroides],
            "projeteis": [p.to_dict() for p in self.__projeteis],
            "ovnis": [o.to_dict() for o in self.__ovnis],
            "ovni_projeteis": [op.to_dict() for op in self.__ovni_projeteis],
            "fantasmas": [f.to_dict() for f in self.__fantasmas],
            "lasers_fantasma": [l.to_dict() for l in self.__lasers_fantasma],
        }
        try:
            with open(ARQUIVO_SAVE_GAME, "w") as f:
                json.dump(estado, f, indent=4)
            print("Estado do jogo salvo com sucesso.")
        except Exception as e:
            print(f"Erro ao salvar o estado do jogo: {e}")

    def carregar_estado_jogo(self) -> bool:
        """
        Carrega o estado do jogo a partir de um arquivo JSON.
        """
        if not os.path.exists(ARQUIVO_SAVE_GAME): return False
        try:
            with open(ARQUIVO_SAVE_GAME, "r") as f: data = json.load(f)
            if data.get("game_over") or not data.get("nave"): return False

            self.__pontuacao, self.__vidas, self.__nivel_atual, self.__game_over = data["pontuacao"], data["vidas"], data["nivel_atual"], data["game_over"]
            
            self.__nave = CLASSE_MAP["Nave"].from_dict(data["nave"])
            self.__asteroides = [CLASSE_MAP[a["classe_tipo"]].from_dict(a) for a in data.get("asteroides", [])]
            self.__projeteis = [CLASSE_MAP[p["classe_tipo"]].from_dict(p) for p in data.get("projeteis", [])]
            self.__ovnis = [CLASSE_MAP[o["classe_tipo"]].from_dict(o) for o in data.get("ovnis", [])]
            self.__ovni_projeteis = [CLASSE_MAP[op["classe_tipo"]].from_dict(op) for op in data.get("ovni_projeteis", [])]
            self.__fantasmas = [CLASSE_MAP[f["classe_tipo"]].from_dict(f) for f in data.get("fantasmas", [])]
            self.__lasers_fantasma = [CLASSE_MAP[l["classe_tipo"]].from_dict(l) for l in data.get("lasers_fantasma", [])]
            
            print("Estado do jogo carregado com sucesso."); return True
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Erro ao carregar o estado do jogo: {e}"); return False

    def loop_principal(self) -> tuple[EstadoJogoLoop, int]:
        """
        O loop principal que roda o jogo quadro a quadro.
        """
        while True:
            delta_tempo = self.__clock.tick(FPS) / 1000.0
            
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.salvar_estado_jogo()
                    return EstadoJogoLoop.VOLTAR_AO_MENU_COM_SAVE, self.__pontuacao
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        self.salvar_estado_jogo() # Salva ao pausar e sair
                        return EstadoJogoLoop.VOLTAR_AO_MENU_COM_SAVE, self.__pontuacao
                    if evento.key == pygame.K_SPACE and self.__nave and self.__nave.is_ativo() and not self.__jogo_pausado:
                        tiros = self.__nave.atirar()
                        if tiros:
                            self.__gerenciador_som.tocar_som('tiro')
                            self.__projeteis.extend(tiros)
            
            self._processar_input_jogo()
            
            if not self.__game_over:
                self._respawn_nave_se_necessario()
                self._atualizar_objetos(delta_tempo)
                self._checar_colisoes()
                self._verificar_proximo_nivel()
            
            self.__tela.fill(PRETO)
            self.__fundo_estrelado.desenhar(self.__tela)
            
            todas_entidades_desenhaveis = [self.__nave] + self.__asteroides + self.__projeteis + self.__ovnis + self.__ovni_projeteis + self.__fantasmas + self.__lasers_fantasma
            for entidade in filter(None, todas_entidades_desenhaveis):
                entidade.desenhar(self.__tela)
            
            self._desenhar_hud()
            if self.__game_over:
                self._desenhar_tela_game_over()
            
            pygame.display.flip()