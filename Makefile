# Makefile para o projeto prompt-tdd

.PHONY: install test run clean

# Configuração do ambiente virtual
VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# Instalação e setup
install:
	@echo "🔧 Instalando dependências..."
	python -m venv $(VENV)
	$(PIP) install -e .
	@echo "✅ Instalação concluída!"

# Testes
test:
	@echo "🧪 Executando testes..."
	$(PYTHON) -m pytest src/tests/ -v
	@echo "✅ Testes concluídos!"

# Execução do CLI
run:
	@echo "🖥️ Executando CLI..."
	$(PYTHON) -m src.cli $(if $(mode),--mode $(mode),) $(if $(format),--format $(format),) "$(prompt-tdd)"

# Limpeza
clean:
	@echo "🧹 Limpando arquivos temporários..."
	rm -rf $(VENV) *.egg-info dist build .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
	@echo "✨ Limpeza concluída!"

# Permite argumentos extras para o comando run
%:
	@: 