import pygame
import pygame_menu
import json
import os

# Importações locais
from config import *
from gerenciador import GerenciadorJogo, EstadoJogoLoop
from entidades import CLASSE_MAP
from ranking_manager import RankingManager
from jogador_ranking import JogadorRanking
from vetor import *


class GerenciadorSom:
    def __init__(self):
        self.__volume_musica = VOLUME_MUSICA_PADRAO
        self.__volume_sfx = VOLUME_SFX_PADRAO
        try:
            # Carrega os efeitos sonoros em memória
            self.__som_tiro = pygame.mixer.Sound(SOM_TIRO)
            self.__som_explosao_asteroide = pygame.mixer.Sound(SOM_EXPLOSAO_ASTEROIDE)
            self.__som_explosao_nave = pygame.mixer.Sound(SOM_EXPLOSAO_NAVE)
            self.__som_ovni_movendo = pygame.mixer.Sound(SOM_OVNI_MOVENDO)
            self.__som_ovni_tiro = pygame.mixer.Sound(SOM_OVNI_TIRO)
            self.__som_fantasma_invisivel = pygame.mixer.Sound(SOM_FANTASMA_INVISIVEL)
            self.atualizar_volumes_sfx()
            print("Efeitos sonoros carregados.")
        except pygame.error as e:
            print(f"AVISO: Não foi possível carregar um ou mais arquivos de som: {e}")
            dummy_sound = type('DummySound', (), {'play': lambda s, *a, **kw: None, 'stop': lambda s: None, 'set_volume': lambda s, v: None})()
            self.__som_tiro, self.__som_explosao_asteroide, self.__som_explosao_nave, self.__som_ovni_movendo, self.__som_ovni_tiro, self.__som_fantasma_invisivel = (dummy_sound,) * 6

    def get_volume_musica(self) -> float:
        return self.__volume_musica

    def get_volume_sfx(self) -> float:
        return self.__volume_sfx

    def tocar_musica_fundo(self, tipo_musica: str = 'menu'):
        pygame.mixer.music.stop()
        try:
            arquivo_musica = MUSICA_FUNDO_MENU if tipo_musica == 'menu' else MUSICA_FUNDO_JOGO
            pygame.mixer.music.load(arquivo_musica)
            pygame.mixer.music.set_volume(self.__volume_musica)
            pygame.mixer.music.play(-1)  # -1 para loop infinito
        except pygame.error as e:
            print(f"AVISO: Não foi possível tocar a música '{tipo_musica}': {e}")

    def parar_musica(self):
        pygame.mixer.music.stop()

    def tocar_som(self, nome_som: str, loop=0):
        if nome_som == 'tiro': self.__som_tiro.play()
        elif nome_som == 'explosao_asteroide': self.__som_explosao_asteroide.play()
        elif nome_som == 'explosao_nave': self.__som_explosao_nave.play()
        elif nome_som == 'ovni_tiro': self.__som_ovni_tiro.play()
        elif nome_som == 'ovni_movendo': self.__som_ovni_movendo.play(loops=loop)
        elif nome_som == 'fantasma_invisivel': self.__som_fantasma_invisivel.play(loops=loop)

    def parar_som(self, nome_som: str):
        if nome_som == 'ovni_movendo': self.__som_ovni_movendo.stop()
        elif nome_som == 'fantasma_invisivel': self.__som_fantasma_invisivel.stop()

    def set_volume_musica(self, volume, *args):
        novo_volume = float(volume) / 100.0
        self.__volume_musica = max(0.0, min(1.0, novo_volume))
        pygame.mixer.music.set_volume(self.__volume_musica)

    def set_volume_sfx(self, volume, *args):
        novo_volume = float(volume) / 100.0
        self.__volume_sfx = max(0.0, min(1.0, novo_volume))
        self.atualizar_volumes_sfx()

    def atualizar_volumes_sfx(self):
        self.__som_tiro.set_volume(self.__volume_sfx)
        self.__som_explosao_asteroide.set_volume(self.__volume_sfx)
        self.__som_explosao_nave.set_volume(self.__volume_sfx)
        self.__som_ovni_movendo.set_volume(self.__volume_sfx * 0.3)
        self.__som_ovni_tiro.set_volume(self.__volume_sfx)
        self.__som_fantasma_invisivel.set_volume(self.__volume_sfx * 0.6)


class App:
    def __init__(self):
        pygame.init()
        self.__tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
        pygame.display.set_caption(TITULO_JOGO)
        self.__clock = pygame.time.Clock()
        self.__gerenciador_som = GerenciadorSom()
        self.__ranking_manager = RankingManager()
        self.__botao_continuar_ref = None
        self.__menu_principal = self._criar_menu_principal()

    def _criar_menu_principal(self) -> pygame_menu.Menu:
        tema = pygame_menu.themes.THEME_DARK.copy()
        tema.widget_font_size = 24; tema.title_font_size = 36; tema.background_color = (40, 40, 60)
        menu = pygame_menu.Menu(title="Asteroids UFV-CRP", width=LARGURA_TELA, height=ALTURA_TELA, theme=tema)
        menu.add.button('Novo Jogo', lambda: self._iniciar_jogo_callback(carregar_save=False))
        
        self.__botao_continuar_ref = menu.add.button('Continuar Jogo', lambda: self._iniciar_jogo_callback(carregar_save=True))
        
        menu.add.button('Ranking', self._criar_menu_ranking())
        menu.add.button('Configurações', self._criar_menu_configuracoes())
        menu.add.button('Sair', pygame_menu.events.EXIT)
        menu.set_onbeforeopen(self._atualizar_botao_continuar)
        
        return menu

    def _criar_menu_ranking(self) -> pygame_menu.Menu:
        menu_ranking = pygame_menu.Menu(
            title="Ranking - Top 10",
            width=LARGURA_TELA * 0.8,
            height=ALTURA_TELA * 0.9,
            theme=pygame_menu.themes.THEME_DARK
        )
        frame = menu_ranking.add.frame_v(width=LARGURA_TELA * 0.7, height=ALTURA_TELA * 0.7)
        frame._relax = True

        def atualizar(menu_atual, proximo_menu):
            # Loop para limpar os widgets antigos do ranking antes de adicionar os novos.
            while frame.get_widgets():
                menu_ranking.remove_widget(frame.get_widgets()[0])

            self.__ranking_manager.carregar_de_arquivo(ARQUIVO_HIGH_SCORES)
            jogadores = self.__ranking_manager.get_jogadores()
            
            if not jogadores:
                frame.pack(menu_ranking.add.label("Nenhum recorde ainda!", font_size=20))
            else:
                for i, jogador in enumerate(jogadores, 1):
                    frame.pack(menu_ranking.add.label(f"{i}. {jogador.get_nome()}: {jogador.get_pontuacao()} pts"))

        menu_ranking.set_onbeforeopen(atualizar)
        menu_ranking.add.button("Voltar", pygame_menu.events.BACK, margin=(0, 20))
        return menu_ranking

    def _criar_menu_configuracoes(self) -> pygame_menu.Menu:
        menu_cfg = pygame_menu.Menu(title="Configurações", width=LARGURA_TELA*0.7, height=ALTURA_TELA*0.6, theme=pygame_menu.themes.THEME_DARK)
        menu_cfg.add.label("Volume da Música:")
        menu_cfg.add.range_slider("", default=int(self.__gerenciador_som.get_volume_musica()*100), range_values=(0, 100), increment=1, onchange=self.__gerenciador_som.set_volume_musica)
        menu_cfg.add.label("Volume dos Efeitos Sonoros (SFX):")
        menu_cfg.add.range_slider("", default=int(self.__gerenciador_som.get_volume_sfx()*100), range_values=(0, 100), increment=1, onchange=self.__gerenciador_som.set_volume_sfx)
        menu_cfg.add.button("Voltar", pygame_menu.events.BACK)
        return menu_cfg

    def _iniciar_jogo_callback(self, carregar_save=False):
        self.__menu_principal.disable()
        self.__gerenciador_som.tocar_musica_fundo('jogo')
        
        jogo = GerenciadorJogo(self.__tela, self.__clock, self.__gerenciador_som)

        if carregar_save:
            if not jogo.carregar_estado_jogo():
                print("Não foi possível carregar o save, iniciando novo jogo.")
                jogo.reiniciar_jogo_completo()
        else:
            jogo.reiniciar_jogo_completo()

        # O loop principal do jogo é executado aqui
        retorno_do_jogo, pontuacao_final = jogo.loop_principal()

        # Adiciona a lógica para salvar o jogo quando o jogador escolhe "Salvar e Sair"
        if retorno_do_jogo == EstadoJogoLoop.VOLTAR_AO_MENU_COM_SAVE:
            jogo.salvar_estado_jogo()

        self.__gerenciador_som.tocar_musica_fundo('menu')
        
        # Lógica de Game Over (remove o save e pede o nome do jogador)
        if retorno_do_jogo == EstadoJogoLoop.VOLTAR_AO_MENU_GAME_OVER:
            if os.path.exists(ARQUIVO_SAVE_GAME):
                try: 
                    os.remove(ARQUIVO_SAVE_GAME)
                except OSError: 
                    pass
            self._coletar_nome_jogador_e_salvar_score(pontuacao_final)
        
        self.__menu_principal.enable()
        self._atualizar_botao_continuar()


    def _coletar_nome_jogador_e_salvar_score(self, pontuacao_final: int):
        """
        Cria e exibe um menu temporário para o jogador digitar o nome e salvar a pontuação.
        """
        nome_var = ["JOGADOR"]
        tema_input = pygame_menu.themes.THEME_DARK.copy()
        tema_input.widget_font_size = 20
        tema_input.title_font_size = 24

        menu_input = pygame_menu.Menu(
            title=f"FIM DE JOGO! Pontos: {pontuacao_final}",
            width=int(LARGURA_TELA * 0.7), height=int(ALTURA_TELA * 0.5), theme=tema_input,
            onclose=pygame_menu.events.NONE
        )
        
        input_field = menu_input.add.text_input("Nome: ", default="JOGADOR", maxchar=10, onchange=lambda v: nome_var.__setitem__(0, v))
        
        # Adiciona um Label para exibir mensagens de erro
        error_label = menu_input.add.label("", font_color=(255, 100, 100), font_size=18)

        def salvar_e_fechar():
            nome = nome_var[0].strip().upper()
            
            # Atualiza o Label em vez de chamar um método que não existe
            if not 3 <= len(nome) <= 10:
                error_label.set_title("Nome deve ter 3-10 caracteres.")
                return

            # Se a validação passar, limpa a mensagem de erro e salva
            error_label.set_title("")
            self.__ranking_manager.carregar_de_arquivo(ARQUIVO_HIGH_SCORES)
            self.__ranking_manager.adicionar_jogador(JogadorRanking(nome, pontuacao_final))
            self.__ranking_manager.salvar_em_arquivo(ARQUIVO_HIGH_SCORES)
            menu_input.disable()

        menu_input.add.button("Salvar e Voltar", salvar_e_fechar)
        menu_input.add.button("Voltar Sem Salvar", menu_input.disable)

        self.__menu_principal.disable()
        menu_input.mainloop(self.__tela)
        self.__menu_principal.enable()

    def _verificar_save_valido(self) -> bool:
        if not os.path.exists(ARQUIVO_SAVE_GAME): return False
        try:
            with open(ARQUIVO_SAVE_GAME, 'r') as f: return not json.load(f).get("game_over", False)
        except (json.JSONDecodeError, IOError): return False

    def _atualizar_botao_continuar(self):
        if not self.__botao_continuar_ref: return
        eh_valido = self._verificar_save_valido()
        self.__botao_continuar_ref.set_title("Continuar Jogo" if eh_valido else "Continuar Jogo (Vazio)")
        self.__botao_continuar_ref.update_font({'color': BRANCO if eh_valido else (100, 100, 100)})
        self.__botao_continuar_ref.set_attribute("readonly", not eh_valido)

    def run(self):
        self.__gerenciador_som.tocar_musica_fundo('menu')
        self._atualizar_botao_continuar()
        try:
            self.__menu_principal.mainloop(self.__tela)
        except Exception as e:
            import traceback
            print(f"Ocorreu um erro fatal no loop principal: {e}"); traceback.print_exc()
        finally:
            pygame.quit(); print("Jogo encerrado.")

if __name__ == '__main__':
    app = App()
    app.run()