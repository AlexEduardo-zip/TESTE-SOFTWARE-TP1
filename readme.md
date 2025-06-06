# TSBanking

## 1. Membros do Grupo
Alex Eduardo Alves dos Santos; 
Matheus Flávio Gonçalves Silva; 2020006850

## 2. Explicação do Sistema

Este sistema é uma aplicação CLI e API que simula o funcionamento básico de um banco digital. Ele permite operações como:
- Depósito e saque
- Transferências (PIX, DOC, TED, interna)
- Investimentos (CDB, poupança, tesouro direto), com cálculo de rendimento por tempo
- Saque em espécie em caixas eletrônicos, com restrições de múltiplos conforme o tipo de caixa
- Consulta de saldo e extrato
- Limpeza de extrato

O objetivo é servir como base para testes de conceitos de software bancário e validação por meio de testes automatizados.

## 3. Tecnologias Utilizadas

- **Python 3.10+**: Linguagem principal do sistema
- **FastAPI**: Framework para criação de APIs rápidas e modernas
- **Pytest**: Framework de testes automatizados
- **Coverage.py**: Ferramenta para análise de cobertura de testes
- **Pydantic**: Validação de dados e modelos
- **GitHub Actions**: Integração contínua, lint e execução de testes
- **Codecov**: (em breve) Monitoramento contínuo da cobertura de testes, com relatórios detalhados e badge de cobertura
