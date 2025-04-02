"""
CLI para interação com o agente.
"""
import os
import json
import logging
import sys
import time
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

def read_server_response(timeout: int = 10) -> Optional[str]:
    """Lê a resposta do servidor do arquivo de log."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with open("mcp_server.log", "r") as f:
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
    prompt: str = typer.Argument(..., help="Prompt para processamento"),
    format: str = typer.Option("json", help="Formato de saída (json ou markdown)"),
    mode: str = typer.Option("feature", help="Modo de operação (feature, status, mcp)")
):
    """Processa prompts usando agentes de IA."""
    try:
        validate_env()
        
        if mode == "mcp":
            api_key = os.getenv("OPENAI_KEY")
            if not api_key:
                raise ValueError("OPENAI_KEY não definida")

            from src.mcp import MCPHandler
            handler = MCPHandler()
            handler.initialize(api_key=api_key)
            
            # Envia uma mensagem inicial com o formato desejado
            message = {
                "content": prompt,
                "metadata": {
                    "type": "feature",
                    "options": {
                        "format": format,
                        "model": "gpt-3.5-turbo",
                        "temperature": 0.7
                    }
                }
            }
            
            # Envia a mensagem para o servidor
            with open("mcp_pipe", "w") as f:
                f.write(json.dumps(message) + "\n")
                f.flush()
            
            # Lê a resposta do servidor
            response = read_server_response()
            if response:
                try:
                    data = json.loads(response)
                    if format == "markdown" and "content" in data and "markdown" in data["content"]:
                        console.print(Markdown(data["content"]["markdown"]))
                    else:
                        console.print_json(data=data)
                except json.JSONDecodeError:
                    console.print(response)
            else:
                console.print("Timeout ao aguardar resposta do servidor")
            return

        if mode == "status":
            env_status = get_env_status()
            model_manager = ModelManager()
            available_models = model_manager.get_available_models()

            status = {
                "env": env_status,
                "models": available_models,
                "orchestrator": True
            }

            console.print_json(data=status)
            return

        # Modo feature (padrão)
        orchestrator = get_orchestrator()
        orchestrator.model_manager.configure(
            model="gpt-3.5-turbo",
            temperature=0.7
        )

        result = orchestrator.handle_input(prompt)

        if format == "markdown":
            markdown = orchestrator.visualizer.visualize(json.dumps(result), "markdown")
            console.print(Markdown(markdown))
        else:
            console.print_json(data=result)

    except Exception as e:
        error_msg = f"Erro ao processar comando: {str(e)}"
        logging.error(error_msg)
        console.print(error_msg)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()