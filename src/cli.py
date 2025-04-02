"""
CLI para interação com o agente.
"""
import json
import logging
import time
import sys
from typing import Optional

import typer
from rich.console import Console

from src.core.utils import validate_env
from src.app import AgentOrchestrator

from src.mcp import MCPHandler, LLMProvider, PromptManager

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer()
console = Console()

def get_orchestrator(api_key: Optional[str] = None) -> AgentOrchestrator:
    """Retorna uma instância do orquestrador."""
    return AgentOrchestrator(api_key=api_key)

def read_server_response(timeout: int = 10) -> Optional[str]:
    """Lê a resposta do servidor do arquivo de log."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with open("logs/mcp_server.log", "r") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    try:
                        data = json.loads(line.strip())
                        if "content" in data:
                            return line.strip()
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        time.sleep(0.1)
    return None

@app.command()
def main(
    prompt: str,
    mode: str = typer.Option("cli", help="Modo de execução (cli ou mcp)"),
    format: str = typer.Option("json", help="Formato de saída (json ou markdown)")
):
    """CLI para o prompt-tdd."""
    try:
        # Valida variáveis de ambiente
        if not validate_env():
            sys.exit(1)
            
        # Inicializa componentes
        llm_provider = LLMProvider()
        prompt_manager = PromptManager()
        
        if mode == "mcp":
            # Modo MCP (Message Control Protocol)
            handler = MCPHandler(llm_provider, prompt_manager)
            handler.run()
        else:
            # Modo CLI padrão
            response = llm_provider.generate(prompt, {"format": format})
            if response:
                print(response)
            else:
                logger.error("Erro ao gerar resposta")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"Erro ao processar comando: {str(e)}")
        print(f"Erro ao processar comando: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    app()