# Configurações comuns para todos os ambientes
import os
from pathlib import Path
from .utils.logger import get_logger, log_execution

logger = get_logger(__name__)

@log_execution
def setup_paths():
    """Configura e valida os caminhos base do projeto"""
    logger.info("INÍCIO - setup_paths | Configurando caminhos base")
    
    try:
        # Constrói caminhos dentro do projeto
        base_dir = Path(__file__).resolve().parent.parent.parent
        logger.debug(f"Diretório base: {base_dir}")

        # Configurações de caminhos
        log_dir = os.path.join(base_dir, 'run', 'logs')
        configs_dir = os.path.join(base_dir, 'configs')

        # Criar diretórios se não existirem
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(configs_dir, exist_ok=True)
        
        logger.info("SUCESSO - Caminhos configurados e validados")
        return base_dir, log_dir, configs_dir
        
    except Exception as e:
        logger.error(f"FALHA - setup_paths | Erro: {str(e)}", exc_info=True)
        raise

# Executa a configuração de caminhos
BASE_DIR, LOG_DIR, CONFIGS_DIR = setup_paths()