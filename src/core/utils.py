"""
Utilitários para o sistema.
Módulo com funções comuns usadas em diferentes partes do sistema.
"""

import os
from typing import Any, List

def mask_sensitive_data(data: Any, mask_str: str = '***') -> Any:
    """
    Mascara dados sensíveis em strings e dicionários.
    
    Args:
        data: Dados a serem mascarados (string, dict ou outro tipo)
        mask_str: String de substituição para dados sensíveis
        
    Returns:
        Dados com informações sensíveis mascaradas
    """
    # Se for None, retorna diretamente
    if data is None:
        return None
        
    # Se for uma string, verificar e mascarar dados sensíveis
    if isinstance(data, str):
        return mask_partially(data, mask_str)
        
    # Se for um dicionário, processar valores recursivamente
    elif isinstance(data, dict):
        masked_data = {}
        for key, value in data.items():
            # Chaves sensíveis são completamente mascaradas
            if any(keyword in key.lower() for keyword in [
                'password', 'senha', 'secret', 'token', 'key', 'auth', 'credential', 'private'
            ]):
                masked_data[key] = mask_str
            else:
                # Processar valores normais recursivamente
                masked_data[key] = mask_sensitive_data(value, mask_str)
        return masked_data
        
    # Se for uma lista, processar itens
    elif isinstance(data, list):
        return [mask_sensitive_data(item, mask_str) for item in data]
        
    # Para outros tipos, retornar sem alteração
    return data

def mask_partially(text, mask_str='***'):
    """
    Mascara parcialmente conteúdo sensível, mantendo caracteres iniciais.
    
    Args:
        text: Texto a ser mascarado
        mask_str: String de substituição
        
    Returns:
        Texto mascarado
    """
    if not text or len(text) < 8:
        return mask_str
        
    # Mostra os primeiros 4 caracteres e mascara o resto
    visible = min(4, len(text) // 3)
    return text[:visible] + mask_str

def get_env_status(var_name: str) -> str:
    """
    Retorna o status de uma variável de ambiente sem expor seu valor.
    
    Args:
        var_name: Nome da variável de ambiente
        
    Returns:
        String indicando o status da variável
    """
    # Lista de palavras-chave para identificar dados sensíveis
    SENSITIVE_KEYWORDS = [
        'pass', 'senha', 'password', 
        'token', 'access_token', 'refresh_token', 'jwt', 
        'secret', 'api_key', 'apikey', 'key', 
        'auth', 'credential', 'oauth', 
        'private', 'signature'
    ]
    
    value = os.environ.get(var_name)
    if not value:
        return "não definido"
    elif any(keyword in var_name.lower() for keyword in SENSITIVE_KEYWORDS):
        return "configurado"
    else:
        # Para variáveis não sensíveis, podemos retornar o valor
        # Mas aplicamos mascaramento para garantir segurança
        return mask_partially(value)

def log_env_status(logger, env_vars: List[str]) -> None:
    """
    Loga o status de múltiplas variáveis de ambiente.
    
    Args:
        logger: Instância do logger
        env_vars: Lista de nomes de variáveis de ambiente
    """
    for var in env_vars:
        status = get_env_status(var)
        logger.info(f"Variável de ambiente {var}: {status}")

# Importar classe TokenValidator
