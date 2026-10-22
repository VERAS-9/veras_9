# 🛍️ Bot de Vendas para Discord

Este é um bot do Discord focado em automação de vendas e gerenciamento de lojas virtuais diretamente pelo aplicativo. Desenvolvido em Python, ele facilita a gestão de estoque, relatórios financeiros e o atendimento aos clientes de forma ágil e automatizada.

## 🚀 Funcionalidades

- **Painel Administrativo:** Interface com botões interativos para os administradores aprovarem ou recusarem pedidos.
- **Relatórios Financeiros:** Comando `/ver_vendas` que gera estatísticas detalhadas e o faturamento total da loja em tempo real.
- **Limpeza Automática:** Sistema integrado para deletar canais de atendimento ou suporte com atraso programado, mantendo o servidor limpo.
- **Persistência de Dados:** Salvamento automático do histórico e estatísticas em arquivo JSON (`estatisticas_vendas.json`).

## 🛠️ Tecnologias Utilizadas

- **Python** (Linguagem principal)
- **Discord.py** (Biblioteca para integração com a API do Discord)
- **Python-dotenv** (Gerenciamento seguro de credenciais/tokens)
- **Asyncio** (Manipulação de processos assíncronos)

## 📦 Como Rodar o Projeto

1. Clone o repositório:
   ```bash
   git clone https://github.com
   ```

2. Instale as dependências necessárias:
   ```bash
   pip install -r requirements.txt
   ```

3. Crie um arquivo `.env` na raiz do projeto e adicione o seu token do Discord:
   ```env
   DISCORD_TOKEN=seu_token_aqui
   ```

4. Inicie o bot:
   ```bash
   python main.py
   ```
