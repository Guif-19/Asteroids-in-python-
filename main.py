import pygame
import pygame_menu
import json
import os
from config import *
from gerenciador_jogo import GerenciadorJogo, EstadoJogoLoop
from entidades import CLASSE_MAP
from ranking_manager import RankingManager
from jogador_ranking import JogadorRanking


class GerenciadorSom:
    def __init__(self):
        self.volume_musica = VOLUME_MUSICA_PADRAO
        self.volume_sfx = VOLUME_SFX_PADRAO
        print("DEBUG: GerenciadorSom __init__ chamado.")
        print("Gerenciador de Som (placeholder) inicializado.")

    def set_volume_musica(self, volume, *args):
        self.volume_musica = max(0.0, min(1.0, volume))
        print(f"Volume da música definido para: {self.volume_musica:.2f}")

    def set_volume_sfx(self, volume, *args):
        self.volume_sfx = max(0.0, min(1.0, volume))
        print(f"Volume dos SFX definido para: {self.volume_sfx:.2f}")


def coletar_nome_jogador_e_salvar_score(tela_coleta, pontuacao_final_coleta, menu_que_chamou, clock):
    nome_jogador_var = ["JOGADOR"]
    tema_input = pygame_menu.themes.THEME_DARK.copy()
    tema_input.widget_font_size = 20
    tema_input.title_font_size = 24

    _menu_input_nome = pygame_menu.Menu(
        title=f"FIM DE JOGO! Pontuação: {pontuacao_final_coleta}",
        width=int(LARGURA_TELA * 0.7),
        height=int(ALTURA_TELA * 0.5),
        theme=tema_input,
        onclose=pygame_menu.events.NONE
    )

    _menu_input_nome.add.label("Digite seu nome (3-10 caracteres):")
    input_field = _menu_input_nome.add.text_input("", default="JOGADOR", maxchar=10,
                                                 onchange=lambda val: nome_jogador_var.__setitem__(0, val))

    def _fechar_este_menu_e_reabilitar_anterior():
        if _menu_input_nome.is_enabled():
            _menu_input_nome.disable()
        deve_fechar_menu_input_flag[0] = True
        if not menu_que_chamou.is_enabled():
            menu_que_chamou.enable()
        atualizar_botao_continuar(menu_que_chamou)

    def acao_salvar_e_voltar():
        nome = nome_jogador_var[0].strip().upper()
        if len(nome) < 3 or len(nome) > 10:
            input_field.set_error("Nome deve ter entre 3 e 10 caracteres.")
            return
        ranking_manager = RankingManager()
        ranking_manager.carregar_de_arquivo(ARQUIVO_HIGH_SCORES)
        novo_jogador = JogadorRanking(nome, pontuacao_final_coleta)
        ranking_manager.adicionar_jogador(novo_jogador)
        ranking_manager.salvar_em_arquivo(ARQUIVO_HIGH_SCORES)
        _fechar_este_menu_e_reabilitar_anterior()

    def acao_voltar_sem_salvar():
        _fechar_este_menu_e_reabilitar_anterior()

    _menu_input_nome.add.button("Salvar Score e Voltar", acao_salvar_e_voltar)
    _menu_input_nome.add.button("Voltar Sem Salvar", acao_voltar_sem_salvar)

    deve_fechar_menu_input_flag = [False]

    if menu_que_chamou.is_enabled():
        menu_que_chamou.disable()
    _menu_input_nome.mainloop(tela_coleta)

    if not menu_que_chamou.is_enabled():
        menu_que_chamou.enable()
    atualizar_botao_continuar(menu_que_chamou)


def iniciar_jogo_callback(tela_jogo, clock_jogo, gerenciador_som_jogo, menu_que_chamou, carregar_save=False):
    print(f"Iniciando jogo... Carregar Save: {carregar_save}")
    menu_que_chamou.disable()
    jogo = GerenciadorJogo(tela_jogo, clock_jogo, gerenciador_som_jogo)
    if carregar_save:
        if not jogo.carregar_estado_jogo():
            print("Não foi possível carregar o save, iniciando novo jogo.")
    else:
        print("Iniciando NOVO jogo...")
        jogo.reiniciar_jogo_completo()

    retorno_do_jogo, pontuacao_final_do_jogo = jogo.loop_principal()

    print(f"Jogo encerrado. Retorno: {retorno_do_jogo}, Pontuação: {pontuacao_final_do_jogo}")

    if retorno_do_jogo == EstadoJogoLoop.VOLTAR_AO_MENU_GAME_OVER:
        try:
            if os.path.exists(ARQUIVO_SAVE_GAME):
                os.remove(ARQUIVO_SAVE_GAME)
        except Exception as e:
            print(f"Aviso: não foi possível remover o save antigo: {e}")

        if pontuacao_final_do_jogo >= 0:
            coletar_nome_jogador_e_salvar_score(tela_jogo, pontuacao_final_do_jogo, menu_que_chamou, clock_jogo)
        else:
            menu_que_chamou.enable()
            atualizar_botao_continuar(menu_que_chamou)

    elif retorno_do_jogo in [EstadoJogoLoop.VOLTAR_AO_MENU_COM_SAVE, EstadoJogoLoop.VOLTAR_AO_MENU_SEM_SALVAR]:
        menu_que_chamou.enable()
        atualizar_botao_continuar(menu_que_chamou)
    else:
        menu_que_chamou.enable()
        atualizar_botao_continuar(menu_que_chamou)


def mostrar_ranking_callback(menu_que_chamou, tela_ranking):
    print("DEBUG: Exibindo ranking.")
    menu_ranking = pygame_menu.Menu(
        title="Ranking - Top 10",
        width=LARGURA_TELA * 0.8,
        height=ALTURA_TELA * 0.9,
        theme=pygame_menu.themes.THEME_DARK,
        onclose=pygame_menu.events.BACK
    )
    ranking_manager = RankingManager()
    ranking_manager.carregar_de_arquivo(ARQUIVO_HIGH_SCORES)

    if not ranking_manager.jogadores:
        menu_ranking.add.label("Nenhum recorde ainda!", font_size=20)
    else:
        for i, jogador in enumerate(ranking_manager.jogadores[:10], 1):
            menu_ranking.add.label(f"{i}. {jogador.nome}: {jogador.pontuacao} pts")

    menu_ranking.add.button("Voltar", pygame_menu.events.BACK)

    menu_que_chamou.disable()
    menu_ranking.mainloop(tela_ranking)

    if not menu_que_chamou.is_enabled():
        menu_que_chamou.enable()
    atualizar_botao_continuar(menu_que_chamou)


def menu_configuracoes_callback(menu_que_chamou, gerenciador_som_cfg, tela_cfg):
    print("DEBUG: Abrindo menu de configurações.")
    menu_cfg = pygame_menu.Menu(
        title="Configurações de Volume",
        width=LARGURA_TELA * 0.7,
        height=ALTURA_TELA * 0.6,
        theme=pygame_menu.themes.THEME_DARK,
        onclose=pygame_menu.events.BACK
    )

    menu_cfg.add.label("Volume da Música:")
    menu_cfg.add.range_slider("", default=int(gerenciador_som_cfg.volume_musica * 100),
                              range_values=(0, 100), increment=1,
                              onchange=lambda val: gerenciador_som_cfg.set_volume_musica(val / 100.0))

    menu_cfg.add.label("Volume dos Efeitos Sonoros (SFX):")
    menu_cfg.add.range_slider("", default=int(gerenciador_som_cfg.volume_sfx * 100),
                              range_values=(0, 100), increment=1,
                              onchange=lambda val: gerenciador_som_cfg.set_volume_sfx(val / 100.0))

    menu_cfg.add.button("Voltar", pygame_menu.events.BACK)

    menu_que_chamou.disable()
    menu_cfg.mainloop(tela_cfg)

    if not menu_que_chamou.is_enabled():
        menu_que_chamou.enable()
    atualizar_botao_continuar(menu_que_chamou)


def verificar_save_valido():
    if not os.path.exists(ARQUIVO_SAVE_GAME):
        return False
    try:
        with open(ARQUIVO_SAVE_GAME, 'r') as f:
            estado = json.load(f)
        return not estado.get("game_over", False) and bool(estado.get("nave"))
    except (json.JSONDecodeError, IOError):
        return False


botao_continuar_ref = None


def atualizar_botao_continuar(menu_alvo):
    global botao_continuar_ref
    if botao_continuar_ref and menu_alvo:
        eh_valido = verificar_save_valido()
        botao_continuar_ref.set_attribute("readonly", not eh_valido)
        botao_continuar_ref.set_title("Continuar Jogo" if eh_valido else "Continuar Jogo (Vazio)")
        botao_continuar_ref.update_font({'color': BRANCO if eh_valido else (100, 100, 100)})
        if eh_valido and not botao_continuar_ref.is_visible():
            botao_continuar_ref.show()
        elif not eh_valido and not botao_continuar_ref.is_visible():
            botao_continuar_ref.show()


def main():
    print("DEBUG: Função main() iniciada.")
    pygame.init()
    tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
    pygame.display.set_caption(TITULO_JOGO)
    clock = pygame.time.Clock()
    print("DEBUG: Tela criada.")

    gerenciador_som = GerenciadorSom()
    print("DEBUG: GerenciadorSom instanciado.")

    tema_menu = pygame_menu.themes.THEME_DARK.copy()
    tema_menu.widget_font_size = 24
    tema_menu.title_font_size = 36
    tema_menu.background_color = (40, 40, 60)

    menu_principal = pygame_menu.Menu(
        title="Asteroids UFV-CRP",
        width=LARGURA_TELA,
        height=ALTURA_TELA,
        theme=tema_menu
    )

    global botao_continuar_ref
    menu_principal.add.button('Novo Jogo', lambda: iniciar_jogo_callback(tela, clock, gerenciador_som, menu_principal, carregar_save=False))
    botao_continuar_ref = menu_principal.add.button('Continuar Jogo', lambda: iniciar_jogo_callback(tela, clock, gerenciador_som, menu_principal, carregar_save=True))
    menu_principal.add.button('Ranking', lambda: mostrar_ranking_callback(menu_principal, tela))
    menu_principal.add.button('Configurações', lambda: menu_configuracoes_callback(menu_principal, gerenciador_som, tela))
    menu_principal.add.button('Sair', pygame_menu.events.EXIT)

    def hook_para_onbefore():
        atualizar_botao_continuar(menu_principal)

    menu_principal.set_onbeforeopen(hook_para_onbefore)
    atualizar_botao_continuar(menu_principal)

    print("DEBUG: Botões adicionados ao menu_principal.")

    while True:
        eventos = pygame.event.get()
        for evento in eventos:
            if evento.type == pygame.QUIT:
                pygame.quit()
                return

        menu_principal.mainloop(tela)

        pygame.quit()


if __name__ == '__main__':
    main()