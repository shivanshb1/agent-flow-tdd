"""
Testes para o módulo CLI.
"""
import json
from unittest.mock import Mock, patch, MagicMock
import os

import pytest
from typer.testing import CliRunner

from src.cli import app, mcp
from src.core.utils import ModelManager, get_env_status, validate_env
from src.app import AgentOrchestrator

# Setup
runner = CliRunner()

# Mock do SDK MCP
class MockMessage:
    def __init__(self, content, metadata):
        self.content = content
        self.metadata = metadata

class MockResponse:
    def __init__(self, content, metadata):
        self.content = content
        self.metadata = metadata

class MockMCPHandler:
    def __init__(self):
        self.orchestrator = None
    
    def initialize(self, api_key=None):
        pass
    
    def handle_message(self, message):
        pass
    
    def run(self):
        pass

@pytest.fixture
def mock_model_manager():
    """Mock do ModelManager."""
    mock = MagicMock(spec=ModelManager)
    mock.get_available_models.return_value = ["gpt-4"]
    mock.generate.return_value = "Resposta mockada"
    return mock

@pytest.fixture
def mock_orchestrator(mock_model_manager):
    """Mock do AgentOrchestrator."""
    mock = MagicMock(spec=AgentOrchestrator)
    mock.model_manager = mock_model_manager
    mock.handle_input.return_value = {"feature": "Login"}
    mock.visualizer = MagicMock()
    mock.visualizer.visualize.return_value = "# Markdown Output"
    return mock

@pytest.fixture
def mock_validate_env():
    """Mock para validate_env."""
    with patch("src.cli.validate_env", autospec=True) as mock:
        yield mock

@pytest.fixture
def mock_get_env_status():
    """Mock para get_env_status."""
    with patch("src.cli.get_env_status") as mock:
        mock.return_value = {
            "required": {"OPENAI_KEY": True},
            "optional": {"ELEVATION_MODEL": False}
        }
        yield mock

@pytest.fixture
def mock_mcp_sdk():
    """Mock do SDK MCP."""
    with patch("src.mcp.BaseMCPHandler") as mock_base_handler:
        mock_handler = MagicMock()
        mock_handler.run.side_effect = lambda: None  # Não faz nada
        mock_base_handler.return_value = mock_handler
        yield mock_base_handler

def test_feature_command_success(mock_model_manager, mock_orchestrator, mock_validate_env):
    """Testa o comando feature com sucesso."""
    # Setup
    mock_orchestrator.handle_input.return_value = {"feature": "Login", "tests": ["test1"]}

    with patch("src.cli.get_orchestrator", return_value=mock_orchestrator):
        # Execução
        result = runner.invoke(app, ["feature", "Criar sistema de login"])

        # Verificações
        assert result.exit_code == 0
        mock_validate_env.assert_called_once()
        mock_model_manager.configure.assert_called_once_with(
            model="gpt-3.5-turbo",
            temperature=0.7
        )

def test_feature_command_markdown_output(mock_model_manager, mock_orchestrator, mock_validate_env):
    """Testa o comando feature com saída em markdown."""
    # Setup
    mock_orchestrator.handle_input.return_value = {"feature": "Login"}

    with patch("src.cli.get_orchestrator", return_value=mock_orchestrator):
        # Execução
        result = runner.invoke(app, ["feature", "Criar login", "--format", "markdown"])

        # Verificações
        assert result.exit_code == 0
        mock_orchestrator.visualizer.visualize.assert_called_once()

def test_feature_command_error(mock_model_manager, mock_orchestrator, mock_validate_env):
    """Testa o comando feature com erro."""
    # Setup
    mock_validate_env.side_effect = Exception("Erro de validação")

    # Execução
    result = runner.invoke(app, ["feature", "Criar login"], catch_exceptions=False)

    # Verificações
    assert result.exit_code == 1  # Erro deve retornar código 1
    assert "Erro ao processar feature" in result.stdout

def test_status_command_success(mock_model_manager, mock_get_env_status):
    """Testa o comando status com sucesso."""
    # Setup
    mock_model_manager.get_available_models.return_value = ["gpt-4", "gpt-3.5"]

    with patch("src.cli.ModelManager", return_value=mock_model_manager):
        # Execução
        result = runner.invoke(app, ["status"])

        # Verificações
        assert result.exit_code == 0
        mock_get_env_status.assert_called_once()
        mock_model_manager.get_available_models.assert_called_once()

def test_status_command_error(mock_model_manager, mock_get_env_status):
    """Testa o comando status com erro."""
    # Setup
    mock_get_env_status.side_effect = Exception("Erro ao obter status")

    # Execução
    result = runner.invoke(app, ["status"], catch_exceptions=False)

    # Verificações
    assert result.exit_code == 1  # Erro deve retornar código 1
    assert "Erro ao verificar status" in result.stdout

def test_mcp_command_feature(mock_orchestrator, capsys, monkeypatch, mock_mcp_sdk):
    """Testa o comando MCP processando uma feature."""
    # Setup
    input_data = {
        "content": "Criar login",
        "metadata": {
            "type": "feature",
            "options": {
                "model": "gpt-4-turbo",
                "temperature": 0.7
            }
        }
    }

    # Simula entrada stdin
    input_lines = [json.dumps(input_data) + "\n", ""]
    input_iter = iter(input_lines)
    monkeypatch.setattr("sys.stdin.readline", lambda: next(input_iter))

    # Configura mock do handler
    mock_handler = mock_mcp_sdk.return_value
    mock_handler.initialize.return_value = None
    mock_handler.run.side_effect = lambda: None

    with patch.dict(os.environ, {"OPENAI_KEY": "test-key"}), \
         patch("src.mcp.MCPHandler", return_value=mock_handler):

        # Execução
        result = runner.invoke(app, ["mcp"])

        # Verificações
        assert result.exit_code == 0
        mock_handler.initialize.assert_called_once_with(api_key="test-key")

def test_mcp_command_status(mock_get_env_status, mock_model_manager, mock_orchestrator, capsys, monkeypatch, mock_mcp_sdk):
    """Testa o comando MCP obtendo status."""
    # Setup
    mock_get_env_status.return_value = {
        "required": {"OPENAI_KEY": True},
        "optional": {"ELEVATION_MODEL": False}
    }
    input_data = {
        "content": "",
        "metadata": {
            "type": "status"
        }
    }

    # Simula entrada stdin
    input_lines = [json.dumps(input_data) + "\n", ""]
    input_iter = iter(input_lines)
    monkeypatch.setattr("sys.stdin.readline", lambda: next(input_iter))

    # Configura mock do handler
    mock_handler = mock_mcp_sdk.return_value
    mock_handler.initialize.return_value = None
    mock_handler.run.side_effect = lambda: None

    with patch.dict(os.environ, {"OPENAI_KEY": "test-key"}), \
         patch("src.mcp.MCPHandler", return_value=mock_handler):

        # Execução
        result = runner.invoke(app, ["mcp"])

        # Verificações
        assert result.exit_code == 0
        mock_handler.initialize.assert_called_once_with(api_key="test-key")

def test_feature_command_address_requirements(mock_model_manager, mock_orchestrator, mock_validate_env):
    """Testa o comando feature via terminal para requisitos de endereço."""
    # Setup
    expected_result = {
        "feature": "Gerenciamento de Endereços",
        "acceptance_criteria": [
            "Deve permitir cadastro de endereços com CEP (Brasil) e ZipCode (EUA)",
            "Deve integrar com API de busca de CEP para autopreenchimento",
            "Deve integrar com API de ZipCode US para autopreenchimento",
            "Deve permitir edição de endereços cadastrados",
            "Deve permitir listagem de endereços com paginação e filtros"
        ],
        "test_scenarios": [
            "Cadastro com CEP válido brasileiro",
            "Cadastro com ZipCode válido americano",
            "Tentativa de cadastro com CEP inválido",
            "Tentativa de cadastro com ZipCode inválido",
            "Edição de endereço existente",
            "Listagem com filtro por país",
            "Paginação de resultados"
        ],
        "integrations": [
            {"name": "ViaCEP API", "type": "CEP", "country": "BR"},
            {"name": "USPS API", "type": "ZipCode", "country": "US"}
        ],
        "complexity": 4
    }

    mock_orchestrator.handle_input.return_value = expected_result

    with patch("src.cli.get_orchestrator", return_value=mock_orchestrator):
        # Execução
        prompt = """
        Criar sistema de gerenciamento de endereços com:
        - Cadastro, alteração e listagem de endereços
        - Integração com API de CEP do Brasil
        - Integração com API de ZipCode dos EUA
        - Validações e autopreenchimento
        - Paginação e filtros na listagem
        """
        result = runner.invoke(app, ["feature", prompt])

        # Verificações
        assert result.exit_code == 0
        mock_validate_env.assert_called_once()
        mock_model_manager.configure.assert_called_once_with(
            model="gpt-3.5-turbo",
            temperature=0.7
        )

def test_mcp_command_address_requirements(mock_orchestrator, capsys, monkeypatch, mock_mcp_sdk):
    """Testa o comando MCP para requisitos de endereço."""
    # Setup
    expected_result = {
        "feature": "Gerenciamento de Endereços",
        "acceptance_criteria": [
            "Deve permitir cadastro de endereços com CEP (Brasil) e ZipCode (EUA)",
            "Deve integrar com API de busca de CEP para autopreenchimento",
            "Deve integrar com API de ZipCode US para autopreenchimento",
            "Deve permitir edição de endereços cadastrados",
            "Deve permitir listagem de endereços com paginação e filtros"
        ],
        "test_scenarios": [
            "Cadastro com CEP válido brasileiro",
            "Cadastro com ZipCode válido americano",
            "Tentativa de cadastro com CEP inválido",
            "Tentativa de cadastro com ZipCode inválido",
            "Edição de endereço existente",
            "Listagem com filtro por país",
            "Paginação de resultados"
        ],
        "integrations": [
            {"name": "ViaCEP API", "type": "CEP", "country": "BR"},
            {"name": "USPS API", "type": "ZipCode", "country": "US"}
        ],
        "complexity": 4,
        "estimated_hours": 40
    }

    mock_orchestrator.handle_input.return_value = expected_result

    input_data = {
        "content": """
        Criar sistema de gerenciamento de endereços com:
        - Cadastro, alteração e listagem de endereços
        - Integração com API de CEP do Brasil
        - Integração com API de ZipCode dos EUA
        - Validações e autopreenchimento
        - Paginação e filtros na listagem
        """,
        "metadata": {
            "type": "feature",
            "options": {
                "model": "gpt-4-turbo",
                "temperature": 0.7,
                "format": "json"
            }
        }
    }

    # Simula entrada stdin
    input_lines = [json.dumps(input_data) + "\n", ""]
    input_iter = iter(input_lines)
    monkeypatch.setattr("sys.stdin.readline", lambda: next(input_iter))

    # Configura mock do handler
    mock_handler = mock_mcp_sdk.return_value
    mock_handler.initialize.return_value = None
    mock_handler.run.side_effect = lambda: None

    with patch.dict(os.environ, {"OPENAI_KEY": "test-key"}), \
         patch("src.mcp.MCPHandler", return_value=mock_handler):

        # Execução
        result = runner.invoke(app, ["mcp"])

        # Verificações
        assert result.exit_code == 0
        mock_handler.initialize.assert_called_once_with(api_key="test-key") 