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

    def get_pontuacao(self) -> int:
        return self.__pontuacao

    def set_pontuacao(self, nova_pontuacao: int):
        self.__pontuacao = nova_pontuacao

    def get_vidas(self) -> int:
        return self.__vidas

    def set_vidas(self, novas_vidas: int):
        self.__vidas = novas_vidas

    def is_game_over(self) -> bool:
        return self.__game_over

    def set_game_over(self, estado: bool):
        self.__game_over = estado

    def reiniciar_jogo_completo(self):
        if os.path.exists(ARQUIVO_SAVE_GAME):
            try: os.remove(ARQUIVO_SAVE_GAME)
            except OSError as e: print(f"Erro ao remover save antigo: {e}")
        
        self.__nave = Nave(Vetor2D(LARGURA_TELA / 2, ALTURA_TELA / 2))
        self.__asteroides, self.__projeteis, self.__ovnis, self.__ovni_projeteis, self.__fantasmas, self.__lasers_fantasma = [], [], [], [], [], []
        
        self.set_pontuacao(0)
        self.set_vidas(VIDAS_INICIAIS)
        self.set_game_over(False)
        self.__nivel_atual = 0
        
        self._spawn_asteroides_nivel()
        
        tempo_final_inv = pygame.time.get_ticks() + (TEMPO_INVENCIBILIDADE_SEGUNDOS * 1000)
        if self.__nave:
            self.__nave.set_invulneravel_fim(tempo_final_inv)

    def _spawn_asteroides_nivel(self):
        num_asteroides = ASTEROIDES_INICIAIS + self.__nivel_atual * 2
        for _ in range(num_asteroides):
            while True:
                pos = Vetor2D(random.randint(0, LARGURA_TELA), random.randint(0, ALTURA_TELA))
                if self.__nave and pos.distancia_ate(self.__nave.get_posicao()) > self.__nave.get_raio() * 7:
                    self.__asteroides.append(Asteroide(pos, "grande"))
                    break

    
    def _verificar_proximo_nivel(self):
        if self.is_game_over() or not self.__nave or not self.__nave.is_ativo(): return
        if not self.__asteroides and not self.__ovnis:
            self.__nivel_atual += 1
            self.set_pontuacao(self.get_pontuacao() + 1000 * self.__nivel_atual)
            self.__nave.ativar_tiro_triplo(DURACAO_TIRO_TRIPLO_SEGUNDOS)
            pygame.time.wait(1000)
            self._spawn_asteroides_nivel()
            self.__nave.set_posicao(Vetor2D(LARGURA_TELA / 2, ALTURA_TELA / 2))
            self.__nave.set_velocidade(Vetor2D(0, 0))

    def _processar_input_jogo(self):
        if not self.__nave or not self.__nave.is_ativo() or self.is_game_over() or self.__jogo_pausado: return
        teclas = pygame.key.get_pressed()
        self.__nave.set_rotacao('esquerda', teclas[pygame.K_a] or teclas[pygame.K_LEFT])
        self.__nave.set_rotacao('direita', teclas[pygame.K_d] or teclas[pygame.K_RIGHT])
        self.__nave.set_acelerando(teclas[pygame.K_w] or teclas[pygame.K_UP])


    def _atualizar_objetos(self, delta_tempo: float):
        self.__fundo_estrelado.atualizar(delta_tempo)
        todas_entidades = [self.__nave] + self.__asteroides + self.__projeteis + self.__ovnis + self.__ovni_projeteis + self.__fantasmas + self.__lasers_fantasma
        for entidade in filter(None, todas_entidades): entidade.atualizar(delta_tempo)
        alvo_jogador = self.__nave.get_posicao() if self.__nave and self.__nave.is_ativo() else None
        if alvo_jogador:
            for ovni in self.__ovnis:
                if ovni.is_ativo(): self.__ovni_projeteis.extend(ovni.tentar_atirar(alvo_jogador))
        for fantasma in self.__fantasmas:
            laser = fantasma.atualizar(delta_tempo, alvo_jogador)
            if laser: self.__lasers_fantasma.append(laser)
        if not self.__fantasmas and random.random() < CHANCE_SPAWN_FANTASMA: self.__fantasmas.append(NaveFantasma())
        if random.random() < CHANCE_SPAWN_OVNI_X and len(self.__ovnis) < MAX_OVNIS_TELA: self.__ovnis.append(OvniX())
        if random.random() < CHANCE_SPAWN_OVNI_CRUZ and len(self.__ovnis) < MAX_OVNIS_TELA: self.__ovnis.append(OvniCruz())
        self.__projeteis[:] = [p for p in self.__projeteis if p.is_ativo()]
        self.__ovni_projeteis[:] = [p for p in self.__ovni_projeteis if p.is_ativo()]
        self.__lasers_fantasma[:] = [l for l in self.__lasers_fantasma if l.is_ativo()]
        self.__asteroides[:] = [a for a in self.__asteroides if a.is_ativo()]
        self.__ovnis[:] = [o for o in self.__ovnis if o.is_ativo()]
        self.__fantasmas[:] = [f for f in self.__fantasmas if f.is_ativo() or f.get_estado() == EstadoFantasma.INVISIVEL]
    
    def _checar_colisoes(self):
        if not self.__nave: return

        # --- Colisão dos projéteis do jogador com inimigos ---
        novos_asteroides_frag = []
        for p in list(self.__projeteis):
            if not p.is_ativo(): continue
            
            # Com asteroides
            for a in list(self.__asteroides):
                if a.is_ativo() and p.colide_com(a):
                    p.set_ativo(False)
                    self.set_pontuacao(self.get_pontuacao() + a.get_pontos())
                    novos_asteroides_frag.extend(a.dividir())
                    break 
            
            # Com OVNIs e Fantasmas
            for o in list(self.__ovnis):
                if p.is_ativo() and o.is_ativo() and p.colide_com(o):
                    p.set_ativo(False); o.set_ativo(False); self.set_pontuacao(self.get_pontuacao() + PONTOS_OVNI); break
            for f in list(self.__fantasmas):
                if p.is_ativo() and f.is_ativo() and p.colide_com(f):
                    p.set_ativo(False); f.set_ativo(False); self.set_pontuacao(self.get_pontuacao() + PONTOS_FANTASMA); break
        
        self.__asteroides.extend(novos_asteroides_frag)
        
        # --- Colisão da nave do jogador com perigos ---
        if not self.__nave.is_invulneravel() and self.__nave.is_ativo():
            todos_os_perigos = self.__asteroides + self.__ovnis + self.__ovni_projeteis + self.__lasers_fantasma
            for inimigo in todos_os_perigos:
                if inimigo.is_ativo() and self.__nave.colide_com(inimigo):
                    if isinstance(inimigo, Asteroide):
                        self.__asteroides.extend(inimigo.dividir())
                    inimigo.set_ativo(False)
                    self._nave_destruida()
                    return

        # --- LÓGICA DE COLISÃO ENTRE ASTEROIDES ---
        for i, ast1 in enumerate(self.__asteroides):
            for j in range(i + 1, len(self.__asteroides)):
                ast2 = self.__asteroides[j]

                if ast1.is_ativo() and ast2.is_ativo() and ast1.colide_com(ast2):
                    
                    v1 = ast1.get_velocidade()
                    v2 = ast2.get_velocidade()
                    ast1.set_velocidade(v2)
                    ast2.set_velocidade(v1)

                    dist_vetor = ast1.get_posicao() - ast2.get_posicao()
                    dist = dist_vetor.magnitude()
                    if dist == 0: continue
                    
                    sobreposicao = (ast1.get_raio() + ast2.get_raio()) - dist
                    if sobreposicao > 0:
                        deslocamento = dist_vetor.normalizar() * (sobreposicao / 2)
                        ast1.set_posicao(ast1.get_posicao() + deslocamento)
                        ast2.set_posicao(ast2.get_posicao() - deslocamento)

    def _nave_destruida(self):
        if not self.__nave or self.__nave.is_invulneravel(): return
        self.__gerenciador_som.tocar_som('explosao_nave')
        self.__nave.set_ativo(False)
        self.set_vidas(self.get_vidas() - 1)
        if self.get_vidas() < 0: self.set_game_over(True)
        else: self.__tempo_para_respawn = pygame.time.get_ticks() + 2000

    def _respawn_nave_se_necessario(self):
        if self.__nave and not self.__nave.is_ativo() and self.get_vidas() >= 0 and self.__tempo_para_respawn > 0 and pygame.time.get_ticks() >= self.__tempo_para_respawn:
            self.__nave.set_posicao(Vetor2D(LARGURA_TELA/2, ALTURA_TELA/2))
            self.__nave.set_velocidade(Vetor2D(0,0))
            self.__nave.set_angulo(0)
            self.__nave.set_ativo(True)
            tempo_final = pygame.time.get_ticks() + (TEMPO_INVENCIBILIDADE_SEGUNDOS * 1000)
            self.__nave.set_invulneravel_fim(tempo_final)
            self.__tempo_para_respawn = 0

    def _desenhar_hud(self):
        self.__tela.blit(self.__fonte_hud.render(f"Pontos: {self.get_pontuacao()}", True, BRANCO), (10, 10))
        for i in range(self.get_vidas()):
            p1 = (LARGURA_TELA - 30 - i * 25, 17)
            p2 = (LARGURA_TELA - 30 - i * 25 - 8 * 0.6, 17 + 8 * 1.6)
            p3 = (LARGURA_TELA - 30 - i * 25 + 8 * 0.6, 17 + 8 * 1.6)
            pygame.draw.polygon(self.__tela, VERDE, [p1, p2, p3], 1)

    def _desenhar_tela_game_over(self):
        texto_go = self.__fonte_game_over.render("GAME OVER", True, VERMELHO)
        self.__tela.blit(texto_go, texto_go.get_rect(center=(LARGURA_TELA//2, ALTURA_TELA//2 - 50)))
        texto_pont = self.__fonte_hud.render(f"Pontuação Final: {self.get_pontuacao()}", True, BRANCO)
        self.__tela.blit(texto_pont, texto_pont.get_rect(center=(LARGURA_TELA//2, ALTURA_TELA//2 + 20)))

    def _set_acao_pausa(self, acao: EstadoJogoLoop):
        if acao == EstadoJogoLoop.VOLTAR_AO_MENU_COM_SAVE: self.salvar_estado_jogo()
        self.__acao_menu_pausa = acao
        self.__jogo_pausado = False



    def _mostrar_menu_pausa(self):
        self.__jogo_pausado = True; self.__acao_menu_pausa = None
        tema_pausa = pygame_menu.themes.THEME_DARK.copy(); tema_pausa.background_color = (0, 0, 0, 180)
        menu_pausa = pygame_menu.Menu(title="JOGO PAUSADO", width=600, height=400, theme=tema_pausa)
        menu_pausa.set_onclose(lambda: self._set_acao_pausa(EstadoJogoLoop.CONTINUAR_JOGO))
        def acao_wrapper(acao: EstadoJogoLoop): self._set_acao_pausa(acao); menu_pausa.disable()
        menu_pausa.add.button('Retornar ao Jogo', lambda: acao_wrapper(EstadoJogoLoop.CONTINUAR_JOGO))
        menu_pausa.add.button('Salvar e Sair', lambda: acao_wrapper(EstadoJogoLoop.VOLTAR_AO_MENU_COM_SAVE))
        menu_pausa.add.button('Sair sem Salvar', lambda: acao_wrapper(EstadoJogoLoop.VOLTAR_AO_MENU_SEM_SALVAR))
        menu_pausa.mainloop(self.__tela)
        self.__jogo_pausado = False

    def salvar_estado_jogo(self):
        if self.is_game_over():
            if os.path.exists(ARQUIVO_SAVE_GAME):
                try: os.remove(ARQUIVO_SAVE_GAME)
                except OSError: pass
            return
        estado = {"pontuacao": self.get_pontuacao(), 
                  "vidas": self.get_vidas(), 
                  "nivel_atual": self.__nivel_atual, 
                  "game_over": self.is_game_over(), 
                  "nave": self.__nave.to_dict() if self.__nave else None, 
                  "asteroides": [a.to_dict() for a in self.__asteroides], 
                  "projeteis": [p.to_dict() for p in self.__projeteis], 
                  "ovnis": [o.to_dict() for o in self.__ovnis], 
                  "ovni_projeteis": [op.to_dict() for op in self.__ovni_projeteis], 
                  "fantasmas": [f.to_dict() for f in self.__fantasmas], 
                  "lasers_fantasma": [l.to_dict() for l in self.__lasers_fantasma],}
        try:
            with open(ARQUIVO_SAVE_GAME, "w") as f: json.dump(estado, f, indent=4)
            print("Estado do jogo salvo com sucesso.")
        except Exception as e: print(f"Erro ao salvar o estado do jogo: {e}")

    def carregar_estado_jogo(self) -> bool:
        if not os.path.exists(ARQUIVO_SAVE_GAME): return False
        try:
            with open(ARQUIVO_SAVE_GAME, "r") as f: data = json.load(f)
            if data.get("game_over") or not data.get("nave"): return False
            self.set_pontuacao(data["pontuacao"]); self.set_vidas(data["vidas"]); self.__nivel_atual = data["nivel_atual"]; self.set_game_over(data["game_over"])
            self.__nave = CLASSE_MAP["Nave"].from_dict(data["nave"])
            self.__asteroides = [CLASSE_MAP[a["classe_tipo"]].from_dict(a) for a in data.get("asteroides", [])]
            self.__projeteis = [CLASSE_MAP[p["classe_tipo"]].from_dict(p) for p in data.get("projeteis", [])]
            self.__ovnis = [CLASSE_MAP[o["classe_tipo"]].from_dict(o) for o in data.get("ovnis", [])]
            self.__ovni_projeteis = [CLASSE_MAP[op["classe_tipo"]].from_dict(op) for op in data.get("ovni_projeteis", [])]
            self.__fantasmas = [CLASSE_MAP[f["classe_tipo"]].from_dict(f) for f in data.get("fantasmas", [])]
            self.__lasers_fantasma = [CLASSE_MAP[l["classe_tipo"]].from_dict(l) for l in data.get("lasers_fantasma", [])]
            print("Estado do jogo carregado com sucesso."); return True
        except Exception as e: print(f"Erro ao carregar o estado do jogo: {e}"); return False

    def loop_principal(self) -> tuple[EstadoJogoLoop, int]:
        self.__jogo_pausado = False
        while True:
            delta_tempo = self.__clock.tick(FPS) / 1000.0
            eventos = pygame.event.get() if not self.__jogo_pausado else []
            for evento in eventos:
                if evento.type == pygame.QUIT: return EstadoJogoLoop.VOLTAR_AO_MENU_SEM_SALVAR, self.get_pontuacao()
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        if self.is_game_over(): return EstadoJogoLoop.VOLTAR_AO_MENU_GAME_OVER, self.get_pontuacao()
                        self._mostrar_menu_pausa()
                        if self.__acao_menu_pausa != EstadoJogoLoop.CONTINUAR_JOGO: return self.__acao_menu_pausa, self.get_pontuacao()
                    if evento.key == pygame.K_SPACE and self.__nave and self.__nave.is_ativo() and not self.__jogo_pausado:
                        tiros = self.__nave.atirar()
                        if tiros: self.__gerenciador_som.tocar_som('tiro'); self.__projeteis.extend(tiros)
            
            self._processar_input_jogo()
            if not self.is_game_over():
                self._respawn_nave_se_necessario(); self._atualizar_objetos(delta_tempo); self._checar_colisoes(); self._verificar_proximo_nivel()
            
            self.__tela.fill(PRETO)
            self.__fundo_estrelado.desenhar(self.__tela)
            todas_entidades = [self.__nave] + self.__asteroides + self.__projeteis + self.__ovnis + self.__ovni_projeteis + self.__fantasmas + self.__lasers_fantasma
            for entidade in filter(None, todas_entidades): entidade.desenhar(self.__tela)
            self._desenhar_hud()
            if self.is_game_over():
                self._desenhar_tela_game_over(); pygame.display.flip(); pygame.time.wait(3000)
                return EstadoJogoLoop.VOLTAR_AO_MENU_GAME_OVER, self.get_pontuacao()
            
            pygame.display.flip()