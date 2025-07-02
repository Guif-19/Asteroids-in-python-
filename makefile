PYTHON = python3
PIP = $(PYTHON) -m pip

 .DEFAULT_GOAL := run

.PHONY: install run clean help

install:
	@echo "--- Instalando dependências ---"
	$(PIP) install -r requirements.txt
	@echo "--- Dependências instaladas com sucesso ---"

run:
	@echo "--- Iniciando o jogo Asteroids ---"
	$(PYTHON) main.py

clean:
	@echo "--- Limpando arquivos temporários e save... ---"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -r {} +
	rm -f savegame.json
	@echo "--- Limpeza concluída ---"
	
help:
	@echo "Comandos disponíveis:"
	@echo "  make install    -> Instala as bibliotecas Python necessárias."
	@echo "  make run        -> Executa o jogo (ação padrão)."
	@echo "  make            -> Executa o jogo (atalho para 'make run')."
	@echo "  make clean      -> Remove arquivos temporários e o save do jogo."
	@echo "  make help       -> Mostra esta mensagem de ajuda."
