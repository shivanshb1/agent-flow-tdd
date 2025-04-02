"""
CLI principal do sistema.
"""
import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from src.agents import (
    ConceptGenerationAgent,
    FeatureCoordinatorAgent,
    GitHubIntegrationAgent,
    PlanValidator,
    TDDCriteriaAgent,
)
from src.core.utils import (
    ModelManager,
    get_env_status,
    log_error,
    validate_env,
)

app = typer.Typer(help="Agent Flow Craft - Framework para automação de fluxo de features")
console = Console()


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
) -> None:
    """
    Cria uma nova feature usando o fluxo completo de agentes.
    """
    try:
        # Valida variáveis de ambiente
        validate_env()

        # Cria o agente coordenador
        agent = FeatureCoordinatorAgent(
            model_name=model,
            elevation_model=elevation_model,
            force_model=force,
            api_key=api_key or os.environ.get("API_KEY"),
            timeout=timeout,
            max_retries=max_retries,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Executa o fluxo
        result = asyncio.run(agent.execute(prompt=prompt))

        # Exibe o resultado
        console.print("[green]Feature criada com sucesso![/green]")
        console.print(result)

    except Exception as e:
        log_error(e)
        console.print(f"[red]Erro ao criar feature: {str(e)}[/red]")


@app.command()
def concept(
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
) -> None:
    """
    Gera um conceito de feature.
    """
    try:
        # Valida variáveis de ambiente
        validate_env()

        # Cria o agente
        agent = ConceptGenerationAgent(
            model_name=model,
            elevation_model=elevation_model,
            force_model=force,
            api_key=api_key or os.environ.get("API_KEY"),
            timeout=timeout,
            max_retries=max_retries,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Executa o fluxo
        result = asyncio.run(agent.execute(prompt=prompt))

        # Exibe o resultado
        console.print("[green]Conceito gerado com sucesso![/green]")
        console.print(result)

    except Exception as e:
        log_error(e)
        console.print(f"[red]Erro ao gerar conceito: {str(e)}[/red]")


@app.command()
def validate(
    plan_file: str,
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
) -> None:
    """
    Valida um plano de execução.
    """
    try:
        # Valida variáveis de ambiente
        validate_env()

        # Cria o agente
        agent = PlanValidator(
            model_name=model,
            elevation_model=elevation_model,
            force_model=force,
            api_key=api_key or os.environ.get("API_KEY"),
            timeout=timeout,
            max_retries=max_retries,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Executa o fluxo
        result = asyncio.run(agent.execute(plan_file=plan_file))

        # Exibe o resultado
        console.print("[green]Plano validado com sucesso![/green]")
        console.print(result)

    except Exception as e:
        log_error(e)
        console.print(f"[red]Erro ao validar plano: {str(e)}[/red]")


@app.command()
def github(
    context_id: str,
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
) -> None:
    """
    Integra uma feature com o GitHub.
    """
    try:
        # Valida variáveis de ambiente
        validate_env()

        # Cria o agente
        agent = GitHubIntegrationAgent(
            model_name=model,
            elevation_model=elevation_model,
            force_model=force,
            api_key=api_key or os.environ.get("API_KEY"),
            timeout=timeout,
            max_retries=max_retries,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Executa o fluxo
        result = asyncio.run(agent.execute(context_id=context_id))

        # Exibe o resultado
        console.print("[green]Integração com GitHub concluída com sucesso![/green]")
        console.print(result)

    except Exception as e:
        log_error(e)
        console.print(f"[red]Erro ao integrar com GitHub: {str(e)}[/red]")


@app.command()
def tdd(
    feature_id: str,
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
) -> None:
    """
    Gera critérios de TDD para uma feature.
    """
    try:
        # Valida variáveis de ambiente
        validate_env()

        # Cria o agente
        agent = TDDCriteriaAgent(
            model_name=model,
            elevation_model=elevation_model,
            force_model=force,
            api_key=api_key or os.environ.get("API_KEY"),
            timeout=timeout,
            max_retries=max_retries,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Executa o fluxo
        result = asyncio.run(agent.execute(feature_id=feature_id))

        # Exibe o resultado
        console.print("[green]Critérios de TDD gerados com sucesso![/green]")
        console.print(result)

    except Exception as e:
        log_error(e)
        console.print(f"[red]Erro ao gerar critérios de TDD: {str(e)}[/red]")


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

        # Exibe a tabela
        console.print(table)

    except Exception as e:
        log_error(e)
        console.print(f"[red]Erro ao obter status: {str(e)}[/red]")


if __name__ == "__main__":
    app()