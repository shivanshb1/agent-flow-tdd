"""
CLI para interação com o agente.
"""
import os
import json
import logging
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown

from src.core.utils import ModelManager, get_env_status, validate_env
from src.app import AgentOrchestrator

app = typer.Typer()
console = Console()

def get_orchestrator(api_key: Optional[str] = None) -> AgentOrchestrator:
    """Retorna uma instância do orquestrador."""
    return AgentOrchestrator(api_key=api_key)

@app.command()
def feature(
    prompt: str,
    format: str = typer.Option("json", help="Formato de saída (json ou markdown)")
):
    """Processa uma feature e gera requisitos."""
    try:
        validate_env()
        orchestrator = get_orchestrator()
        orchestrator.model_manager.configure(
            model="gpt-3.5-turbo",
            temperature=0.7
        )

        result = orchestrator.handle_input(prompt)

        if format == "markdown":
            markdown = orchestrator.visualizer.visualize(result)
            console.print(Markdown(markdown))
        else:
            console.print_json(data=result)

    except Exception as e:
        error_msg = f"Erro ao processar feature: {str(e)}"
        logging.error(error_msg)
        console.print(error_msg)
        raise typer.Exit(code=1)

@app.command()
def status():
    """Verifica o status do sistema."""
    try:
        env_status = get_env_status()
        model_manager = ModelManager()
        available_models = model_manager.get_available_models()

        status = {
            "env": env_status,
            "models": available_models,
            "orchestrator": True
        }

        console.print_json(data=status)

    except Exception as e:
        error_msg = f"Erro ao verificar status: {str(e)}"
        logging.error(error_msg)
        console.print(error_msg)
        raise typer.Exit(code=1)

@app.command()
def mcp():
    """Inicia o modo MCP (Model Context Protocol)."""
    try:
        api_key = os.getenv("OPENAI_KEY")
        if not api_key:
            raise ValueError("OPENAI_KEY não definida")

        from src.mcp import MCPHandler
        handler = MCPHandler()
        handler.initialize(api_key=api_key)
        handler.run()

    except Exception as e:
        error_msg = f"Erro no modo MCP: {str(e)}"
        logging.error(error_msg)
        console.print(error_msg)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()