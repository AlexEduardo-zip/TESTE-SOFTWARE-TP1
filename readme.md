# TS Banking - Sistema Bancário em Python

### 1. Membros do Grupo
Alex Eduardo Alves dos Santos; 2021032145
Matheus Flávio Gonçalves Silva; 2020006850

Aplicação bancária com:
- 🏦 Lógica de operações bancárias (depósito, saque, transferência)
- 📊 Investimentos com rendimento (CDB, Poupança, Tesouro Direto)
- 🖥️ Interface textual interativa (Textual)
- ✅ Testes automatizados

## Pré-requisitos
- Python 3.10+
- pip

## 🚀 Como Executar

### 1. Instalar dependências
```bash
pip install textual pytest coverage
```

### 2. Executar a aplicação

```bash
python3 banco_textual/app.py
```

### 3. Executar testes

```bash
# Rodar todos os testes
pytest tests/

# Rodar testes com cobertura
coverage run -m pytest tests/
coverage report  # Exibe relatório no terminal
coverage html    # Gera relatório HTML em htmlcov/
```

### 4. Explicação do Sistema

Este sistema é uma aplicação CLI e API que simula o funcionamento básico de um banco digital. Ele permite operações como:
- Depósito e saque
- Transferências (PIX, DOC, TED, interna)
- Investimentos (CDB, poupança, tesouro direto), com cálculo de rendimento por tempo
- Saque em espécie em caixas eletrônicos, com restrições de múltiplos conforme o tipo de caixa
- Consulta de saldo e extrato
- Limpeza de extrato

O objetivo é servir como base para testes de conceitos de software bancário e validação por meio de testes automatizados.

### 5. Tecnologias Utilizadas

- **Python 3.10+**: Linguagem principal do sistema
- **FastAPI**: Framework para criação de APIs rápidas e modernas
- **Pytest**: Framework de testes automatizados
- **Coverage.py**: Ferramenta para análise de cobertura de testes
- **Pydantic**: Validação de dados e modelos
- **GitHub Actions**: Integração contínua, lint e execução de testes
- **Codecov**: Monitoramento contínuo da cobertura de testes, com relatórios detalhados e badge de cobertura
- **textual**: Exibe a aplicação para interação do usuario no terminal.

### 🛠️ 6. Comandos Úteis
Comando	Descrição
python3 -m banco_textual.app	Executa com imports absolutos
pytest -v	Testes com output detalhado
coverage html && open htmlcov/index.html	Abre relatório de cobertura

### 💡 7. Dicas
Para desenvolvimento, instale como pacote:

```bash
pip install -e .
```
Acesse a conta principal (saldo inicial: R$1000) ou destino (R$500)