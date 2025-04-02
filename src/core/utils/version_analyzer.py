"""
Módulo para análise de commits e determinação automática de versões.
"""
import os
import re
import json
from typing import Dict, Optional, Tuple

from src.core.logger import get_logger, log_execution

logger = get_logger(__name__)

COMMIT_TYPES = {
    'feat': 'minor',  # Novas funcionalidades
    'fix': 'patch',   # Correções de bugs
    'docs': 'patch',  # Documentação
    'style': 'patch', # Formatação
    'refactor': 'patch', # Refatoração
    'test': 'patch',  # Testes
    'chore': 'patch', # Manutenção
    'perf': 'patch',  # Performance
    'ci': 'patch',    # CI/CD
    'build': 'patch', # Build
    'breaking': 'major' # Breaking changes
}

BREAKING_PATTERNS = [
    r'breaking change',
    r'breaking-change',
    r'incompatible',
    r'não compatível',
    r'breaking',
    r'major update'
]

FEATURE_PATTERNS = [
    r'add(?:ed|ing)?\s+(?:new\s+)?(?:feature|functionality)',
    r'implement(?:ed|ing)?',
    r'criado?\s+(?:novo|nova)',
    r'adiciona(?:do|ndo)?',
    r'nova\s+funcionalidade',
    r'novo\s+recurso'
]

FIX_PATTERNS = [
    r'fix(?:ed|ing)?',
    r'bug\s*fix',
    r'resolve[sd]?',
    r'corrig(?:e|ido|indo)',
    r'conserta(?:do|ndo)?',
    r'correc[aã]o'
]

@log_execution
def analyze_commit_message(message: str) -> str:
    """
    Analisa a mensagem do commit para determinar o tipo de versão a ser incrementada.
    
    Args:
        message: Mensagem do commit
        
    Returns:
        str: Tipo de versão ('major', 'minor' ou 'patch')
    """
    message = message.lower()
    
    # Verifica breaking changes
    for pattern in BREAKING_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            return 'major'
    
    # Verifica novas funcionalidades
    for pattern in FEATURE_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            return 'minor'
    
    # Verifica correções
    for pattern in FIX_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            return 'patch'
    
    # Se não identificou nenhum padrão específico, assume patch
    return 'patch'

@log_execution
def get_current_version() -> Tuple[str, Dict]:
    """
    Obtém a versão atual do projeto.
    
    Returns:
        Tuple[str, Dict]: Versão atual e dados do version_commits.json
    """
    try:
        with open('version_commits.json', 'r') as f:
            data = json.load(f)
            versions = sorted(data.keys())
            if versions:
                return versions[-1], data
    except Exception as e:
        logger.error(f"Erro ao ler version_commits.json: {str(e)}")
    
    return "0.1.0", {}

@log_execution
def get_last_commit_info() -> Optional[Tuple[str, str]]:
    """
    Obtém informações do último commit.
    
    Returns:
        Optional[Tuple[str, str]]: (hash do commit, mensagem do commit) ou None se falhar
    """
    try:
        commit_hash = os.popen('git rev-parse --short HEAD').read().strip()
        commit_msg = os.popen('git log -1 --pretty=%B').read().strip()
        return commit_hash, commit_msg
    except Exception as e:
        logger.error(f"Erro ao obter informações do último commit: {str(e)}")
        return None

@log_execution
def increment_version(current: str, increment_type: str) -> str:
    """
    Incrementa a versão baseado no tipo de incremento.
    
    Args:
        current: Versão atual
        increment_type: Tipo de incremento ('major', 'minor' ou 'patch')
        
    Returns:
        str: Nova versão
    """
    try:
        # Se a versão atual usa o formato de data
        if re.match(r'\d{4}\.\d{2}\.\d{2}', current):
            import time
            return f"{time.strftime('%Y.%m.%d')}.1"
        
        # Versão semântica padrão
        parts = current.split('.')
        if len(parts) < 3:
            parts.extend(['0'] * (3 - len(parts)))
        
        major, minor, patch = map(lambda x: int(re.search(r'\d+', x).group()), parts[:3])
        
        if increment_type == 'major':
            return f"{major + 1}.0.0"
        elif increment_type == 'minor':
            return f"{major}.{minor + 1}.0"
        else:  # patch
            return f"{major}.{minor}.{patch + 1}"
    except Exception as e:
        logger.error(f"Erro ao incrementar versão: {str(e)}")
        return current

@log_execution
def update_version_files(new_version: str) -> bool:
    """
    Atualiza os arquivos que contêm a versão.
    
    Args:
        new_version: Nova versão a ser definida
        
    Returns:
        bool: True se a atualização foi bem sucedida
    """
    try:
        # Atualiza setup.py
        with open('setup.py', 'r') as f:
            content = f.read()
        content = re.sub(r'version="[^"]*"', f'version="{new_version}"', content)
        with open('setup.py', 'w') as f:
            f.write(content)
            
        # Atualiza __init__.py
        with open('src/__init__.py', 'r') as f:
            content = f.read()
        content = re.sub(r'__version__\s*=\s*"[^"]*"', f'__version__ = "{new_version}"', content)
        with open('src/__init__.py', 'w') as f:
            f.write(content)
            
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar arquivos de versão: {str(e)}")
        return False

@log_execution
def smart_bump() -> Optional[str]:
    """
    Realiza o bump de versão de forma inteligente, analisando o último commit.
    
    Returns:
        Optional[str]: Nova versão ou None se falhar
    """
    # Obtém informações do último commit
    commit_info = get_last_commit_info()
    if not commit_info:
        return None
    
    commit_hash, commit_msg = commit_info
    
    # Analisa a mensagem do commit
    increment_type = analyze_commit_message(commit_msg)
    
    # Obtém versão atual
    current_version, version_data = get_current_version()
    
    # Incrementa a versão
    new_version = increment_version(current_version, increment_type)
    
    # Atualiza os arquivos
    if not update_version_files(new_version):
        return None
    
    # Atualiza version_commits.json
    version_data[new_version] = {
        'commit_hash': commit_hash,
        'timestamp': os.popen('date "+%Y-%m-%d %H:%M:%S"').read().strip(),
        'increment_type': increment_type,
        'previous_version': current_version
    }
    
    try:
        with open('version_commits.json', 'w') as f:
            json.dump(version_data, f, indent=2)
    except Exception as e:
        logger.error(f"Erro ao atualizar version_commits.json: {str(e)}")
        return None
    
    return new_version 