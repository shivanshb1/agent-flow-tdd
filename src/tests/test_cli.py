"""
Testes para o módulo CLI.
"""
import json
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from src.cli import app, ModelManager, AgentOrchestrator
from src.core.utils import get_env_status, validate_env

# Setup
runner = CliRunner()

@pytest.fixture
def mock_model_manager():
    with patch("src.cli.ModelManager") as mock:
        manager = Mock()
        mock.return_value = manager
        yield manager

@pytest.fixture
def mock_orchestrator():
    with patch("src.cli.AgentOrchestrator") as mock:
        orchestrator = Mock()
        mock.return_value = orchestrator
        yield orchestrator

@pytest.fixture
def mock_validate_env():
    with patch("src.cli.validate_env") as mock:
        yield mock

@pytest.fixture
def mock_get_env_status():
    with patch("src.cli.get_env_status") as mock:
        mock.return_value = {
            "required": {"OPENAI_API_KEY": True},
            "optional": {"ELEVATION_MODEL": False}
        }
        yield mock

def test_feature_command_success(mock_model_manager, mock_orchestrator, mock_validate_env):
    """Testa o comando feature com sucesso."""
    # Setup
    mock_orchestrator.handle_input.return_value = {"feature": "Login", "tests": ["test1"]}
    
    # Execução
    result = runner.invoke(app, ["feature", "Criar sistema de login"])
    
    # Verificações
    assert result.exit_code == 0
    mock_validate_env.assert_called_once()
    mock_model_manager.return_value.configure.assert_called_once()
    mock_orchestrator.handle_input.assert_called_once_with("Criar sistema de login")
    assert "Feature processada com sucesso!" in result.stdout

def test_feature_command_markdown_output(mock_model_manager, mock_orchestrator, mock_validate_env):
    """Testa o comando feature com saída em markdown."""
    # Setup
    mock_orchestrator.handle_input.return_value = {"feature": "Login"}
    mock_orchestrator.visualizer.visualize.return_value = "# Feature: Login"
    
    # Execução
    result = runner.invoke(app, ["feature", "Criar login", "--format", "markdown"])
    
    # Verificações
    assert result.exit_code == 0
    mock_orchestrator.visualizer.visualize.assert_called_once()
    assert "# Feature: Login" in result.stdout

def test_feature_command_error(mock_model_manager, mock_orchestrator, mock_validate_env):
    """Testa o comando feature com erro."""
    # Setup
    mock_validate_env.side_effect = Exception("Erro de validação")
    
    # Execução
    result = runner.invoke(app, ["feature", "Criar login"])
    
    # Verificações
    assert result.exit_code == 0  # Typer captura a exceção
    assert "Erro ao processar feature" in result.stdout

def test_status_command_success(mock_model_manager, mock_get_env_status):
    """Testa o comando status com sucesso."""
    # Setup
    mock_model_manager.return_value.get_available_models.return_value = ["gpt-4", "gpt-3.5"]
    
    # Execução
    result = runner.invoke(app, ["status"])
    
    # Verificações
    assert result.exit_code == 0
    mock_get_env_status.assert_called_once()
    mock_model_manager.return_value.get_available_models.assert_called_once()
    assert "Status do Sistema" in result.stdout
    assert "OK" in result.stdout

def test_status_command_error(mock_model_manager, mock_get_env_status):
    """Testa o comando status com erro."""
    # Setup
    mock_get_env_status.side_effect = Exception("Erro ao obter status")
    
    # Execução
    result = runner.invoke(app, ["status"])
    
    # Verificações
    assert result.exit_code == 0  # Typer captura a exceção
    assert "Erro ao obter status" in result.stdout

def test_mcp_command_feature(mock_orchestrator):
    """Testa o comando MCP processando uma feature."""
    # Setup
    mock_orchestrator.handle_input.return_value = {"feature": "Login"}
    input_data = {"type": "feature", "prompt": "Criar login"}
    
    # Simula entrada stdin
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.readline.side_effect = [
            json.dumps(input_data) + "\n",
            ""  # EOF
        ]
        
        # Execução
        result = runner.invoke(app, ["mcp"])
        
        # Verificações
        assert result.exit_code == 0
        mock_orchestrator.handle_input.assert_called_once_with("Criar login")

def test_mcp_command_status(mock_get_env_status, mock_model_manager):
    """Testa o comando MCP obtendo status."""
    # Setup
    mock_model_manager.return_value.get_available_models.return_value = ["gpt-4"]
    input_data = {"type": "status"}
    
    # Simula entrada stdin
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.readline.side_effect = [
            json.dumps(input_data) + "\n",
            ""  # EOF
        ]
        
        # Execução
        result = runner.invoke(app, ["mcp"])
        
        # Verificações
        assert result.exit_code == 0
        mock_get_env_status.assert_called_once()
        mock_model_manager.return_value.get_available_models.assert_called_once()

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
    mock_model_manager.return_value.configure.assert_called_once()
    mock_orchestrator.handle_input.assert_called_once_with(prompt)
    assert "Feature processada com sucesso!" in result.stdout
    
    # Verifica conteúdo específico da resposta
    output = json.loads(result.stdout.split("\n")[0])  # Primeira linha contém o JSON
    assert output["feature"] == "Gerenciamento de Endereços"
    assert len(output["acceptance_criteria"]) == 5
    assert len(output["test_scenarios"]) == 7
    assert len(output["integrations"]) == 2
    assert output["complexity"] == 4

def test_mcp_command_address_requirements(mock_orchestrator):
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
        "type": "feature",
        "prompt": """
        Criar sistema de gerenciamento de endereços com:
        - Cadastro, alteração e listagem de endereços
        - Integração com API de CEP do Brasil
        - Integração com API de ZipCode dos EUA
        - Validações e autopreenchimento
        - Paginação e filtros na listagem
        """,
        "options": {
            "model": "gpt-4-turbo",
            "temperature": 0.7,
            "format": "json"
        }
    }
    
    # Simula entrada stdin
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.readline.side_effect = [
            json.dumps(input_data) + "\n",
            ""  # EOF
        ]
        
        # Execução
        result = runner.invoke(app, ["mcp"])
        
        # Verificações
        assert result.exit_code == 0
        mock_orchestrator.handle_input.assert_called_once_with(input_data["prompt"])
        
        # Verifica resposta JSON
        output = json.loads(result.stdout.split("\n")[0])  # Primeira linha contém o JSON
        assert output["status"] == "success"
        result_data = output["result"]
        assert result_data["feature"] == "Gerenciamento de Endereços"
        assert len(result_data["acceptance_criteria"]) == 5
        assert len(result_data["test_scenarios"]) == 7
        assert len(result_data["integrations"]) == 2
        assert result_data["complexity"] == 4
        assert result_data["estimated_hours"] == 40 