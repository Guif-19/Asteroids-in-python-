import json
import os
from jogador_ranking import JogadorRanking
from typing import List

class RankingManager:
    def __init__(self):
        self.__jogadores: List[JogadorRanking] = []

    def get_jogadores(self) -> List[JogadorRanking]:
        return self.__jogadores.copy()

    def carregar_de_arquivo(self, arquivo: str):
        try:
            with open(arquivo, "r") as f:
                dados = json.load(f)
            self.__jogadores = [JogadorRanking.from_dict(d) for d in dados]
        except (FileNotFoundError, json.JSONDecodeError):
            self.__jogadores = []

    def adicionar_jogador(self, jogador: JogadorRanking):
        self.__jogadores.append(jogador)
        self.__jogadores.sort(key=lambda j: j.get_pontuacao(), reverse=True)
        self.__jogadores = self.__jogadores[:10]

    def salvar_em_arquivo(self, arquivo: str):
        with open(arquivo, "w") as f:
            json.dump([j.to_dict() for j in self.__jogadores], f, indent=4)