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


# --- Classe: GerenciadorSom ---
class GerenciadorSom:
    def __init__(self):
        self.volume_musica = VOLUME_MUSICA_PADRAO
        self.volume_sfx = VOLUME_SFX_PADRAO
        try:
            # Carrega os efeitos sonoros em memória
            self.som_tiro = pygame.mixer.Sound(SOM_TIRO)
            self.som_explosao_asteroide = pygame.mixer.Sound(SOM_EXPLOSAO_ASTEROIDE)
            self.som_explosao_nave = pygame.mixer.Sound(SOM_EXPLOSAO_NAVE)
            self.som_ovni_movendo = pygame.mixer.Sound(SOM_OVNI_MOVENDO)
            self.som_ovni_tiro = pygame.mixer.Sound(SOM_OVNI_TIRO)
            self.som_fantasma_invisivel = pygame.mixer.Sound(SOM_FANTASMA_INVISIVEL)
            self.atualizar_volumes_sfx()
            print("Efeitos sonoros carregados.")
        except pygame.error as e:
            print(f"AVISO: Não foi possível carregar um ou mais arquivos de som: {e}")
            self.som_tiro = type('DummySound', (), {'play': lambda: None, 'set_volume': lambda v: None})()
            self.som_explosao_asteroide, self.som_explosao_nave, self.som_ovni_movendo, self.som_ovni_tiro, self.som_fantasma_invisivel = (self.som_tiro,)*5

    def tocar_musica_fundo(self, tipo_musica: str = 'menu'):
        pygame.mixer.music.stop()
        try:
            arquivo_musica = MUSICA_FUNDO_MENU if tipo_musica == 'menu' else MUSICA_FUNDO_JOGO
            pygame.mixer.music.load(arquivo_musica)
            pygame.mixer.music.set_volume(self.volume_musica)
            pygame.mixer.music.play(-1)  # -1 para loop infinito
        except pygame.error as e:
            print(f"AVISO: Não foi possível tocar a música '{tipo_musica}': {e}")

    def parar_musica(self):
        pygame.mixer.music.stop()

    def tocar_som(self, nome_som: str, loop=0):
        if nome_som == 'tiro': self.som_tiro.play()
        elif nome_som == 'explosao_asteroide': self.som_explosao_asteroide.play()
        elif nome_som == 'explosao_nave': self.som_explosao_nave.play()
        elif nome_som == 'ovni_tiro': self.som_ovni_tiro.play()
        elif nome_som == 'ovni_movendo': self.som_ovni_movendo.play(loops=loop)
        elif nome_som == 'fantasma_invisivel': self.som_fantasma_invisivel.play(loops=loop)

    def parar_som(self, nome_som: str):
        if nome_som == 'ovni_movendo': self.som_ovni_movendo.stop()
        elif nome_som == 'fantasma_invisivel': self.som_fantasma_invisivel.stop()

    def set_volume_musica(self, volume, *args):
        # Converte o volume (0-100) para a escala do Pygame (0.0-1.0)
        novo_volume = float(volume) / 100.0
        self.volume_musica = max(0.0, min(1.0, novo_volume))
        pygame.mixer.music.set_volume(self.volume_musica)

    def set_volume_sfx(self, volume, *args):
        novo_volume = float(volume) / 100.0
        self.volume_sfx = max(0.0, min(1.0, novo_volume))
        self.atualizar_volumes_sfx()

    def atualizar_volumes_sfx(self):
        self.som_tiro.set_volume(self.volume_sfx)
        self.som_explosao_asteroide.set_volume(self.volume_sfx)
        self.som_explosao_nave.set_volume(self.volume_sfx)
        self.som_ovni_movendo.set_volume(self.volume_sfx * 0.3)
        self.som_ovni_tiro.set_volume(self.volume_sfx)
        self.som_fantasma_invisivel.set_volume(self.volume_sfx * 0.6)


# --- Funções de Callback para o Menu ---
def coletar_nome_jogador_e_salvar_score(tela_coleta, pontuacao_final_coleta, menu_que_chamou, clock):
    nome_jogador_var = ["JOGADOR"]
    tema_input = pygame_menu.themes.THEME_DARK.copy()
    tema_input.widget_font_size = 20
    tema_input.title_font_size = 24

    _menu_input_nome = pygame_menu.Menu(
        title=f"FIM DE JOGO! Pontos: {pontuacao_final_coleta}",
        width=int(LARGURA_TELA * 0.7), height=int(ALTURA_TELA * 0.5), theme=tema_input,
        onclose=pygame_menu.events.NONE
    )
    _menu_input_nome.add.label("Digite seu nome (3-10 caracteres):")
    input_field = _menu_input_nome.add.text_input("", default="JOGADOR", maxchar=10, onchange=lambda val: nome_jogador_var.__setitem__(0, val))

    deve_fechar_menu_input_flag = [False]

    def _acao_processar_e_fechar(salvar_score: bool):
        if salvar_score:
            nome = nome_jogador_var[0].strip().upper()
            if not 3 <= len(nome) <= 10:
                input_field.set_error("Nome deve ter entre 3 e 10 caracteres.")
                return
            ranking_manager = RankingManager()
            ranking_manager.carregar_de_arquivo(ARQUIVO_HIGH_SCORES)
            ranking_manager.adicionar_jogador(JogadorRanking(nome, pontuacao_final_coleta))
            ranking_manager.salvar_em_arquivo(ARQUIVO_HIGH_SCORES)
        
        deve_fechar_menu_input_flag[0] = True
        if _menu_input_nome.is_enabled(): _menu_input_nome.disable()

    _menu_input_nome.add.button("Salvar Score e Voltar", lambda: _acao_processar_e_fechar(salvar_score=True))
    _menu_input_nome.add.button("Voltar Sem Salvar", lambda: _acao_processar_e_fechar(salvar_score=False))

    if menu_que_chamou.is_enabled(): menu_que_chamou.disable()

    while not deve_fechar_menu_input_flag[0]:
        eventos = pygame.event.get()
        if any(e.type == pygame.QUIT for e in eventos):
            pygame.quit(); exit()
        if _menu_input_nome.is_enabled():
            _menu_input_nome.update(eventos)
            if _menu_input_nome.is_enabled():
                tela_coleta.fill((30, 30, 30))
                _menu_input_nome.draw(tela_coleta)
        pygame.display.flip()
        clock.tick(FPS)

    if not menu_que_chamou.is_enabled(): menu_que_chamou.enable()
    atualizar_botao_continuar(menu_que_chamou)


def iniciar_jogo_callback(tela_jogo, clock_jogo, gerenciador_som, menu_principal, carregar_save=False):
    menu_principal.disable()
    gerenciador_som.tocar_musica_fundo('jogo')
    jogo = GerenciadorJogo(tela_jogo, clock_jogo, gerenciador_som)
    if carregar_save:
        if not jogo.carregar_estado_jogo():
            print("Não foi possível carregar save, iniciando novo jogo.")
    else:
        jogo.reiniciar_jogo_completo()

    retorno_do_jogo, pontuacao_final = jogo.loop_principal()

    gerenciador_som.tocar_musica_fundo('menu')

    if retorno_do_jogo == EstadoJogoLoop.VOLTAR_AO_MENU_GAME_OVER:
        try:
            if os.path.exists(ARQUIVO_SAVE_GAME): os.remove(ARQUIVO_SAVE_GAME)
        except Exception as e: print(f"Aviso: não foi possível remover o save antigo: {e}")
        if pontuacao_final >= 0:
            coletar_nome_jogador_e_salvar_score(tela_jogo, pontuacao_final, menu_principal, clock_jogo)
        else:
            if not menu_principal.is_enabled(): menu_principal.enable()
            atualizar_botao_continuar(menu_principal)
    else:
        if not menu_principal.is_enabled(): menu_principal.enable()
        atualizar_botao_continuar(menu_principal)


def criar_menu_ranking() -> pygame_menu.Menu:
    """Cria e retorna o menu de ranking."""
    menu_ranking = pygame_menu.Menu(
        title="Ranking - Top 10",
        width=LARGURA_TELA * 0.8,
        height=ALTURA_TELA * 0.9,
        theme=pygame_menu.themes.THEME_DARK
    )
    frame_ranking = menu_ranking.add.frame_v(width=LARGURA_TELA * 0.7, height=ALTURA_TELA * 0.7)
    frame_ranking._relax = True

    menu_ranking.add.button("Voltar", pygame_menu.events.BACK)

    def atualizar_conteudo_do_menu(current_menu=None, next_menu=None):
        for widget in list(frame_ranking.get_widgets()):
            menu_ranking.remove_widget(widget)
        
        ranking_manager = RankingManager()
        ranking_manager.carregar_de_arquivo(ARQUIVO_HIGH_SCORES)

        if not ranking_manager.jogadores:
            frame_ranking.pack(menu_ranking.add.label("Nenhum recorde ainda!", font_size=20))
        else:
            for i, jogador in enumerate(ranking_manager.jogadores, 1):
                frame_ranking.pack(menu_ranking.add.label(f"{i}. {jogador.nome}: {jogador.pontuacao} pts"))

    menu_ranking.set_onbeforeopen(atualizar_conteudo_do_menu)

    atualizar_conteudo_do_menu

    return menu_ranking




def criar_menu_configuracoes(gerenciador_som: GerenciadorSom) -> pygame_menu.Menu:
    """Cria e retorna o menu de configurações."""
    menu_cfg = pygame_menu.Menu(
        title="Configurações",
        width=LARGURA_TELA * 0.7,
        height=ALTURA_TELA * 0.6,
        theme=pygame_menu.themes.THEME_DARK
    )
    menu_cfg.add.label("Volume da Música:")
    menu_cfg.add.range_slider("", default=int(gerenciador_som.volume_musica * 100), range_values=(0, 100), increment=1, onchange=gerenciador_som.set_volume_musica)
    menu_cfg.add.label("Volume dos Efeitos Sonoros (SFX):")
    menu_cfg.add.range_slider("", default=int(gerenciador_som.volume_sfx * 100), range_values=(0, 100), increment=1, onchange=gerenciador_som.set_volume_sfx)
    menu_cfg.add.button("Voltar", pygame_menu.events.BACK)
    return menu_cfg


def verificar_save_valido():
    if not os.path.exists(ARQUIVO_SAVE_GAME): return False
    try:
        with open(ARQUIVO_SAVE_GAME, 'r') as f: estado = json.load(f)
        return not estado.get("game_over", False) and bool(estado.get("nave"))
    except (json.JSONDecodeError, IOError): return False


botao_continuar_ref = None

def atualizar_botao_continuar(menu_alvo):
    global botao_continuar_ref
    if botao_continuar_ref and menu_alvo:
        eh_valido = verificar_save_valido()
        botao_continuar_ref.set_attribute("readonly", not eh_valido)
        botao_continuar_ref.set_title("Continuar Jogo" if eh_valido else "Continuar Jogo (Vazio)")
        botao_continuar_ref.update_font({'color': BRANCO if eh_valido else (100, 100, 100)})
        if eh_valido:
            if not botao_continuar_ref.is_visible(): botao_continuar_ref.show()
        else:
            if not botao_continuar_ref.is_visible(): botao_continuar_ref.show()


# --- Função Principal ---
def main():
    pygame.init()
    pygame.mixer.init()
    tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
    pygame.display.set_caption(TITULO_JOGO)
    clock = pygame.time.Clock()
    gerenciador_som = GerenciadorSom()

    tema_menu = pygame_menu.themes.THEME_DARK.copy()
    tema_menu.widget_font_size = 24
    tema_menu.title_font_size = 36
    tema_menu.background_color = (40, 40, 60)

    menu_principal = pygame_menu.Menu(
        title="Asteroids UFV-CRP",
        width=LARGURA_TELA, height=ALTURA_TELA,
        theme=tema_menu
    )


    # 1. Crie os sub-menus ANTES de adicionar os botões
    menu_ranking = criar_menu_ranking()
    menu_configuracoes = criar_menu_configuracoes(gerenciador_som)

    # 2. Adicione os botões, passando os objetos de menu como ação
    global botao_continuar_ref
    menu_principal.add.button('Novo Jogo', lambda: iniciar_jogo_callback(tela, clock, gerenciador_som, menu_principal, carregar_save=False))
    botao_continuar_ref = menu_principal.add.button('Continuar Jogo', lambda: iniciar_jogo_callback(tela, clock, gerenciador_som, menu_principal, carregar_save=True))
    
    menu_principal.add.button('Ranking', menu_ranking)
    menu_principal.add.button('Configurações', menu_configuracoes)

    menu_principal.add.button('Sair', pygame_menu.events.EXIT)
    
    def hook_para_onbefore():
        atualizar_botao_continuar(menu_principal)

    menu_principal.set_onbeforeopen(hook_para_onbefore)
    atualizar_botao_continuar(menu_principal) 

    gerenciador_som.tocar_musica_fundo('menu')
    
    try:
        menu_principal.mainloop(tela)
    except Exception as e:
        print(f"Ocorreu um erro fatal no loop principal: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        print("Jogo encerrado.")


if __name__ == '__main__':
    main()