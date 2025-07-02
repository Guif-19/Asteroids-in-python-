import pygame
import pygame_menu
import os
import json
import random   
from enum import Enum, auto
from config import *
from entidade import *
from vetor import Vetor2D


class EstadoJogoLoop(Enum):
    CONTINUAR_JOGO = 0
    VOLTAR_AO_MENU_SEM_SALVAR = 1
    VOLTAR_AO_MENU_COM_SAVE = 2
    VOLTAR_AO_MENU_GAME_OVER = 3


class FundoEstrelado:
    def __init__(self):
        self.estrelas_lentas = [[random.randrange(LARGURA_TELA), random.randrange(ALTURA_TELA), 1] for _ in range(NUM_ESTRELAS_LENTAS)]
        self.estrelas_rapidas = [[random.randrange(LARGURA_TELA), random.randrange(ALTURA_TELA), 2] for _ in range(NUM_ESTRELAS_RAPIDAS)]

    def atualizar(self, delta_tempo: float):
        for estrela in self.estrelas_lentas:
            estrela[1] = (estrela[1] + VELOCIDADE_ESTRELAS_LENTA * delta_tempo * FPS) % ALTURA_TELA
            if estrela[1] < VELOCIDADE_ESTRELAS_LENTA:
                estrela[0] = random.randrange(LARGURA_TELA)

        for estrela in self.estrelas_rapidas:
            estrela[1] = (estrela[1] + VELOCIDADE_ESTRELAS_RAPIDA * delta_tempo * FPS) % ALTURA_TELA
            if estrela[1] < VELOCIDADE_ESTRELAS_RAPIDA:
                estrela[0] = random.randrange(LARGURA_TELA)

    def desenhar(self, tela: pygame.Surface):
        for x, y, tamanho in self.estrelas_lentas:
            pygame.draw.circle(tela, (150, 150, 150), (int(x), int(y)), max(1, tamanho // 2))
        for x, y, tamanho in self.estrelas_rapidas:
            pygame.draw.circle(tela, COR_ESTRELA, (int(x), int(y)), tamanho)


class GerenciadorJogo:
    def __init__(self, tela: pygame.Surface, clock: pygame.time.Clock, gerenciador_som):
        self.tela = tela
        self.clock = clock
        self.gerenciador_som = gerenciador_som
        self.nave = None
        self.asteroides = []
        self.projeteis = []
        self.ovnis = []
        self.ovni_projeteis = []
        self.fantasmas = []
        self.lasers_fantasma = []
        self.fundo_estrelado = FundoEstrelado()
        self.pontuacao = 0
        self.vidas = VIDAS_INICIAIS
        self.game_over = False
        self.nivel_atual = 0
        self.fonte_hud = pygame.font.Font(None, 36)
        self.fonte_game_over = pygame.font.Font(None, 72)
        self.fonte_pausa = pygame.font.Font(None, 50)
        self.menu_pausa_obj = None
        self.jogo_pausado = False
        self.acao_menu_pausa = None
        self.tempo_para_respawn = 0


    def reiniciar_jogo_completo(self):
        try:
            if os.path.exists(ARQUIVO_SAVE_GAME):
                os.remove(ARQUIVO_SAVE_GAME)
        except Exception as e:
            print(f"Aviso: não foi possível remover o save antigo: {e}")
        self.nave = Nave(Vetor2D(LARGURA_TELA / 2, ALTURA_TELA / 2))
        self.asteroides.clear(); self.projeteis.clear(); self.ovnis.clear()
        self.ovni_projeteis.clear(); self.fantasmas.clear(); self.lasers_fantasma.clear()
        self.pontuacao = 0
        self.vidas = VIDAS_INICIAIS
        self.game_over = False
        self.nivel_atual = 0
        self._spawn_asteroides_nivel()

    def _verificar_proximo_nivel(self):
        if self.game_over or not self.nave or not self.nave.is_ativo():
            return

        if not self.asteroides:
            self.nivel_atual += 1
            self.pontuacao += 1000 * self.nivel_atual
            print(f"Nível {self.nivel_atual} iniciado.")
            self.nave.ativar_tiro_triplo(DURACAO_TIRO_TRIPLO_SEGUNDOS)
            pygame.time.wait(1000)
            self._spawn_asteroides_nivel()
            self.nave.set_posicao(Vetor2D(LARGURA_TELA / 2, ALTURA_TELA / 2))
            self.nave.set_velocidade(Vetor2D(0, 0))

    def _spawn_asteroides_nivel(self):
        num_asteroides = ASTEROIDES_INICIAIS + self.nivel_atual * 2
        for _ in range(num_asteroides):
            while True:
                pos_x = random.randint(0, LARGURA_TELA)
                pos_y = random.randint(0, ALTURA_TELA)
                pos_candidata = Vetor2D(pos_x, pos_y)
                if not self.nave or (pos_candidata - self.nave.get_posicao()).magnitude() > self.nave.get_raio() * 7:
                    self.asteroides.append(Asteroide(pos_candidata, "grande"))
                    break

    def _processar_input_jogo(self):
        if not self.nave or not self.nave.is_ativo() or self.game_over or self.jogo_pausado:
            return

        teclas = pygame.key.get_pressed()
        self.nave.rotacionando_esquerda = teclas[pygame.K_a] or teclas[pygame.K_LEFT]
        self.nave.rotacionando_direita = teclas[pygame.K_d] or teclas[pygame.K_RIGHT]
        self.nave.acelerando = teclas[pygame.K_w] or teclas[pygame.K_UP]

    def _atualizar_objetos(self, delta_tempo: float):
        self.fundo_estrelado.atualizar(delta_tempo)
        if self.nave and self.nave.is_ativo(): self.nave.atualizar(delta_tempo)

        for lista in [self.asteroides, self.projeteis, self.ovnis, self.ovni_projeteis, self.lasers_fantasma]:
            for item in lista: item.atualizar(delta_tempo)

        if self.nave and self.nave.is_ativo():
            for ovni in self.ovnis:
                if ovni.is_ativo():
                    novos_tiros = ovni.tentar_atirar(self.nave.get_posicao())
                    if novos_tiros: self.gerenciador_som.tocar_som('ovni_tiro'); self.ovni_projeteis.extend(novos_tiros)
            
            for fantasma in self.fantasmas:
                estado_anterior = fantasma.get_estado()
                laser = fantasma.atualizar(delta_tempo, self.nave.get_posicao())
                if laser: self.lasers_fantasma.append(laser)
                if fantasma.get_estado() == EstadoFantasma.INVISIVEL and estado_anterior != EstadoFantasma.INVISIVEL:
                    self.gerenciador_som.parar_som('fantasma_invisivel')
                elif fantasma.get_estado() == EstadoFantasma.CARREGANDO and estado_anterior == EstadoFantasma.INVISIVEL:
                    self.gerenciador_som.tocar_som('fantasma_invisivel', loop=-1)

        if len(self.fantasmas) < MAX_FANTASMAS_TELA and random.random() < CHANCE_SPAWN_FANTASMA:
            if not any(f.get_estado() == EstadoFantasma.INVISIVEL for f in self.fantasmas):
                self.fantasmas.append(NaveFantasma())

        if random.random() < CHANCE_SPAWN_OVNI_X and len(self.ovnis) < MAX_OVNIS_TELA:
            self.ovnis.append(OvniX()); self.gerenciador_som.tocar_som('ovni_movendo', loop=-1)
        if random.random() < CHANCE_SPAWN_OVNI_CRUZ and len(self.ovnis) < MAX_OVNIS_TELA:
            self.ovnis.append(OvniCruz()); self.gerenciador_som.tocar_som('ovni_movendo', loop=-1)

        self.projeteis = [p for p in self.projeteis if p.is_ativo()]
        self.ovni_projeteis = [p for p in self.ovni_projeteis if p.is_ativo()]
        self.lasers_fantasma = [l for l in self.lasers_fantasma if l.is_ativo()]
        self.asteroides = [a for a in self.asteroides if a.is_ativo()]
        for ovni in list(self.ovnis):
            if not ovni.is_ativo(): self.gerenciador_som.parar_som('ovni_movendo'); self.ovnis.remove(ovni)
        self.fantasmas = [f for f in self.fantasmas if f.is_ativo() or f.get_estado() == EstadoFantasma.INVISIVEL]

    def _checar_colisoes(self):
        if not self.nave or not self.nave.is_ativo(): return
        novos_asteroides = []
        for p in list(self.projeteis):
            if not p.is_ativo(): continue
            for a in list(self.asteroides):
                if a.is_ativo() and p.colide_com(a): p.set_ativo(False); self.pontuacao += a.get_pontos(); novos_asteroides.extend(a.dividir()); self.gerenciador_som.tocar_som('explosao_asteroide'); break
            for o in list(self.ovnis):
                if p.is_ativo() and o.is_ativo() and p.colide_com(o): p.set_ativo(False); o.set_ativo(False); self.pontuacao += PONTOS_OVNI; self.gerenciador_som.parar_som('ovni_movendo'); break
            for f in list(self.fantasmas):
                 if p.is_ativo() and f.is_ativo() and p.colide_com(f): p.set_ativo(False); f.set_ativo(False); self.pontuacao += PONTOS_FANTASMA; print("DEBUG: Nave Fantasma destruída!"); self.gerenciador_som.parar_som('fantasma_invisivel'); break
        self.asteroides.extend(novos_asteroides)
        if not self.nave.is_ativo() or pygame.time.get_ticks() < self.nave.tempo_invulneravel_fim: return
        for proj_o in list(self.ovni_projeteis):
            if proj_o.is_ativo() and self.nave.colide_com(proj_o): proj_o.set_ativo(False); self._nave_destruida(); return
        for laser in self.lasers_fantasma:
            if laser.is_ativo() and laser.colide_com(self.nave): laser.set_ativo(False); self._nave_destruida(); return
        for a in list(self.asteroides):
            if a.is_ativo() and self.nave.colide_com(a): self._nave_destruida(); self.asteroides.extend(a.dividir()); return
        for o in list(self.ovnis):
            if o.is_ativo() and self.nave.colide_com(o): o.set_ativo(False); self.gerenciador_som.parar_som('ovni_movendo'); self._nave_destruida(); return
        for i, ast1 in enumerate(self.asteroides):
            if not ast1.is_ativo(): continue
            for j in range(i + 1, len(self.asteroides)):
                ast2 = self.asteroides[j];
                if not ast2.is_ativo(): continue
                if ast1.colide_com(ast2):
                    dist_vet = ast1.get_posicao() - ast2.get_posicao(); dist = dist_vet.magnitude()
                    if dist == 0: dist_vet, dist = Vetor2D(1, 0), 1
                    sobreposicao = (ast1.get_raio() + ast2.get_raio()) - dist
                    separacao = dist_vet.normalizar() * (sobreposicao / 2)
                    ast1.set_posicao(ast1.get_posicao() + separacao); ast2.set_posicao(ast2.get_posicao() - separacao)
                    v1, v2 = ast1.get_velocidade(), ast2.get_velocidade(); x1, x2 = ast1.get_posicao(), ast2.get_posicao()
                    dist_quad = (x1.distancia_ate(x2))**2
                    if dist_quad == 0: continue
                    fator = 2 * (v1 - v2).dot(x1 - x2) / dist_quad
                    nova_v1 = v1 - (x1 - x2) * fator; nova_v2 = v2 - (x2 - x1) * fator
                    if nova_v1.magnitude() > VEL_MAX_ASTEROIDE: nova_v1 = nova_v1.normalizar() * VEL_MAX_ASTEROIDE
                    if nova_v2.magnitude() > VEL_MAX_ASTEROIDE: nova_v2 = nova_v2.normalizar() * VEL_MAX_ASTEROIDE
                    ast1.set_velocidade(nova_v1); ast2.set_velocidade(nova_v2)

    def _nave_destruida(self):
        if not self.nave or not self.nave.is_ativo() or pygame.time.get_ticks() < self.nave.tempo_invulneravel_fim: return
        self.gerenciador_som.tocar_som('explosao_nave')
        self.nave.set_ativo(False)
        self.vidas -= 1
        self.nave.tem_tiro_triplo = False
        if self.vidas < 0: self.game_over = True
        else: self.tempo_para_respawn = pygame.time.get_ticks() + 1500

    def _respawn_nave_se_necessario(self):
        if self.nave and not self.nave.is_ativo() and self.tempo_para_respawn > 0 and pygame.time.get_ticks() >= self.tempo_para_respawn:
            print("DEBUG: Nave está respawnando (timer atingido).")
            self.nave.set_posicao(Vetor2D(LARGURA_TELA / 2, ALTURA_TELA / 2))
            self.nave.set_velocidade(Vetor2D(0, 0))
            self.nave.set_angulo(0)
            self.nave.set_ativo(True)
            self.tempo_para_respawn = 0
            self.nave.tempo_invulneravel_fim = pygame.time.get_ticks() + TEMPO_INVENCIBILIDADE_SEGUNDOS * 1000

    def _desenhar_hud(self):
        texto_pontuacao = self.fonte_hud.render(f"Pontuação: {self.pontuacao}", True, BRANCO)
        self.tela.blit(texto_pontuacao, (10, 10))
        raio_icone = 8
        for i in range(self.vidas):
            pos_x = LARGURA_TELA - 30 - i * 25; pos_y = 25
            p1 = (pos_x, pos_y - raio_icone)
            p2 = (pos_x - raio_icone * 0.6, pos_y + raio_icone * 0.6)
            p3 = (pos_x + raio_icone * 0.6, pos_y + raio_icone * 0.6)
            pygame.draw.polygon(self.tela, VERDE, [p1, p2, p3], 1)

    def _desenhar_tela_game_over(self):
        texto_go = self.fonte_game_over.render("GAME OVER", True, VERMELHO)
        rect_go = texto_go.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 2 - 50))
        self.tela.blit(texto_go, rect_go)
        texto_pont_final = self.fonte_hud.render(f"Pontuação Final: {self.pontuacao}", True, BRANCO)
        rect_pont_final = texto_pont_final.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 2 + 20))
        self.tela.blit(texto_pont_final, rect_pont_final)
        texto_instrucao = self.fonte_hud.render("Pressione ESC para voltar ao Menu", True, CINZA_CLARO)
        rect_instrucao = texto_instrucao.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 2 + 70))
        self.tela.blit(texto_instrucao, rect_instrucao)

    def salvar_estado_jogo(self):
        if self.game_over:
            try:
                if os.path.exists(ARQUIVO_SAVE_GAME): os.remove(ARQUIVO_SAVE_GAME)
            except OSError: pass
            return
        estado = {"nave": self.nave.to_dict() if self.nave else None, "asteroides": [a.to_dict() for a in self.asteroides], "projeteis": [p.to_dict() for p in self.projeteis], "ovnis": [o.to_dict() for o in self.ovnis], "ovni_projeteis": [op.to_dict() for op in self.ovni_projeteis], "fantasmas": [f.to_dict() for f in self.fantasmas], "lasers_fantasma": [l.to_dict() for l in self.lasers_fantasma], "pontuacao": self.pontuacao, "vidas": self.vidas, "nivel_atual": self.nivel_atual, "game_over": self.game_over}
        try:
            with open(ARQUIVO_SAVE_GAME, "w") as f: json.dump(estado, f, indent=4)
            print("Estado salvo.")
        except Exception as e: print(f"Erro ao salvar: {e}")
    def carregar_estado_jogo(self):
        try:
            if not os.path.exists(ARQUIVO_SAVE_GAME): self.reiniciar_jogo_completo(); return False
            with open(ARQUIVO_SAVE_GAME, "r") as f: data = json.load(f)
            if data.get("game_over", False) or not data.get("nave"): self.reiniciar_jogo_completo(); return False
            self.game_over = data.get("game_over", False); self.nivel_atual = data.get("nivel_atual", 0); self.pontuacao = data.get("pontuacao", 0); self.vidas = data.get("vidas", VIDAS_INICIAIS)
            self.nave = Nave.from_dict(data["nave"])
            self.asteroides = [Asteroide.from_dict(a) for a in data.get("asteroides", [])]
            self.projeteis = [Projetil.from_dict(p) for p in data.get("projeteis", [])]
            self.ovnis = [CLASSE_MAP[o["classe_tipo"]].from_dict(o) for o in data.get("ovnis", [])]
            self.ovni_projeteis = [OVNIProjetil.from_dict(op) for op in data.get("ovni_projeteis", [])]
            self.fantasmas = [NaveFantasma.from_dict(f) for f in data.get("fantasmas", [])]
            self.lasers_fantasma = [LaserFantasma.from_dict(l) for l in data.get("lasers_fantasma", [])]
            print("Estado do jogo carregado com sucesso."); return True
        except Exception as e:
            print(f"Erro crítico ao carregar estado do jogo: {e}"); import traceback; traceback.print_exc(); self.reiniciar_jogo_completo(); return False

    def _mostrar_menu_pausa(self):
        tema_pausa = pygame_menu.themes.THEME_DARK.copy()
        tema_pausa.background_color = (0, 0, 0, 180)
        menu = pygame_menu.Menu(title="JOGO PAUSADO", width=int(LARGURA_TELA * 0.5), height=int(ALTURA_TELA * 0.6), theme=tema_pausa)
        menu.add.button("Retornar ao Jogo", lambda: self._set_acao(EstadoJogoLoop.CONTINUAR_JOGO))
        menu.add.button("Salvar e Sair", lambda: self._set_acao(EstadoJogoLoop.VOLTAR_AO_MENU_COM_SAVE))
        menu.add.button("Sair sem Salvar", lambda: self._set_acao(EstadoJogoLoop.VOLTAR_AO_MENU_SEM_SALVAR))
        while self.jogo_pausado and self.acao_menu_pausa is None:
            eventos = pygame.event.get()
            for evento in eventos:
                if evento.type == pygame.QUIT: self._set_acao(EstadoJogoLoop.VOLTAR_AO_MENU_SEM_SALVAR); break
            if not self.jogo_pausado: break
            menu.update(eventos)
            menu.draw(self.tela)
            pygame.display.flip()
            self.clock.tick(FPS)

    def _set_acao(self, acao):
        if acao == EstadoJogoLoop.VOLTAR_AO_MENU_COM_SAVE: self.salvar_estado_jogo()
        self.acao_menu_pausa = acao
        self.jogo_pausado = False

    def loop_principal(self):
        print("DEBUG: Iniciando loop principal do jogo.")
        self.jogo_pausado = False
        self.acao_menu_pausa = None
        while True:
            delta_tempo = self.clock.tick(FPS) / 1000.0
            eventos = pygame.event.get()
            for evento in eventos:
                if evento.type == pygame.QUIT:
                    if not self.game_over: self.salvar_estado_jogo(); return EstadoJogoLoop.VOLTAR_AO_MENU_COM_SAVE, self.pontuacao
                    else: return EstadoJogoLoop.VOLTAR_AO_MENU_GAME_OVER, self.pontuacao
                elif evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        if self.game_over: return EstadoJogoLoop.VOLTAR_AO_MENU_GAME_OVER, self.pontuacao
                        else:
                            self.jogo_pausado = True
                            self._mostrar_menu_pausa()
                            if self.acao_menu_pausa != EstadoJogoLoop.CONTINUAR_JOGO: return self.acao_menu_pausa, self.pontuacao
                            self.acao_menu_pausa = None; self.jogo_pausado = False
                    elif evento.key == pygame.K_SPACE:
                        if self.nave and self.nave.is_ativo() and not self.jogo_pausado and not self.game_over:
                             novos_projeteis = self.nave.atirar()
                             if novos_projeteis: self.gerenciador_som.tocar_som('tiro'); self.projeteis.extend(novos_projeteis)
            if self.jogo_pausado: continue
            self._processar_input_jogo()
            if not self.game_over:
                self._respawn_nave_se_necessario()
                if self.nave and self.nave.is_ativo():
                    self._atualizar_objetos(delta_tempo); self._checar_colisoes(); self._verificar_proximo_nivel()
            self.tela.fill(PRETO); self.fundo_estrelado.desenhar(self.tela)
            if self.nave: self.nave.desenhar(self.tela)
            for obj in self.asteroides + self.projeteis + self.ovnis + self.ovni_projeteis + self.fantasmas + self.lasers_fantasma: obj.desenhar(self.tela)
            self._desenhar_hud()
            if self.game_over: self._desenhar_tela_game_over()
            pygame.display.flip()
