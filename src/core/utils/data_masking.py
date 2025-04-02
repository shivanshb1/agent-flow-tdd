"""
Funções para mascaramento de dados sensíveis.
"""
import re
from typing import Any, Dict, List, Union

def mask_sensitive_data(data: Union[str, Dict[str, Any], List[Any]]) -> Union[str, Dict[str, Any], List[Any]]:
    """
    Mascara dados sensíveis em strings, dicionários ou listas.

    Args:
        data: Dados a serem mascarados. Pode ser uma string, dicionário ou lista.

    Returns:
        Dados com informações sensíveis mascaradas.
    """
    if isinstance(data, str):
        # Mascara tokens e chaves de API
        patterns = [
            (r'["\']?[a-zA-Z0-9-_]{20,}["\']?', '***API_KEY***'),  # API keys
            (r'Bearer\s+[a-zA-Z0-9-_.]+', 'Bearer ***TOKEN***'),  # Bearer tokens
            (r'github_pat_[a-zA-Z0-9_]+', '***GITHUB_PAT***'),  # GitHub PATs
            (r'ghp_[a-zA-Z0-9]+', '***GITHUB_TOKEN***'),  # GitHub tokens
            (r'sk-[a-zA-Z0-9]+', '***OPENAI_KEY***'),  # OpenAI keys
        ]
        masked = data
        for pattern, replacement in patterns:
            masked = re.sub(pattern, replacement, masked)
        return masked
    elif isinstance(data, dict):
        return {k: mask_sensitive_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    return data 