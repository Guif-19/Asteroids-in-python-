import pygame
import pygame_menu
import os
import json
import random
from enum import Enum, auto
from config import *
from entidades import *
from vetor import Vetor2D


class EstadoJogoLoop:
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
        self.asteroides.clear()
        self.projeteis.clear()
        self.ovnis.clear()
        self.ovni_projeteis.clear()
        self.pontuacao = 0
        self.vidas = VIDAS_INICIAIS
        self.game_over = False
        self.nivel_atual = 0
        self._spawn_asteroides_nivel()

    def _verificar_proximo_nivel(self):
        """
        Verifica se todos os asteroides foram destruídos para avançar de nível.
        """
        if self.game_over or not self.nave or not self.nave.ativo:
            return 

        # Avança de nível se não houver mais asteroides na tela
        if not self.asteroides:
            self.nivel_atual += 1
            self.pontuacao += 1000 * self.nivel_atual # Bônus por nível
            print(f"Nível {self.nivel_atual} iniciado.")
            
            # Ativa o power-up de tiro triplo como recompensa
            self.nave.ativar_tiro_triplo(DURACAO_TIRO_TRIPLO_SEGUNDOS)
            
            pygame.time.wait(1000) # Pequena pausa antes do próximo nível
            self._spawn_asteroides_nivel() # Gera novos asteroides
            
            # Centraliza a nave para o início do novo nível
            self.nave.posicao = Vetor2D(LARGURA_TELA / 2, ALTURA_TELA / 2)
            self.nave.velocidade = Vetor2D(0, 0)

    def _spawn_asteroides_nivel(self):
        num_asteroides = ASTEROIDES_INICIAIS + self.nivel_atual * 2
        self.asteroides = []
        for _ in range(num_asteroides):
            while True:
                pos_x = random.randint(0, LARGURA_TELA)
                pos_y = random.randint(0, ALTURA_TELA)
                pos_candidata = Vetor2D(pos_x, pos_y)
                if not self.nave or (pos_candidata - self.nave.posicao).magnitude() > self.nave.raio * 5:
                    self.asteroides.append(Asteroide(pos_candidata, "grande"))
                    break

    def _processar_input_jogo(self):
        if not self.nave or not self.nave.ativo or self.game_over or self.jogo_pausado:
            return

        teclas = pygame.key.get_pressed()
        self.nave.rotacionando_esquerda = teclas[pygame.K_a] or teclas[pygame.K_LEFT]
        self.nave.rotacionando_direita = teclas[pygame.K_d] or teclas[pygame.K_RIGHT]
        self.nave.acelerando = teclas[pygame.K_w] or teclas[pygame.K_UP]

        # Tiro com mouse esquerdo
        if pygame.K_SPACE:
            if pygame.time.get_ticks() - self.nave.ultimo_tiro_tempo > COOLDOWN_TIRO:
                novos_projeteis = self.nave.atirar()
                self.projeteis.extend(novos_projeteis)
                self.nave.ultimo_tiro_tempo = pygame.time.get_ticks()

    def _atualizar_objetos(self, delta_tempo: float):
        self.fundo_estrelado.atualizar(delta_tempo)
        if self.nave and self.nave.ativo:
            self.nave.atualizar(delta_tempo)

        # Atualiza todos os objetos do jogo
        for entidade_lista in [self.asteroides, self.projeteis, self.ovnis, self.ovni_projeteis, self.lasers_fantasma]:
            for entidade in entidade_lista:
                entidade.atualizar(delta_tempo)

        # Lógica de spawn e atualização específica de Fantasmas
        if self.nave and self.nave.ativo:
            # Spawna um novo fantasma se houver espaço
            if len(self.fantasmas) < MAX_FANTASMAS_TELA and random.random() < CHANCE_SPAWN_FANTASMA:
                self.fantasmas.append(NaveFantasma())
                print("DEBUG: *** CONDIÇÃO DE SPAWN DO FANTASMA ATINGIDA! ***")

            # Atualiza os fantasmas existentes
            for fantasma in self.fantasmas:
                laser = fantasma.atualizar(delta_tempo, self.nave.posicao)
                if laser:
                    self.lasers_fantasma.append(laser)

        # Lógica de tiro do OVNI
        if self.nave and self.nave.ativo:
            for ovni in self.ovnis:
                if ovni.ativo:
                    novos_tiros_ovni = ovni.tentar_atirar(self.nave.posicao)
                    if novos_tiros_ovni:
                        self.ovni_projeteis.extend(novos_tiros_ovni)

        # Remove objetos inativos
        self.projeteis = [p for p in self.projeteis if p.ativo]
        self.ovni_projeteis = [p for p in self.ovni_projeteis if p.ativo]
        self.asteroides = [a for a in self.asteroides if a.ativo]
        self.ovnis = [o for o in self.ovnis if o.ativo]
        self.lasers_fantasma = [l for l in self.lasers_fantasma if l.ativo]
        self.fantasmas = [f for f in self.fantasmas if f.ativo or f.estado == EstadoFantasma.INVISIVEL]

        # Lógica de Spawn de OVNIs
        if random.random() < CHANCE_SPAWN_OVNI and len(self.ovnis) < MAX_OVNIS_TELA:
            # Escolhe aleatoriamente qual tipo de OVNI criar
            tipo_ovni = random.choice([OvniX, OvniCruz])
            self.ovnis.append(tipo_ovni()) # Cria uma instância do tipo escolhido

        # Spawn
        if len(self.fantasmas) < MAX_FANTASMAS_TELA and random.random() < CHANCE_SPAWN_FANTASMA:
            # Garante que só crie um fantasma se não houver um no estado INVISIVEL esperando para aparecer
            # A checagem 'all' pode ser complexa, vamos simplificar para debug:
            if len(self.fantasmas) == 0: # Simplificando: só spawna se não houver NENHUM fantasma
                print("DEBUG: *** CONDIÇÃO DE SPAWN DO FANTASMA ATINGIDA! ***") # <<< ADICIONE ESTE PRINT
                self.fantasmas.append(NaveFantasma())

        # Atualização
        if self.nave and self.nave.ativo:
            for fantasma in self.fantasmas:
                # Vamos verificar se a atualização está sendo chamada
                print(f"DEBUG: Atualizando fantasma no estado {fantasma.estado}") # <<< ADICIONE ESTE PRINT
                laser = fantasma.atualizar(delta_tempo, self.nave.posicao)
                if laser:
                    self.lasers_fantasma.append(laser)

        # Limpeza de objetos inativos
        self.fantasmas = [f for f in self.fantasmas if f.ativo or f.estado == EstadoFantasma.INVISIVEL]
        self.lasers_fantasma = [l for l in self.lasers_fantasma if l.ativo]

    def _checar_colisoes(self):
        if not self.nave or not self.nave.ativo:
            return

        # --- Colisão de Projéteis da Nave com Inimigos ---
        novos_asteroides = []
        for projetil in list(self.projeteis):
            if not projetil.ativo: continue

            # Checa colisão com Asteroides
            for asteroide in list(self.asteroides):
                if asteroide.ativo and projetil.colide_com(asteroide):
                    projetil.ativo = False
                    self.pontuacao += asteroide.pontos
                    self.gerenciador_som.tocar_som('explosao_asteroide')
                    novos_asteroides.extend(asteroide.dividir())
                    break # Projétil só atinge uma coisa

            # Checa colisão com OVNIs
            for ovni in list(self.ovnis):
                if projetil.ativo and ovni.ativo and projetil.colide_com(ovni):
                    projetil.ativo = False
                    ovni.ativo = False
                    self.pontuacao += PONTOS_OVNI
                    break

            # Checa colisão com Nave Fantasma
            for fantasma in list(self.fantasmas):
                 if projetil.ativo and fantasma.ativo and projetil.colide_com(fantasma):
                    projetil.ativo = False
                    fantasma.ativo = False
                    self.pontuacao += PONTOS_FANTASMA
                    print("DEBUG: Nave Fantasma destruída!")
                    break

        # Adiciona os novos fragmentos de asteroides à lista principal
        self.asteroides.extend(novos_asteroides)

        # --- Colisão da Nave com Perigos ---
        if not self.nave.ativo: return # Se a nave foi destruída por um projétil, para aqui

        # Nave vs. Projéteis de OVNI
        for proj in list(self.ovni_projeteis):
            if proj.ativo and self.nave.colide_com(proj):
                proj.ativo = False
                self._nave_destruida()
                if not self.nave.ativo: return # Para se a nave foi destruída

        # Nave vs. Lasers de Fantasma
        for laser in self.lasers_fantasma:
            if laser.ativo and laser.colide_com(self.nave):
                laser.ativo = False
                self._nave_destruida()
                if not self.nave.ativo: return # Para se a nave foi destruída

        # Nave vs. Asteroides
        for asteroide in list(self.asteroides):
            if asteroide.ativo and self.nave.colide_com(asteroide):
                self._nave_destruida()
                # Asteroide também é destruído ou se divide na colisão com a nave
                self.asteroides.extend(asteroide.dividir()) 
                if not self.nave.ativo: return # Para se a nave foi destruída
                break # Nave só colide com um asteroide por vez

        # Nave vs. OVNIs
        for ovni in list(self.ovnis):
            if ovni.ativo and self.nave.colide_com(ovni):
                ovni.ativo = False # OVNI também é destruído
                self._nave_destruida()
                if not self.nave.ativo: return # Para se a nave foi destruída
                break

        # --- Colisão Entre Asteroides (Para evitar tremedeira) ---
        for i in range(len(self.asteroides)):
            ast1 = self.asteroides[i]
            if not ast1.ativo: continue
            for j in range(i + 1, len(self.asteroides)):
                ast2 = self.asteroides[j]
                if not ast2.ativo: continue

                if ast1.colide_com(ast2):
                    # 1. Correção de Posição
                    distancia_vetor = ast1.posicao - ast2.posicao
                    distancia = distancia_vetor.magnitude()
                    if distancia == 0:
                        distancia_vetor = Vetor2D(1, 0)
                        distancia = 1
                    sobreposicao = (ast1.raio + ast2.raio) - distancia
                    direcao_separacao = distancia_vetor / distancia
                    deslocamento = direcao_separacao * (sobreposicao / 2)
                    ast1.posicao += deslocamento
                    ast2.posicao -= deslocamento

                                        # 2. Resposta de Velocidade (com limite de velocidade máxima)
                    v1 = ast1.velocidade
                    v2 = ast2.velocidade
                    x1 = ast1.posicao
                    x2 = ast2.posicao
                    
                    dist_quadrada = (x1.distancia_ate(x2))**2
                    if dist_quadrada == 0: continue
                    
                    fator = 2 * (v1 - v2).dot(x1 - x2) / dist_quadrada
                    
                    # Calcula as novas velocidades temporariamente
                    nova_velocidade1 = v1 - (x1 - x2) * fator
                    nova_velocidade2 = v2 - (x2 - x1) * fator

                    # VERIFICA E APLICA O LIMITE DE VELOCIDADE
                    if nova_velocidade1.magnitude() > VEL_MAX_ASTEROIDE:
                        nova_velocidade1 = nova_velocidade1.normalizar() * VEL_MAX_ASTEROIDE
                    
                    if nova_velocidade2.magnitude() > VEL_MAX_ASTEROIDE:
                        nova_velocidade2 = nova_velocidade2.normalizar() * VEL_MAX_ASTEROIDE

                    # Atribui as velocidades finais (já limitadas)
                    ast1.velocidade = nova_velocidade1
                    ast2.velocidade = nova_velocidade2


    def _nave_destruida(self):
        if not self.nave or not self.nave.ativo:
            return
        
        self.gerenciador_som.tocar_som('explosao_nave') # <<< TOCA O SOM
        print(f"DEBUG: Nave destruída. Vidas antes: {self.vidas}")


        print(f"DEBUG: Nave destruída. Vidas antes: {self.vidas}")
        self.nave.ativo = False
        self.vidas -= 1
        self.nave.tem_tiro_triplo = False

        if self.vidas <= 0:
            self.game_over = True
            print("GAME OVER")
        else:
            print(f"Vida perdida. Vidas restantes: {self.vidas}. Nave será respawnada no próximo frame.")
            self.tempo_para_respawn = pygame.time.get_ticks() + 1500

    def _respawn_nave_se_necessario(self):
        """Restaura a nave se ela foi destruída e o tempo de espera já passou."""
        # A condição agora checa se o timer foi ativado (é maior que zero) e se o tempo atual já passou do agendado.
        if self.nave and not self.nave.ativo and self.tempo_para_respawn > 0 and pygame.time.get_ticks() >= self.tempo_para_respawn:
            
            print("DEBUG: Nave está respawnando (timer atingido).")
            # REMOVEMOS a linha pygame.time.wait(1500)

            # Recria a nave no centro
            self.nave.posicao = Vetor2D(LARGURA_TELA / 2, ALTURA_TELA / 2)
            self.nave.velocidade = Vetor2D(0, 0)
            self.nave.angulo_graus = 0
            self.nave.ativo = True # Ativa a nave
            
            # Zera o timer para que esta lógica não seja executada novamente até a próxima morte
            self.tempo_para_respawn = 0
            
            # Aplica invulnerabilidade temporária
            self.nave.tempo_invulneravel_fim = pygame.time.get_ticks() + TEMPO_INVENCIBILIDADE_SEGUNDOS * 1000

    def _desenhar_hud(self):
        texto_pontuacao = self.fonte_hud.render(f"Pontuação: {self.pontuacao}", True, BRANCO)
        self.tela.blit(texto_pontuacao, (10, 10))

        for i in range(self.vidas):
            vida_nave = Nave(Vetor2D(0, 0))
            vida_nave.raio = 8
            vida_nave.posicao = Vetor2D(LARGURA_TELA - 30 - i * 25, 25)
            vida_nave.angulo_graus = 0
            vida_nave.desenhar(self.tela)

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
            print("DEBUG: Jogo terminado, save de 'Continue' não será criado.")
            try:
                if os.path.exists(ARQUIVO_SAVE_GAME): os.remove(ARQUIVO_SAVE_GAME)
            except OSError: pass
            return

        estado = {
            "nave": self.nave.to_dict() if self.nave else None,
            "asteroides": [a.to_dict() for a in self.asteroides],
            "projeteis": [p.to_dict() for p in self.projeteis],
            "ovnis": [o.to_dict() for o in self.ovnis],
            "ovni_projeteis": [op.to_dict() for op in self.ovni_projeteis],
            "fantasmas": [f.to_dict() for f in self.fantasmas],
            "lasers_fantasma": [l.to_dict() for l in self.lasers_fantasma],
            "pontuacao": self.pontuacao,
            "vidas": self.vidas,
            "nivel_atual": self.nivel_atual,
            "game_over": self.game_over
        }

        try:
            with open(ARQUIVO_SAVE_GAME, "w") as f:
                json.dump(estado, f, indent=4)
            print("Estado salvo.")
        except Exception as e:
            print(f"Erro ao salvar: {e}")

    def carregar_estado_jogo(self):
        try:
            if not os.path.exists(ARQUIVO_SAVE_GAME):
                print("Arquivo de save não encontrado. Iniciando novo jogo.")
                self.reiniciar_jogo_completo() # Inicia um jogo limpo
                return False

            with open(ARQUIVO_SAVE_GAME, "r") as f:
                data = json.load(f)

            if data.get("game_over", False) or not data.get("nave"):
                print("Arquivo de save é de um jogo terminado ou inválido. Iniciando novo jogo.")
                self.reiniciar_jogo_completo()
                return False

            self.game_over = data.get("game_over", False)
            self.nivel_atual = data.get("nivel_atual", 0)
            self.pontuacao = data.get("pontuacao", 0)
            self.vidas = data.get("vidas", VIDAS_INICIAIS)

            # Recria todos os objetos usando CLASSE_MAP
            self.nave = Nave.from_dict(data["nave"])
            self.asteroides = [Asteroide.from_dict(a) for a in data.get("asteroides", [])]
            self.projeteis = [Projetil.from_dict(p) for p in data.get("projeteis", [])]
            self.ovnis = [CLASSE_MAP[o["classe_tipo"]].from_dict(o) for o in data.get("ovnis", [])]
            self.ovni_projeteis = [OVNIProjetil.from_dict(op) for op in data.get("ovni_projeteis", [])]
            self.fantasmas = [CLASSE_MAP[f["classe_tipo"]].from_dict(f) for f in data.get("fantasmas", [])] # <<< Adicionar
            self.lasers_fantasma = [CLASSE_MAP[l["classe_tipo"]].from_dict(l) for l in data.get("lasers_fantasma", [])] # <<< Adicionar

            print("Estado do jogo carregado com sucesso.")
            return True
        except Exception as e:
            print(f"Erro crítico ao carregar estado do jogo: {e}")
            import traceback
            traceback.print_exc()
            self.reiniciar_jogo_completo() # Em caso de erro, inicia um novo jogo por segurança
            return False
        
    def _mostrar_menu_pausa(self):
        tema_pausa = pygame_menu.themes.THEME_DARK.copy()
        tema_pausa.background_color = (0, 0, 0, 180)
        menu = pygame_menu.Menu(
            title="JOGO PAUSADO",
            width=int(LARGURA_TELA * 0.5),
            height=int(ALTURA_TELA * 0.6),
            theme=tema_pausa,
            onclose=pygame_menu.events.BACK
        )

        menu.add.button("Retornar ao Jogo", lambda: self._set_acao(EstadoJogoLoop.CONTINUAR_JOGO))
        menu.add.button("Salvar e Sair", lambda: self._set_acao(EstadoJogoLoop.VOLTAR_AO_MENU_COM_SAVE))
        menu.add.button("Sair sem Salvar", lambda: self._set_acao(EstadoJogoLoop.VOLTAR_AO_MENU_SEM_SALVAR))

        fundo_pausa_snap = self.tela.copy()
        overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        fundo_pausa_snap.blit(overlay, (0, 0))

        texto = self.fonte_game_over.render("JOGO PAUSADO", True, BRANCO)
        rect = texto.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 2 - 50))
        fundo_pausa_snap.blit(texto, rect)

        self.jogo_pausado = True
        clock_pausa = pygame.time.Clock()
        while self.jogo_pausado and self.acao_menu_pausa is None:
            eventos = pygame.event.get()
            for evento in eventos:
                if evento.type == pygame.QUIT:
                    self._set_acao(EstadoJogoLoop.VOLTAR_AO_MENU_SEM_SALVAR)
                    self.jogo_pausado = False
                    break

            if not self.jogo_pausado:
                break

            menu.update(eventos)
            self.tela.blit(fundo_pausa_snap, (0, 0))
            menu.draw(self.tela)
            pygame.display.flip()
            clock_pausa.tick(FPS)

    def _set_acao(self, acao):
        if acao == EstadoJogoLoop.VOLTAR_AO_MENU_COM_SAVE:
            self.salvar_estado_jogo() # Salva o jogo aqui
        self.acao_menu_pausa = acao
        self.jogo_pausado = False

    # gerenciador_jogo.py (substitua o método inteiro)

    def loop_principal(self):
        print("DEBUG: Iniciando loop principal do jogo.")
        self.jogo_pausado = False
        self.acao_menu_pausa = None

        while True: # O loop agora continuará indefinidamente até um 'return' explícito.
            delta_tempo = self.clock.tick(FPS) / 1000.0
            eventos = pygame.event.get()

            # 1. TRATAMENTO DE EVENTOS (lógica corrigida)
            for evento in eventos:
                # CONDIÇÃO 1: Jogador fechou a janela?
                if evento.type == pygame.QUIT:
                    print("DEBUG: Evento QUIT (fechar janela) recebido.")
                    if not self.game_over:
                        self.salvar_estado_jogo()
                        return EstadoJogoLoop.VOLTAR_AO_MENU_COM_SAVE, self.pontuacao
                    else:
                        return EstadoJogoLoop.VOLTAR_AO_MENU_GAME_OVER, self.pontuacao

                # CONDIÇÃO 2: Jogador pressionou uma tecla?
                elif evento.type == pygame.KEYDOWN:
                    # Que tecla foi?
                    if evento.key == pygame.K_ESCAPE:
                        if self.game_over:
                            print("DEBUG: ESC pressionado na tela de GAME OVER.")
                            return EstadoJogoLoop.VOLTAR_AO_MENU_GAME_OVER, self.pontuacao
                        else: # Se o jogo está rolando, abre o menu de pausa
                            print("DEBUG: ESC pressionado para abrir menu de pausa.")
                            self.jogo_pausado = True
                            self._mostrar_menu_pausa()
                            if self.acao_menu_pausa != EstadoJogoLoop.CONTINUAR_JOGO:
                                return self.acao_menu_pausa, self.pontuacao
                            self.jogo_pausado = False
                            self.acao_menu_pausa = None
                    
                    # Tiro com a barra de espaço
                    elif evento.key == pygame.K_SPACE and self.nave and self.nave.ativo and not self.jogo_pausado and not self.game_over:
                        novos_projeteis = self.nave.atirar()
                        self.projeteis.extend(novos_projeteis)
                        if novos_projeteis: # Verifica se um tiro foi realmente criado
                            self.gerenciador_som.tocar_som('tiro') # <<< TOCA O SOM
                            self.projeteis.extend(novos_projeteis)


            # 2. LÓGICA DO JOGO (só executa se não estiver pausado)
            if not self.jogo_pausado:
                self._processar_input_jogo() # Processa movimento contínuo da nave

                if not self.game_over:
                    self._respawn_nave_se_necessario()
                    if self.nave and self.nave.ativo:
                        self._atualizar_objetos(delta_tempo)
                        self._checar_colisoes()
                        self._verificar_proximo_nivel()

                # 3. DESENHO
                self.tela.fill(PRETO)
                self.fundo_estrelado.desenhar(self.tela)

                # Desenha todos os objetos de jogo
                if self.nave: self.nave.desenhar(self.tela)
                for asteroide in self.asteroides: asteroide.desenhar(self.tela)
                for projetil in self.projeteis: projetil.desenhar(self.tela)
                for ovni in self.ovnis: ovni.desenhar(self.tela)
                for proj in self.ovni_projeteis: proj.desenhar(self.tela)
                for fantasma in self.fantasmas: fantasma.desenhar(self.tela)
                for laser in self.lasers_fantasma: laser.desenhar(self.tela)
                
                self._desenhar_hud()
                if self.game_over:
                    self._desenhar_tela_game_over()

                pygame.display.flip()