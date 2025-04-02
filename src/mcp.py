# src/mpc.py
"""
Módulo para lidar com o protocolo MCP (Model Context Protocol).
"""
import json
import logging
import sys
from typing import Optional, Dict, Any

from src.app import AgentOrchestrator
from src.core.utils import ModelManager

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("mcp_server.log")
    ]
)

logger = logging.getLogger(__name__)

try:
    from mcp_sdk import BaseMCPHandler, Message, Response
except ImportError:
    # Mock classes para testes
    class Message:
        """Mock da classe Message do SDK MCP."""
        def __init__(self, content: str, metadata: Dict[str, Any]):
            self.content = content
            self.metadata = metadata

    class Response:
        """Mock da classe Response do SDK MCP."""
        def __init__(self, content: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
            self.content = content
            self.metadata = metadata or {}

    class BaseMCPHandler:
        """Mock da classe BaseMCPHandler do SDK MCP."""
        def __init__(self):
            self.initialized = False
            self.hook = "/prompt-tdd"

        def initialize(self, api_key: str) -> None:
            """Inicializa o handler com a chave da API."""
            self.initialized = True

        def run(self) -> None:
            """Executa o loop principal do handler."""
            while True:
                try:
                    line = sys.stdin.readline()
                    if not line:
                        break

                    data = json.loads(line)
                    message = Message(data["content"], data["metadata"])
                    response = self.handle_message(message)
                    print(json.dumps({
                        "content": response.content,
                        "metadata": response.metadata
                    }))
                except Exception as e:
                    logging.error(f"Erro ao processar mensagem: {str(e)}")
                    break

        def handle_message(self, message: Message) -> Response:
            """Processa uma mensagem e retorna uma resposta."""
            raise NotImplementedError()

class MCPHandler:
    """Manipulador do protocolo MCP."""

    def __init__(self):
        """Inicializa o manipulador MCP."""
        self.orchestrator = None
        self.model_manager = ModelManager()

    def initialize(self, api_key: Optional[str] = None):
        """Inicializa o orquestrador com a chave da API."""
        logger.info("Inicializando MCPHandler...")
        self.orchestrator = AgentOrchestrator(api_key=api_key)
        self.model_manager.configure(
            model="gpt-3.5-turbo",
            temperature=0.7
        )
        logger.info("MCPHandler inicializado com sucesso")

    def process_message(self, message: str) -> dict:
        """Processa uma mensagem recebida."""
        try:
            logger.info(f"Processando mensagem: {message[:100]}...")
            data = json.loads(message)
            content = data.get("content")
            metadata = data.get("metadata", {})
            
            if not content:
                raise ValueError("Mensagem sem conteúdo")

            if not self.orchestrator:
                raise ValueError("Orquestrador não inicializado")

            # Configura o modelo com as opções fornecidas
            options = metadata.get("options", {})
            model = options.get("model", "gpt-3.5-turbo")
            temperature = options.get("temperature", 0.7)
            logger.info(f"Configurando modelo: {model} (temperatura: {temperature})")
            self.orchestrator.model_manager.configure(
                model=model,
                temperature=temperature
            )

            logger.info("Processando entrada com o orquestrador...")
            result = self.orchestrator.handle_input(content)
            
            # Converte para markdown se solicitado
            output_format = options.get("format", "json")
            if output_format == "markdown":
                logger.info("Convertendo resultado para markdown...")
                result = {
                    "content": {
                        "markdown": self.orchestrator.visualizer.visualize(json.dumps(result), "markdown")
                    }
                }

            logger.info("Mensagem processada com sucesso")
            return result

        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}", exc_info=True)
            return {
                "content": {"error": str(e)},
                "metadata": {"status": "error"}
            }

    def run(self):
        """Executa o manipulador MCP."""
        try:
            logger.info("Iniciando servidor MCP...")
            with open("mcp_pipe", "r") as f:
                logger.info("Pipe aberto para leitura")
                while True:
                    line = f.readline()
                    if not line:
                        logger.info("Pipe fechado, encerrando servidor")
                        break

                    try:
                        logger.info("Processando linha recebida...")
                        result = self.process_message(line)
                        response = json.dumps(result)
                        logger.info(f"Enviando resposta: {response[:100]}...")
                        print(response)
                        sys.stdout.flush()
                    except json.JSONDecodeError as e:
                        logger.error(f"Erro ao processar mensagem: {str(e)}", exc_info=True)
                        print(json.dumps({
                            "content": {"error": str(e)},
                            "metadata": {"status": "error"}
                        }))
                        sys.stdout.flush()

        except KeyboardInterrupt:
            logger.info("Servidor interrompido pelo usuário")
        except Exception as e:
            logger.error(f"Erro fatal no servidor: {str(e)}", exc_info=True)

if __name__ == "__main__":
    # Executar como serviço standalone
    handler = MCPHandler()
    handler.initialize(api_key=None)  # A chave será obtida das variáveis de ambiente
    handler.run()