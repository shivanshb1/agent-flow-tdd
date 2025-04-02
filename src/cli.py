"""
CLI principal do sistema.
"""
import asyncio
import json
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from src.core.utils import (
    ModelManager,
    get_env_status,
    log_error,
    validate_env,
)
from src.app import AgentOrchestrator

app = typer.Typer(help="Agent Flow TDD - Framework para automação de fluxo de features TDD")
console = Console()
orchestrator = AgentOrchestrator()

@app.command()
def feature(
    prompt: str,
    model: str = typer.Option(
        "gpt-4-turbo",
        "--model",
        "-m",
        help="Modelo a ser usado",
    ),
    elevation_model: Optional[str] = typer.Option(
        None,
        "--elevation-model",
        "-e",
        help="Modelo alternativo para fallback",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Força o uso do modelo especificado sem fallback",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="Chave da API para o modelo",
    ),
    timeout: int = typer.Option(
        30,
        "--timeout",
        "-t",
        help="Tempo limite para requisições ao modelo",
    ),
    max_retries: int = typer.Option(
        3,
        "--max-retries",
        "-r",
        help="Número máximo de tentativas em caso de falha",
    ),
    temperature: float = typer.Option(
        0.7,
        "--temperature",
        "-temp",
        help="Temperatura para geração de texto pelo modelo",
    ),
    max_tokens: Optional[int] = typer.Option(
        None,
        "--max-tokens",
        "-mt",
        help="Número máximo de tokens para geração de texto",
    ),
    output_format: str = typer.Option(
        "json",
        "--format",
        "-fmt",
        help="Formato de saída (json ou markdown)",
    ),
) -> None:
    """
    Cria uma nova feature usando o fluxo completo de agentes.
    """
    try:
        # Valida variáveis de ambiente
        validate_env()

        # Configura o modelo com os parâmetros fornecidos
        model_manager = ModelManager()
        model_manager.configure(
            model=model,
            elevation_model=elevation_model,
            force=force,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Processa a feature usando o orquestrador
        result = orchestrator.handle_input(prompt)

        # Formata a saída de acordo com o formato solicitado
        if output_format == "markdown":
            formatted_result = orchestrator.visualizer.visualize(json.dumps(result), "markdown")
            console.print(formatted_result)
        else:
            console.print(json.dumps(result, indent=2))

        console.print("[green]Feature processada com sucesso![/green]")

    except Exception as e:
        log_error(e)
        console.print(f"[red]Erro ao processar feature: {str(e)}[/red]")

@app.command()
def status() -> None:
    """
    Exibe o status do sistema.
    """
    try:
        # Obtém status das variáveis de ambiente
        env_status = get_env_status()

        # Obtém modelos disponíveis
        model_manager = ModelManager()
        available_models = model_manager.get_available_models()

        # Cria tabela de status
        table = Table(title="Status do Sistema")
        table.add_column("Componente", style="cyan")
        table.add_column("Status", style="green")

        # Adiciona status das variáveis obrigatórias
        for var, set_ in env_status["required"].items():
            table.add_row(
                var,
                "[green]OK[/green]" if set_ else "[red]Não configurado[/red]",
            )

        # Adiciona status das variáveis opcionais
        for var, set_ in env_status["optional"].items():
            table.add_row(
                f"{var} (opcional)",
                "[green]OK[/green]" if set_ else "[yellow]Não configurado[/yellow]",
            )

        # Adiciona modelos disponíveis
        table.add_row("Modelos Disponíveis", ", ".join(available_models))

        # Adiciona status do orquestrador
        table.add_row(
            "Orquestrador",
            "[green]Ativo[/green]" if orchestrator else "[red]Inativo[/red]"
        )

        # Exibe a tabela
        console.print(table)

    except Exception as e:
        log_error(e)
        console.print(f"[red]Erro ao obter status: {str(e)}[/red]")

@app.command()
def mcp() -> None:
    """
    Inicia o modo MCP via stdin/stdout.
    """
    try:
        # Desativa saída rich para evitar interferência no protocolo
        console = Console(file=sys.stderr)
        console.print("[green]Iniciando modo MCP via stdin/stdout...[/green]")
        
        while True:
            try:
                # Lê comando da entrada padrão
                line = sys.stdin.readline()
                if not line:
                    break
                
                # Processa o comando JSON
                command = json.loads(line)
                
                # Executa o comando apropriado
                if command["type"] == "feature":
                    result = orchestrator.handle_input(command["prompt"])
                    response = {
                        "status": "success",
                        "result": result
                    }
                elif command["type"] == "status":
                    env_status = get_env_status()
                    model_manager = ModelManager()
                    response = {
                        "status": "success",
                        "result": {
                            "env": env_status,
                            "models": model_manager.get_available_models(),
                            "orchestrator": "active" if orchestrator else "inactive"
                        }
                    }
                else:
                    response = {
                        "status": "error",
                        "error": f"Comando desconhecido: {command['type']}"
                    }
                
                # Envia resposta para stdout
                print(json.dumps(response))
                sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                print(json.dumps({
                    "status": "error",
                    "error": f"JSON inválido: {str(e)}"
                }))
                sys.stdout.flush()
            except Exception as e:
                print(json.dumps({
                    "status": "error",
                    "error": str(e)
                }))
                sys.stdout.flush()
    
    except KeyboardInterrupt:
        console.print("[yellow]Encerrando modo MCP...[/yellow]")
    except Exception as e:
        log_error(e)
        console.print(f"[red]Erro no modo MCP: {str(e)}[/red]")

if __name__ == "__main__":
    app()