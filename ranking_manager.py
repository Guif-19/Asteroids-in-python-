import json
import os
from jogador_ranking import JogadorRanking

class RankingManager:
    def __init__(self):
        self.jogadores = []

    def carregar_de_arquivo(self, arquivo: str):
        try:
            with open(arquivo, "r") as f:
                dados = json.load(f)
            self.jogadores = [JogadorRanking.from_dict(d) for d in dados]
        except (FileNotFoundError, json.JSONDecodeError):
            self.jogadores = []

    def adicionar_jogador(self, jogador: JogadorRanking):
        self.jogadores.append(jogador)
        self.jogadores.sort(key=lambda j: j.pontuacao, reverse=True)
        self.jogadores = self.jogadores[:10]

    def salvar_em_arquivo(self, arquivo: str):
        try:
            with open(arquivo, "w") as f:
                json.dump([j.to_dict() for j in self.jogadores], f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar ranking: {e}")