# src/mpc.py
"""
Módulo para processamento de mensagens MCP (Model Context Protocol).
"""
import json
import logging
import sys
from typing import Any, Dict, Optional

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

class MCPHandler(BaseMCPHandler):
    """Handler para processamento de mensagens MCP."""

    def __init__(self):
        """Inicializa o handler."""
        super().__init__()
        self.orchestrator = None

    def initialize(self, api_key: str) -> None:
        """Inicializa o handler com a chave da API."""
        super().initialize(api_key)
        from src.app import AgentOrchestrator
        self.orchestrator = AgentOrchestrator()
        self.orchestrator.model_manager.configure(
            model="gpt-3.5-turbo",
            temperature=0.7
        )
        logging.info("Handler inicializado com sucesso")

    def handle_message(self, message: Message) -> Response:
        """Processa uma mensagem e retorna uma resposta."""
        try:
            command_type = message.metadata.get("type", "")
            options = message.metadata.get("options", {})

            if command_type == "feature":
                # Configura o modelo com as opções fornecidas
                model = options.get("model", "gpt-3.5-turbo")
                temperature = options.get("temperature", 0.7)
                self.orchestrator.model_manager.configure(
                    model=model,
                    temperature=temperature
                )

                # Processa a feature
                result = self.orchestrator.handle_input(message.content)
                return Response(content=result)

            elif command_type == "status":
                from src.core.utils import get_env_status
                env_status = get_env_status()
                models = self.orchestrator.model_manager.get_available_models()
                status = {
                    "env": env_status,
                    "models": models,
                    "orchestrator": True
                }
                return Response(content=status)

            else:
                raise ValueError(f"Tipo de comando desconhecido: {command_type}")

        except Exception as e:
            logging.error(f"Erro ao processar mensagem: {str(e)}")
            return Response(
                content={"error": str(e)},
                metadata={"status": "error"}
            )

if __name__ == "__main__":
    # Configuração básica de logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Executar como serviço standalone
    handler = MCPHandler()
    handler.run()