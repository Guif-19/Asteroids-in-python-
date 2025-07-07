import os
import pathlib

# Pega o diretório onde este arquivo (config.py) está
DIRETORIO_ATUAL = pathlib.Path(__file__).parent.resolve()
# Monta o caminho para a pasta 'assets'
DIRETORIO_ASSETS = os.path.join(DIRETORIO_ATUAL, "assets")

# Cores
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
VERMELHO = (255, 0, 0)
VERDE = (0, 255, 0)
AZUL = (0, 0, 255)
CINZA_CLARO = (200, 200, 200)
COR_ESTRELA = BRANCO
COR_OVNI = AZUL
COR_PROJETIL_OVNI = VERMELHO

# Configurações da Tela
LARGURA_TELA = 800
ALTURA_TELA = 600
FPS = 60
TITULO_JOGO = "Asteroids UFV-CRP"

# Nave
VELOCIDADE_ROTACAO_NAVE = 3
ACELERACAO_NAVE = 0.2
FRICCAO_NAVE = 0.99
COOLDOWN_TIRO = 200  # ms
VIDAS_INICIAIS = 5
TEMPO_INVENCIBILIDADE_SEGUNDOS = 2


# Projétil
VELOCIDADE_PROJETIL = 10
DURACAO_PROJETIL = 60  # frames

# Asteroide
VEL_MIN_ASTEROIDE = 0.5
VEL_MAX_ASTEROIDE = 2.0
ASTEROIDES_INICIAIS = 4
PONTOS_ASTEROIDE_GRANDE = 20
PONTOS_ASTEROIDE_MEDIO = 50
PONTOS_ASTEROIDE_PEQUENO = 100

# OVNI
CHANCE_SPAWN_OVNI = 0.0001
VELOCIDADE_OVNI = 4
COOLDOWN_TIRO_OVNI_MS = 1500
TEMPO_OVNI_ANTES_ATIRAR_SEGUNDOS = 10
MAX_OVNIS_TELA = 2
PONTOS_OVNI = 1000
VELOCIDADE_PROJETIL_OVNI = 5
CHANCE_SPAWN_OVNI_X = 0.001
COR_PROJETIL_OVNI_X = (255, 0, 255)  # Rosa
CHANCE_SPAWN_OVNI_CRUZ = 0.001
COR_PROJETIL_OVNI_CRUZ = (0, 255, 0)  # Verde

# Nave Fantasma
CHANCE_SPAWN_FANTASMA = 1
MAX_FANTASMAS_TELA = 1
PONTOS_FANTASMA = 500
VELOCIDADE_LASER_FANTASMA = 12


# Timings em milissegundos (1000ms = 1s)
DURACAO_FANTASMA_CARREGANDO_MS = 2500
DURACAO_FANTASMA_INVISIVEL_MS = 4000
DURACAO_LASER_FANTASMA_MS = 250     
COR_FANTASMA = (180, 0, 255)       # Roxo
COR_FANTASMA_CARREGANDO = BRANCO   # Cor do indicador de carga
COR_FANTASMA_LASER = (255, 0, 220) # Rosa choque


# Fundo Estrelado
NUM_ESTRELAS_LENTAS = 50
NUM_ESTRELAS_RAPIDAS = 30
VELOCIDADE_ESTRELAS_LENTA = 1
VELOCIDADE_ESTRELAS_RAPIDA = 3

# Sons
VOLUME_MUSICA_PADRAO = 0.5
VOLUME_SFX_PADRAO = 0.7


# Power-up Tiro Triplo
DURACAO_TIRO_TRIPLO_SEGUNDOS = 15
ANGULO_TIRO_TRIPLO_GRAUS = 20

# Arquivos
ARQUIVO_HIGH_SCORES = "high_scores.json"
ARQUIVO_SAVE_GAME = "savegame.json"


# --- Assets (usando os caminhos absolutos para a estrutura assets/images e assets/sounds) ---
# Sons
SOM_TIRO = os.path.join(DIRETORIO_ASSETS, "sounds", "laser1.mp3")
SOM_EXPLOSAO_ASTEROIDE = os.path.join(DIRETORIO_ASSETS, "sounds", "explosao_asteroide.mp3")
SOM_EXPLOSAO_NAVE = os.path.join(DIRETORIO_ASSETS, "sounds", "explode.mp3")
MUSICA_FUNDO_JOGO = os.path.join(DIRETORIO_ASSETS, "sounds", "musica_fase_1.mp3")
MUSICA_FUNDO_MENU = os.path.join(DIRETORIO_ASSETS, "sounds", "musica_menu.mp3")
SOM_OVNI_MOVENDO = os.path.join(DIRETORIO_ASSETS, "sounds", "ovnimove.wav")
SOM_OVNI_TIRO = os.path.join(DIRETORIO_ASSETS, "sounds", "ovnishot.wav")
SOM_FANTASMA_INVISIVEL = os.path.join(DIRETORIO_ASSETS, "sounds", "invisibleufo.mp3")

# Imagens
IMAGEM_NAVE = os.path.join(DIRETORIO_ASSETS, "images", "pixel_ship_blue.png")
IMAGEM_ASTEROIDE_GRANDE = os.path.join(DIRETORIO_ASSETS, "images", "pixel_asteroid.png")
IMAGEM_ASTEROIDE_MEDIO = os.path.join(DIRETORIO_ASSETS, "images", "pixel_asteroid - medium.png")
IMAGEM_ASTEROIDE_PEQUENO = os.path.join(DIRETORIO_ASSETS, "images", "asteroid_tiny.png")
IMAGEM_OVNI_X = os.path.join(DIRETORIO_ASSETS, "images", "pixel_ship_red_small_2.png")
IMAGEM_OVNI_CRUZ = os.path.join(DIRETORIO_ASSETS, "images", "pixel_ship_green_small_2.png")
IMAGEM_PROJETIL_JOGADOR = os.path.join(DIRETORIO_ASSETS, "images", "pixel_laser_small_blue.png")
IMAGEM_PROJETIL_OVNI_X = os.path.join(DIRETORIO_ASSETS, "images", "pixel_laser_small_red.png")
IMAGEM_PROJETIL_OVNI_CRUZ = os.path.join(DIRETORIO_ASSETS, "images", "pixel_laser_small_red.png")
IMAGEM_FANTASMA = os.path.join(DIRETORIO_ASSETS, "images", "pixel_station_purple.png")
IMAGEM_LASER_FANTASMA = os.path.join(DIRETORIO_ASSETS, "images", "pixel_laser_small_red.png")


