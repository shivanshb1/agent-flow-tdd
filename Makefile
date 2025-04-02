# Variáveis de configuração
PYTHON := python3
VENV_DIR := .venv
VENV_BIN := $(VENV_DIR)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip

# Configurações do projeto
PROJECT_NAME := agent-flow-tdd
VERSION := $(shell cat VERSION || echo "0.1.0")
DIST_DIR := dist
BUILD_DIR := build

.PHONY: all install clean create-venv pack deploy undeploy help build publish version update-changelog test test-cli test-e2e cli cli-feature cli-status cli-mcp

help:  ## Mostra esta mensagem de ajuda
	@echo "Agent Flow TDD - Framework para automação de fluxo de features TDD"
	@echo ""
	@echo "Comandos disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

all: clean create-venv install test  ## Executa limpeza, cria venv, instala dependências e roda testes

create-venv:  ## Cria ambiente virtual Python
	@echo "🔧 Criando ambiente virtual..."
	@rm -rf $(VENV_DIR)
	@$(PYTHON) -m venv $(VENV_DIR)
	@$(VENV_PIP) install --upgrade pip
	@echo "✅ Ambiente virtual criado em $(VENV_DIR)"

install: create-venv  ## Instala dependências do projeto
	@echo "📦 Instalando dependências..."
	@$(VENV_PIP) install -e .
	@echo "✅ Dependências instaladas"

clean:  ## Remove arquivos temporários e caches
	@echo "🧹 Limpando arquivos temporários..."
	@rm -rf $(BUILD_DIR) $(DIST_DIR) .pytest_cache .coverage htmlcov .eggs *.egg-info
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@echo "✅ Limpeza concluída"

build: clean  ## Compila o projeto
	@echo "🏗️ Compilando projeto..."
	@$(VENV_PYTHON) setup.py build
	@echo "✅ Build concluído"

pack: build  ## Cria pacote para distribuição
	@echo "📦 Criando pacote..."
	@$(VENV_PYTHON) setup.py sdist bdist_wheel
	@echo "✅ Pacote criado em $(DIST_DIR)"

publish: pack  ## Publica pacote no PyPI
	@echo "🚀 Publicando pacote..."
	@$(VENV_BIN)/twine upload $(DIST_DIR)/*
	@echo "✅ Pacote publicado"

version:  ## Mostra a versão atual do projeto
	@echo "📋 Versão atual: $(VERSION)"

update-changelog:  ## Atualiza o CHANGELOG.md
	@echo "📝 Atualizando CHANGELOG.md..."
	@$(VENV_PYTHON) scripts/update_changelog.py
	@echo "✅ CHANGELOG.md atualizado"

deploy: pack  ## Realiza deploy do projeto
	@echo "🚀 Iniciando deploy..."
	@$(VENV_PYTHON) scripts/deploy.py
	@echo "✅ Deploy concluído"

undeploy:  ## Remove deploy do projeto
	@echo "🔄 Removendo deploy..."
	@$(VENV_PYTHON) scripts/undeploy.py
	@echo "✅ Undeploy concluído"

test: ## Executa todos os testes
	@echo "🧪 Executando testes..."
	@$(VENV_BIN)/pytest -v src/tests/
	@echo "✅ Testes concluídos"

test-cli: ## Executa testes específicos do CLI
	@echo "🧪 Executando testes do CLI..."
	@$(VENV_BIN)/pytest -v src/tests/test_cli.py
	@echo "✅ Testes do CLI concluídos"

test-e2e: ## Executa testes end-to-end
	@echo "🧪 Executando testes E2E..."
	@$(VENV_BIN)/pytest -v src/tests/e2e/
	@echo "✅ Testes E2E concluídos"

cli-feature: ## Executa o CLI no modo feature
	@echo "🖥️ Iniciando CLI no modo feature..."
	@$(VENV_PYTHON) -m src.cli feature "Descreva sua feature aqui"

cli-status: ## Executa o CLI no modo status
	@echo "🖥️ Iniciando CLI no modo status..."
	@$(VENV_PYTHON) -m src.cli status

cli-mcp: ## Executa o CLI no modo MCP
	@echo "🖥️ Iniciando CLI no modo MCP..."
	@$(VENV_PYTHON) -m src.cli mcp

cli: cli-feature ## Alias para cli-feature (comando padrão) 