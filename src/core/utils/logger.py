# src/core/logger.py
import os
import sys
import logging
import logging.handlers
from pathlib import Path
from functools import wraps
import time
import re
from typing import Optional, Union, Dict, Any
from rich.console import Console
from rich.logging import RichHandler

# Diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Garantir que o diretório de logs existe
os.makedirs(LOG_DIR, exist_ok=True)

# Configuração de níveis de log
LOG_LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# Nível de log padrão - pode ser sobrescrito via variável de ambiente
DEFAULT_LOG_LEVEL = 'INFO'
LOG_LEVEL = os.environ.get('LOG_LEVEL', DEFAULT_LOG_LEVEL).upper()
NUMERIC_LOG_LEVEL = LOG_LEVEL_MAP.get(LOG_LEVEL, logging.INFO)

# Lista de palavras-chave para identificar dados sensíveis
SENSITIVE_KEYWORDS = [
    'pass', 'senha', 'password', 
    'token', 'access_token', 'refresh_token', 'jwt', 
    'secret', 'api_key', 'apikey', 'key', 
    'auth', 'credential', 'oauth', 
    'private', 'signature'
]

# Padrões de tokens a serem mascarados
TOKEN_PATTERNS = [
    r'sk-[a-zA-Z0-9]{20,}',
    r'sk-proj-[a-zA-Z0-9_-]{20,}',
    r'gh[pous]_[a-zA-Z0-9]{20,}',
    r'github_pat_[a-zA-Z0-9]{20,}',
    r'eyJ[a-zA-Z0-9_-]{5,}\.eyJ[a-zA-Z0-9_-]{5,}\.[a-zA-Z0-9_-]{5,}',
    r'[a-zA-Z0-9_-]{30,}'
]

class SecureLogFilter(logging.Filter):
    """Filtro para mascarar dados sensíveis nos registros de log"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Processa e mascara dados sensíveis no registro de log"""
        record.msg = self.mask_sensitive_data(record.msg)
        if isinstance(record.args, dict):
            record.args = self.mask_sensitive_data(record.args)
        else:
            record.args = tuple(self.mask_sensitive_data(arg) for arg in record.args)
        return True

    def mask_sensitive_data(self, data: Any, mask_str: str = '***') -> Any:
        """Mascara dados sensíveis em strings e estruturas de dados"""
        if isinstance(data, dict):
            return {k: self.mask_value(k, v, mask_str) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.mask_sensitive_data(item, mask_str) for item in data]
        elif isinstance(data, str):
            return self.mask_string(data, mask_str)
        return data

    def mask_value(self, key: str, value: Any, mask_str: str) -> Any:
        """Mascara valores sensíveis baseado na chave e conteúdo"""
        if any(keyword in key.lower() for keyword in SENSITIVE_KEYWORDS):
            return mask_str
        return self.mask_sensitive_data(value, mask_str)

    def mask_string(self, text: str, mask_str: str) -> str:
        """Mascara padrões sensíveis em strings"""
        if len(text) > 20:
            for pattern in TOKEN_PATTERNS:
                if re.search(pattern, text):
                    return self.mask_partially(text, mask_str)
        if any(keyword in text.lower() for keyword in SENSITIVE_KEYWORDS):
            return self.mask_partially(text, mask_str)
        return text

    def mask_partially(self, text: str, mask_str: str) -> str:
        """Mascara parcialmente mantendo parte do conteúdo"""
        if len(text) <= 10:
            return mask_str
        prefix = text[:4]
        suffix = text[-4:] if len(text) > 8 else ''
        return f"{prefix}{mask_str}{suffix}"

def setup_logging(
    name: str = 'agent_flow_tdd',
    level: Union[str, int] = NUMERIC_LOG_LEVEL,
    log_file: Optional[str] = None,
    enable_rich: bool = True,
    file_max_mb: int = 10,
    backup_count: int = 7
) -> logging.Logger:
    """
    Configura o sistema de logging unificado com suporte a Rich e segurança
    
    Args:
        name: Nome do logger
        level: Nível de log (int ou string)
        log_file: Caminho para arquivo de log
        enable_rich: Habilita saída formatada com Rich
        file_max_mb: Tamanho máximo do arquivo em MB
        backup_count: Número de arquivos de backup
        
    Returns:
        Logger configurado
    """
    # Converter nível de log se necessário
    if isinstance(level, str):
        level = LOG_LEVEL_MAP.get(level.upper(), logging.INFO)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remover handlers existentes
    if logger.handlers:
        logger.handlers.clear()
    
    # Adicionar filtro de segurança
    logger.addFilter(SecureLogFilter())
    
    # Configurar console handler com Rich
    if enable_rich and sys.stdout.isatty():
        console = Console(color_system="auto")
        rich_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=True,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=False
        )
        rich_handler.setLevel(level)
        logger.addHandler(rich_handler)
    
    # Configurar file handler com rotação
    if log_file:
        log_path = Path(LOG_DIR) / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path,
            maxBytes=file_max_mb*1024*1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    
    return logger

def log_execution(func=None, level=logging.INFO):
    """Decorador para logar execução de funções com segurança"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger('agent_flow_tdd')
            
            safe_args = [logger.getEffectiveLevel() >= logging.DEBUG or SecureLogFilter().mask_sensitive_data(arg) 
                        for arg in args]
            safe_kwargs = {k: logger.getEffectiveLevel() >= logging.DEBUG or SecureLogFilter().mask_sensitive_data(v) 
                          for k, v in kwargs.items()}
            
            logger.log(level, f"Iniciando {func.__qualname__} - Args: {safe_args}, Kwargs: {safe_kwargs}")
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.log(level, f"Concluído {func.__qualname__} em {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"Erro em {func.__qualname__} após {elapsed:.3f}s", exc_info=True)
                raise
        return wrapper
    return decorator(func) if func else decorator

# Alias para compatibilidade
get_logger = setup_logging

# Logger global padrão
logger = setup_logging()

# Funções auxiliares de conveniência
def log_error(message: str, exc_info=False) -> None:
    """Registra erro com stacktrace opcional"""
    logger.error(message, exc_info=exc_info)

def log_warning(message: str) -> None:
    """Registra aviso"""
    logger.warning(message)

def log_info(message: str) -> None:
    """Registra informação"""
    logger.info(message)

def log_debug(message: str) -> None:
    """Registra mensagem de debug"""
    logger.debug(message)

def get_child_logger(name: str) -> logging.Logger:
    """Obtém um logger filho configurado"""
    return logger.getChild(name)