import json
import os
from jogador_ranking import JogadorRanking
from typing import List
from config import ARQUIVO_HIGH_SCORES

class RankingManager:
    def __init__(self):
        self.__jogadores: List[JogadorRanking] = []

    def get_jogadores(self) -> List[JogadorRanking]:
        return self.__jogadores.copy()

    def set_jogadores(self, nova_lista: List[JogadorRanking]) -> None:
        self.__jogadores = nova_lista

    def carregar_scores(self):
        """Carrega os scores do arquivo JSON padrão."""
        try:
            with open(ARQUIVO_HIGH_SCORES, "r") as f:
                dados = json.load(f)
            # Usa o novo setter para definir a lista
            self.set_jogadores([JogadorRanking.from_dict(d) for d in dados])
        except (FileNotFoundError, json.JSONDecodeError):
            self.set_jogadores([]) # Usa o setter para esvaziar a lista

    def adicionar_score(self, novo_recorde: JogadorRanking):
        """Adiciona um novo score à lista, ordena e mantém apenas o Top 10."""
        # Pega a lista atual com o getter
        jogadores_atuais = self.get_jogadores()
        jogadores_atuais.append(novo_recorde)
        jogadores_atuais.sort(key=lambda j: j.get_pontuacao(), reverse=True)
        # Define a nova lista ordenada e cortada com o setter
        self.set_jogadores(jogadores_atuais[:10])

    def salvar_scores(self):
        """Salva a lista de scores atual no arquivo JSON padrão."""
        with open(ARQUIVO_HIGH_SCORES, "w") as f:
            json.dump([j.to_dict() for j in self.get_jogadores()], f, indent=4)

