import math

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
VELOCIDADE_ROTACAO_NAVE = 5
ACELERACAO_NAVE = 0.2
FRICCAO_NAVE = 0.99
COOLDOWN_TIRO = 300  # ms
VIDAS_INICIAIS = 1
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
CHANCE_SPAWN_OVNI = 0.001
VELOCIDADE_OVNI = 5
COOLDOWN_TIRO_OVNI_MS = 1500
TEMPO_OVNI_ANTES_ATIRAR_SEGUNDOS = 3
MAX_OVNIS_TELA = 2
PONTOS_OVNI = 1000
VELOCIDADE_PROJETIL_OVNI = 5
CHANCE_SPAWN_OVNI_X = 0.001
COR_PROJETIL_OVNI_X = (255, 0, 255)  # Rosa
CHANCE_SPAWN_OVNI_CRUZ = 0.001
COR_PROJETIL_OVNI_CRUZ = (0, 255, 0)  # Verde

# Nave Fantasma
CHANCE_SPAWN_FANTASMA = 0.001
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


# Assets de som
SOM_TIRO = "assets/sounds/laser1.mp3"
SOM_EXPLOSAO_ASTEROIDE = "assets/sounds/explosao_asteroide.mp3"
SOM_EXPLOSAO_NAVE = "assets/sounds/explode.mp3"
MUSICA_FUNDO_JOGO = "assets/sounds/musica_fase_1.mp3"
MUSICA_FUNDO_MENU = "assets/sounds/musica_menu.mp3"
SOM_OVNI_MOVENDO = "assets/sounds/ovnimove.wav"
SOM_OVNI_TIRO = "assets/sounds/ovnishot.wav"
SOM_FANTASMA_INVISIVEL = "assets/sounds/invisibleufo.mp3"


# Power-up Tiro Triplo
DURACAO_TIRO_TRIPLO_SEGUNDOS = 15
ANGULO_TIRO_TRIPLO_GRAUS = 20

# Arquivos
ARQUIVO_HIGH_SCORES = "high_scores.json"
ARQUIVO_SAVE_GAME = "savegame.json"


# Sprite 
IMAGEM_NAVE = "assets/images/pixel_ship_blue_small.png"
IMAGEM_NAVE_TRIPLO = "assets/images/pixel_ship_blue_small.png"
IMAGEM_PROJETIL_JOGADOR = "assets/images/pixel_laser_small_blue.png"

IMAGEM_ASTEROIDE_GRANDE = "assets/images/pixel_asteroid.png"
IMAGEM_ASTEROIDE_MEDIO = "assets/images/pixel_asteroid.png" # Vamos reutilizar e diminuir a escala
IMAGEM_ASTEROIDE_PEQUENO = "assets/images/asteroid_tiny.png"

IMAGEM_OVNI_X = "assets/images/pixel_ship_red_small_2.png"
IMAGEM_OVNI_CRUZ = "assets/images/pixel_ship_green_small_2.png"
IMAGEM_PROJETIL_OVNI_X = "assets/images/pixel_laser_small_red.png"
IMAGEM_PROJETIL_OVNI_CRUZ = "assets/images/pixel_laser_small_red.png" # Use a cópia se for diferente

IMAGEM_FANTASMA = "assets/images/pixel_shape3_blue.png"
IMAGEM_LASER_FANTASMA = "assets/images/horizontal_bar_red.png" # Usando a barra como laser

