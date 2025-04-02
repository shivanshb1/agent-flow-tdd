#!/usr/bin/env python3
"""
Script de instalação do pacote.
"""
import os
from setuptools import find_packages, setup

# Configurações de ferramentas
os.environ["BLACK_LINE_LENGTH"] = "100"
os.environ["BLACK_TARGET_VERSION"] = "py39"
os.environ["ISORT_PROFILE"] = "black"
os.environ["ISORT_MULTI_LINE_OUTPUT"] = "3"
os.environ["ISORT_LINE_LENGTH"] = "100"
os.environ["MYPY_PYTHON_VERSION"] = "3.9"
os.environ["MYPY_WARN_RETURN_ANY"] = "1"
os.environ["MYPY_WARN_UNUSED_CONFIGS"] = "1"
os.environ["MYPY_DISALLOW_UNTYPED_DEFS"] = "1"
os.environ["MYPY_CHECK_UNTYPED_DEFS"] = "1"
os.environ["PYTEST_ADDOPTS"] = "-v --cov=src --cov-report=term-missing"

# Configuração do commitizen
os.environ["CZ_TYPE"] = "conventional"
os.environ["CZ_MAX_HEADER_LENGTH"] = "72"
os.environ["CZ_MAX_LINE_LENGTH"] = "100"
os.environ["CZ_VERSION_SCHEME"] = "semver"
os.environ["CZ_VERSION_FILES"] = "setup.py:version,src/__init__.py:__version__"
os.environ["CZ_CUSTOMIZE_HOOK"] = "cz_customize"

setup(
    name="agent-flow-craft",
    version="2025.04.01.1",
    description="Framework para automação de fluxo de criação de features usando agentes de IA",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Seu Nome",
    author_email="seu.email@exemplo.com",
    python_requires=">=3.9",
    packages=find_packages(),
    package_dir={"": "."},
    install_requires=[
        "openai>=1.0.0",
        "openrouter>=0.3.0",
        "google-generativeai>=0.3.0",
        "rope>=1.10.0",
        "pygithub>=2.1.0",
        "python-dotenv>=1.0.0",
        "rich>=13.0.0",
        "typer>=0.9.0",
        "pydantic>=2.0.0",
        "requests>=2.31.0",
        "tenacity>=8.2.0",
        "cachetools>=5.3.0",
        # Ferramentas de desenvolvimento
        "pytest>=7.0.0",
        "pytest-cov>=4.1.0",
        "black>=23.0.0",
        "isort>=5.12.0",
        "flake8>=6.1.0",
        "mypy>=1.5.0",
        "autoflake>=2.2.0",
        "commitizen>=3.12.0",
    ],
    entry_points={
        "console_scripts": [
            "agent-flow-craft=src.cli.cli:app",
            "cz=commitizen.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    setup_requires=["setuptools>=61.0.0", "wheel>=0.40.0"],
    options={
        "flake8": {
            "max_line_length": 100,
            "exclude": ".git,__pycache__,build,dist,*.egg-info",
        },
    },
) 