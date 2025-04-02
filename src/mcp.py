# src/mpc.py
"""
Integração com o Model Context Protocol (MCP) SDK.
"""
import sys
import json
import logging
from typing import Dict, Any, Optional

from mcp_sdk import ProtocolHandler, BaseMessage, ErrorMessage, CommandMessage  # Assume SDK installation

from src.core.utils import ModelManager, get_env_status, validate_env
from src.app import AgentOrchestrator

logger = logging.getLogger(__name__)

class MCPHandler:
    def __init__(self, orchestrator: Optional[AgentOrchestrator] = None):
        self.protocol = ProtocolHandler()
        self.orchestrator = orchestrator or self._initialize_orchestrator()
        
        # Registrar comandos MCP
        self.protocol.register_command("feature", self.handle_feature)
        self.protocol.register_command("status", self.handle_status)
        self.protocol.register_command("ping", self.handle_ping)

    def _initialize_orchestrator(self) -> AgentOrchestrator:
        """Inicializa o orquestrador com configurações do ambiente"""
        validate_env()
        return AgentOrchestrator(api_key=os.environ["OPENAI_KEY"])

    async def handle_feature(self, msg: CommandMessage) -> BaseMessage:
        """Processa um comando de feature via MCP"""
        try:
            if not msg.payload or "prompt" not in msg.payload:
                return ErrorMessage(code=400, message="Payload inválido: campo 'prompt' obrigatório")

            result = self.orchestrator.handle_input(msg.payload["prompt"])
            
            return BaseMessage(
                message_type="feature_response",
                payload={
                    "status": "success",
                    "result": result
                }
            )
        except Exception as e:
            logger.error(f"Erro no processamento de feature: {str(e)}")
            return ErrorMessage(code=500, message=f"Erro interno: {str(e)}")

    async def handle_status(self, msg: CommandMessage) -> BaseMessage:
        """Retorna o status do sistema via MCP"""
        try:
            env_status = get_env_status()
            models = self.orchestrator.model_manager.get_available_models()
            
            return BaseMessage(
                message_type="status_response",
                payload={
                    "env": {
                        "required": env_status["required"],
                        "optional": env_status["optional"]
                    },
                    "models": models,
                    "orchestrator_active": True
                }
            )
        except Exception as e:
            logger.error(f"Erro ao obter status: {str(e)}")
            return ErrorMessage(code=500, message=f"Erro interno: {str(e)}")

    async def handle_ping(self, msg: CommandMessage) -> BaseMessage:
        """Health check básico"""
        return BaseMessage(
            message_type="pong",
            payload={"timestamp": time.time()}
        )

    def run(self):
        """Inicia o loop principal do protocolo"""
        try:
            logger.info("Iniciando serviço MCP...")
            self.protocol.run()
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