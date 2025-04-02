# src/mpc.py
"""
Integração com o Model Context Protocol (MCP) SDK.
"""
import sys
import json
import logging
from typing import Dict, Any, Optional

from mcp_sdk import MCPHandler as BaseMCPHandler
from mcp_sdk.types import Message, Response

from src.core.utils import ModelManager, get_env_status, validate_env
from src.app import AgentOrchestrator

logger = logging.getLogger(__name__)

class MCPHandler(BaseMCPHandler):
    """Handler para integração com o Model Context Protocol"""
    
    def __init__(self):
        super().__init__()
        self.orchestrator = None
        
    def initialize(self, api_key: Optional[str] = None) -> None:
        """Inicializa o handler com a chave da API"""
        try:
            self.orchestrator = AgentOrchestrator(api_key=api_key)
            logger.info("MCPHandler inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar MCPHandler: {str(e)}", exc_info=True)
            raise
    
    def handle_message(self, message: Message) -> Response:
        """Processa uma mensagem MCP"""
        try:
            # Extrai dados da mensagem
            command_type = message.metadata.get("type", "feature")
            prompt = message.content
            options = message.metadata.get("options", {})
            
            # Configura o modelo se especificado
            if "model" in options:
                self.orchestrator.model_manager.configure(
                    model=options["model"],
                    api_key=options.get("api_key"),
                    temperature=options.get("temperature", 0.7),
                    max_tokens=options.get("max_tokens")
                )
            
            # Processa o comando
            if command_type == "feature":
                result = self.orchestrator.handle_input(prompt)
                return Response(
                    content=result,
                    metadata={
                        "status": "success",
                        "type": "feature"
                    }
                )
            elif command_type == "status":
                env_status = get_env_status()
                available_models = self.orchestrator.model_manager.get_available_models()
                result = {
                    "env": env_status,
                    "models": available_models,
                    "orchestrator": True
                }
                return Response(
                    content=result,
                    metadata={
                        "status": "success",
                        "type": "status"
                    }
                )
            else:
                return Response(
                    content={"error": f"Comando desconhecido: {command_type}"},
                    metadata={
                        "status": "error",
                        "type": "unknown_command"
                    }
                )
                
        except Exception as e:
            logger.error(f"Erro ao processar mensagem MCP: {str(e)}", exc_info=True)
            return Response(
                content={"error": str(e)},
                metadata={
                    "status": "error",
                    "type": "processing_error"
                }
            )

    def run(self):
        """Inicia o loop principal do protocolo"""
        try:
            logger.info("Iniciando serviço MCP...")
            self.run()
        except KeyboardInterrupt:
            logger.info("Serviço MCP encerrado")
        except Exception as e:
            logger.error(f"Falha crítica no serviço MCP: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    # Configuração básica de logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Executar como serviço standalone
    handler = MCPHandler()
    handler.run()