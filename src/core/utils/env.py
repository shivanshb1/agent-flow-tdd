"""
Utilitários para gerenciamento de variáveis de ambiente.
"""
import os
from typing import Dict, Optional


def get_env_var(name: str, default: Optional[str] = None, args_value: Optional[str] = None) -> Optional[str]:
    """
    Obtém uma variável de ambiente, priorizando args sobre os.environ.

    Args:
        name: Nome da variável.
        default: Valor padrão se a variável não existir.
        args_value: Valor passado via argumentos de linha de comando.

    Returns:
        Valor da variável ou None se não encontrada.
    """
    # Prioriza valor passado via args
    if args_value is not None:
        return args_value
    
    # Se não houver valor em args, tenta os.environ
    return os.environ.get(name, default)


def get_env_status() -> Dict[str, Dict[str, bool]]:
    """
    Verifica o status das variáveis de ambiente necessárias.

    Returns:
        Dicionário com o status de cada variável.
    """
    required_vars = {
        "OPENAI_KEY": False,
        "GITHUB_TOKEN": False,
        "GITHUB_OWNER": False,
        "GITHUB_REPO": False,
    }

    optional_vars = {
        "OPENROUTER_KEY": False,
        "DEEPSEEK_KEY": False,
        "GEMINI_KEY": False,
        "DEFAULT_MODEL": False,
        "ELEVATION_MODEL": False,
        "FALLBACK_ENABLED": False,
        "MODEL_TIMEOUT": False,
        "MAX_RETRIES": False,
        "CACHE_ENABLED": False,
        "CACHE_TTL": False,
        "CACHE_DIR": False,
        "LOG_LEVEL": False,
        "LOG_FILE": False,
    }

    # Verifica variáveis obrigatórias
    for var in required_vars:
        required_vars[var] = bool(get_env_var(var))

    # Verifica variáveis opcionais
    for var in optional_vars:
        optional_vars[var] = bool(get_env_var(var))

    return {
        "required": required_vars,
        "optional": optional_vars,
        "all_required_set": all(required_vars.values()),
    }


def validate_env() -> None:
    """
    Valida se todas as variáveis de ambiente obrigatórias estão definidas.

    Raises:
        ValueError: Se alguma variável obrigatória não estiver definida.
    """
    status = get_env_status()
    if not status["all_required_set"]:
        missing = [var for var, set_ in status["required"].items() if not set_]
        raise ValueError(
            f"Variáveis de ambiente obrigatórias não definidas: {', '.join(missing)}\n"
            "IMPORTANTE: Não use arquivos .env. Configure as variáveis diretamente no ambiente ou via argumentos."
        )