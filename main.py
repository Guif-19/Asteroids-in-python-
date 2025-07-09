import pygame
import pygame_menu
import json
import os
from typing import Optional

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

    def get_tela(self) -> pygame.Surface:
        return self.__tela

    def get_clock(self) -> pygame.time.Clock:
        return self.__clock

    def get_gerenciador_som(self) -> 'GerenciadorSom':
        return self.__gerenciador_som

    def get_ranking_manager(self) -> 'RankingManager':
        return self.__ranking_manager

    def get_menu_principal(self) -> 'pygame_menu.Menu':
        return self.__menu_principal

    def get_botao_continuar_ref(self) -> Optional[pygame_menu.widgets.Button]:
        return self.__botao_continuar_ref

    def set_botao_continuar_ref(self, botao: pygame_menu.widgets.Button):
        self.__botao_continuar_ref = botao


    def _criar_menu_principal(self) -> pygame_menu.Menu:
        tema = pygame_menu.themes.THEME_DARK.copy()
        tema.widget_font_size = 24
        tema.title_font_size = 36
        tema.background_color = (40, 40, 60)
        menu = pygame_menu.Menu(title="Asteroids UFV-CRP", width=LARGURA_TELA, height=ALTURA_TELA, theme=tema)
        
        menu.add.button('Novo Jogo', lambda: self._iniciar_jogo_callback(carregar_save=False))
        
        # Usa o setter para definir a referência do botão
        self.set_botao_continuar_ref(
            menu.add.button('Continuar Jogo', lambda: self._iniciar_jogo_callback(carregar_save=True))
        )
        
        menu.add.button('Ranking', self._criar_menu_ranking())
        menu.add.button('Configurações', self._criar_menu_configuracoes())
        menu.add.button('Sair', pygame_menu.events.EXIT)
        menu.set_onbeforeopen(self._atualizar_botao_continuar)
        
        return menu

    def _criar_menu_ranking(self) -> pygame_menu.Menu:
        menu_ranking = pygame_menu.Menu(title="Ranking - Top 10", width=LARGURA_TELA * 0.8, height=ALTURA_TELA * 0.9, theme=pygame_menu.themes.THEME_DARK)
        frame = menu_ranking.add.frame_v(width=LARGURA_TELA * 0.7, height=ALTURA_TELA * 0.7)
        frame._relax = True
        
        def atualizar_ranking(menu_atual, proximo_menu):
            ranking_manager = self.get_ranking_manager() # Usa getter
            ranking_manager.carregar_scores()
            jogadores = ranking_manager.get_jogadores()

            if menu_ranking.get_widget('ranking_table'):
                menu_ranking.remove_widget('ranking_table')

            tabela = menu_ranking.add.table(table_id='ranking_table')
            tabela.add_row(['Pos.', 'Nome', 'Pontuacao'], cell_align=pygame_menu.locals.ALIGN_CENTER, cell_padding=5, cell_font=pygame_menu.font.FONT_FRANCHISE)
            if not jogadores:
                tabela.add_row(['-', 'Nenhum recorde salvo', '-'], cell_align=pygame_menu.locals.ALIGN_CENTER)
            else:
                for i, jogador in enumerate(jogadores, 1):
                    tabela.add_row([str(i), jogador.get_nome(), str(jogador.get_pontuacao())], cell_align=pygame_menu.locals.ALIGN_CENTER)
            frame.pack(tabela)

        menu_ranking.set_onbeforeopen(atualizar_ranking)
        menu_ranking.add.button("Voltar", pygame_menu.events.BACK, margin=(0, 20))
        return menu_ranking

    def _criar_menu_configuracoes(self) -> pygame_menu.Menu:
        gerenciador_som = self.get_gerenciador_som() # Usa getter
        menu_cfg = pygame_menu.Menu(title="Configurações", width=LARGURA_TELA*0.7, height=ALTURA_TELA*0.6, theme=pygame_menu.themes.THEME_DARK)
        menu_cfg.add.label("Volume da Música:")
        menu_cfg.add.range_slider("", default=int(gerenciador_som.get_volume_musica()*100), range_values=(0, 100), increment=1, onchange=gerenciador_som.set_volume_musica)
        menu_cfg.add.label("Volume dos Efeitos Sonoros (SFX):")
        menu_cfg.add.range_slider("", default=int(gerenciador_som.get_volume_sfx()*100), range_values=(0, 100), increment=1, onchange=gerenciador_som.set_volume_sfx)
        menu_cfg.add.button("Voltar", pygame_menu.events.BACK)
        return menu_cfg

    def _iniciar_jogo_callback(self, carregar_save=False):
        self.get_menu_principal().disable() # Usa getter
        gerenciador_som = self.get_gerenciador_som()
        gerenciador_som.tocar_musica_fundo('jogo')
        
        jogo = GerenciadorJogo(self.get_tela(), self.get_clock(), gerenciador_som)

        if carregar_save:
            if not jogo.carregar_estado_jogo():
                print("Não foi possível carregar o save, iniciando novo jogo.")
                jogo.reiniciar_jogo_completo()
        else:
            jogo.reiniciar_jogo_completo()

        retorno_do_jogo, pontuacao_final = jogo.loop_principal()

        if retorno_do_jogo == EstadoJogoLoop.VOLTAR_AO_MENU_GAME_OVER:
            self._coletar_nome_jogador_e_salvar_score(pontuacao_final)
        
        gerenciador_som.tocar_musica_fundo('menu')
        self.get_menu_principal().enable() # Usa getter
        self._atualizar_botao_continuar()

    def _coletar_nome_jogador_e_salvar_score(self, pontuacao_final: int):
        if pontuacao_final <= 0: return
        menu_nome = pygame_menu.Menu(title="FIM DE JOGO", width=500, height=300, theme=pygame_menu.themes.THEME_DARK)
        menu_nome.add.label(f"Pontuacao Final: {pontuacao_final}", font_size=30)
        menu_nome.add.vertical_margin(20)
        text_input = menu_nome.add.text_input('Seu Nome: ', default='JOGADOR', maxchar=10)

        def acao_salvar():
            nome_digitado = text_input.get_value().strip().upper()
            if not nome_digitado: print("Nome não pode ser vazio!"); return
            
            print(f"Criando novo recorde para {nome_digitado} com {pontuacao_final} pontos.")
            novo_recorde = JogadorRanking(nome_digitado, pontuacao_final)
            
            ranking_manager = self.get_ranking_manager() # Usa getter
            ranking_manager.carregar_scores()
            ranking_manager.adicionar_score(novo_recorde)
            ranking_manager.salvar_scores()
            menu_nome.disable()
            self._atualizar_botao_continuar()

        menu_nome.add.button('Salvar Pontuacao', acao_salvar, margin=(20,0))
        menu_nome.add.button('Voltar ao Menu', menu_nome.disable)
        menu_nome.mainloop(self.get_tela()) # Usa getter

    def _verificar_save_valido(self) -> bool:
        if not os.path.exists(ARQUIVO_SAVE_GAME): return False
        try:
            with open(ARQUIVO_SAVE_GAME, 'r') as f:
                return not json.load(f).get("game_over", True)
        except (json.JSONDecodeError, IOError): return False

    def _atualizar_botao_continuar(self):
        botao = self.get_botao_continuar_ref() # Usa getter
        if not botao: return
        
        eh_valido = self._verificar_save_valido()
        botao.set_title("Continuar Jogo" if eh_valido else "Continuar (Vazio)")
        botao.update_font({'color': BRANCO if eh_valido else (100, 100, 100)})
        botao.readonly = not eh_valido # Atributo readonly pode ser acessado diretamente

    def run(self):
        self.get_gerenciador_som().tocar_musica_fundo('menu') # Usa getter
        self._atualizar_botao_continuar()
        try:
            self.get_menu_principal().mainloop(self.get_tela()) # Usa getters
        except Exception as e:
            import traceback
            print(f"Ocorreu um erro fatal no loop principal: {e}"); traceback.print_exc()
        finally:
            pygame.quit()
            print("Jogo encerrado.")

if __name__ == '__main__':
    app = App()
    app.run()