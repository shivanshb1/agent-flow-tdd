# Agent Flow TDD

Framework para automação de fluxo de features TDD usando agentes de IA.

## 🚀 Funcionalidades

- Geração de features com critérios de aceite e cenários de teste
- Análise de complexidade e estimativas
- Suporte a múltiplos modelos de IA (GPT-3.5, GPT-4)
- Interface CLI com modo interativo e MCP (Multi-Command Protocol)
- Saída em formatos JSON e Markdown

## 📋 Pré-requisitos

- Python 3.13+
- Chave de API OpenAI (`OPENAI_KEY`)
- Ambiente virtual Python (venv)

## 🛠️ Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/agent-flow-tdd.git
cd agent-flow-tdd
```

2. Crie e ative o ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
make install
```

4. Configure a variável de ambiente `OPENAI_KEY`:
```bash
export OPENAI_KEY="sua-chave-aqui"
```

## 🎮 Comandos Disponíveis

### `make install`
Instala todas as dependências do projeto.

```bash
make install
```

### `make test`
Executa todos os testes do projeto.

```bash
make test
```

### `make cli`
Inicia o CLI para processamento de features.

```bash
make cli

# Exemplos de uso:
cli feature "Criar sistema de login com autenticação de dois fatores"
cli feature "Criar sistema de cadastro de usuários" --model gpt-4-turbo
cli feature "Criar API REST" --format markdown
cli status
```

#### Opções do comando `feature`:
- `--model, -m`: Modelo a ser usado (default: gpt-3.5-turbo)
- `--elevation-model, -e`: Modelo para fallback (default: gpt-4-turbo)
- `--force, -f`: Força uso do modelo sem fallback
- `--api-key, -k`: Chave da API (opcional)
- `--timeout, -t`: Tempo limite em segundos (default: 30)
- `--max-retries, -r`: Máximo de tentativas (default: 3)
- `--temperature, -temp`: Temperatura do modelo (default: 0.7)
- `--max-tokens, -mt`: Limite de tokens (opcional)
- `--format, -fmt`: Formato de saída (json/markdown)

### Modo MCP (Multi-Command Protocol)

O modo MCP permite interação via stdin/stdout usando JSON:

```bash
cli mcp
```

#### Comandos MCP:

1. Processar Feature:
```json
{
  "type": "feature",
  "prompt": "Criar sistema de login",
  "options": {
    "model": "gpt-4-turbo",
    "temperature": 0.7,
    "format": "json"
  }
}
```

2. Obter Status:
```json
{
  "type": "status"
}
```

## 🧪 Testes

O projeto usa pytest para testes. Execute:

```bash
make test
```

## 📝 Logs

Os logs são gerados automaticamente com:
- Nível INFO para entrada/saída de funções
- Nível DEBUG para estados intermediários
- Nível ERROR para exceções (com stacktrace)

## 🔒 Variáveis de Ambiente

- `OPENAI_KEY`: Chave da API OpenAI (obrigatória)
- `ELEVATION_MODEL`: Modelo para fallback (opcional)

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua branch de feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.