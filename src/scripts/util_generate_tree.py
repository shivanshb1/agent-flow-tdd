from rich.console import Console
from rich.tree import Tree
import os
import argparse
from src.core.utils.logger import get_logger, log_execution

logger = get_logger(__name__)

@log_execution
def build_tree(directory: str, tree: Tree):
    """Constrói a árvore de diretórios recursivamente"""
    logger.info(f"INÍCIO - build_tree | Diretório: {directory}")
    
    try:
        entries = os.listdir(directory)
        logger.debug(f"Encontrados {len(entries)} itens em {directory}")
        
        for entry in sorted(entries):
            if entry in [".git", "__pycache__", "node_modules", ".github"]:
                continue
                
            path = os.path.join(directory, entry)
            if os.path.isdir(path):
                logger.debug(f"Processando diretório: {entry}")
                branch = tree.add(f"📁 {entry}")
                build_tree(path, branch)
            else:
                logger.debug(f"Adicionando arquivo: {entry}")
                tree.add(f"📄 {entry}")
        
        return tree
    except Exception as e:
        logger.error(f"FALHA - build_tree | Erro: {str(e)}", exc_info=True)
        raise

@log_execution
def main():
    """Função principal"""
    logger.info("INÍCIO - main")
    
    try:
        parser = argparse.ArgumentParser(description="Gera árvore de diretórios")
        parser.add_argument(
            "--output", "-o",
            type=str,
            default="TREE.md",
            help="Caminho do arquivo de saída"
        )
        
        args = parser.parse_args()
        logger.debug(f"Argumentos processados: output={args.output}")
        
        console = Console(record=True)
        root_tree = Tree("📦 [bold blue]agent-flow-tdd[/bold blue]")
        
        build_tree(".", root_tree)
        logger.info("Árvore construída com sucesso")
        
        output_dir = os.path.dirname(args.output)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            logger.debug(f"Diretório de saída criado: {output_dir}")
        
        with open(args.output, "w") as f:
            f.write("# 📂 Estrutura do Projeto\n\n```\n")
            f.write(console.export_text(root_tree))
            f.write("\n```\n")
            
        logger.info(f"SUCESSO - Arquivo gerado: {args.output}")
        
    except Exception as e:
        logger.error(f"FALHA - main | Erro: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
