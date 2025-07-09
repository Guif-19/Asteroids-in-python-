class JogadorRanking:
    def __init__(self, nome: str, pontuacao: int):
        self.__nome = nome
        self.__pontuacao = pontuacao

    def get_nome(self) -> str: return self.__nome
    def get_pontuacao(self) -> int: return self.__pontuacao

    def set_nome(self, novo_nome: str) -> None:
        self.__nome = novo_nome

    def set_pontuacao(self, nova_pontuacao: int) -> None:

        self.__pontuacao = nova_pontuacao


    def to_dict(self) -> dict:
        return {"nome": self.__nome, "pontuacao": self.__pontuacao}

    @staticmethod
    def from_dict(data):
        return JogadorRanking(data["nome"], data["pontuacao"])
