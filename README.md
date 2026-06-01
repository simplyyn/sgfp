# SGFP - Sistema de Gerenciamento Financeiro Pessoal

Aplicação web para controle de finanças pessoais, desenvolvida com Python Flask e SQLite.

## Tecnologias

- **Backend:** Python 3, Flask, Flask-SQLAlchemy, Flask-Login
- **Banco de dados:** SQLite
- **Frontend:** Bootstrap 5, Chart.js, Bootstrap Icons
- **Outros:** python-dotenv

## Funcionalidades

- Cadastro e autenticação de usuários
- Cadastro, edição e exclusão de receitas e despesas
- Dashboard com resumo financeiro (saldo, receitas e despesas totais)
- Gráfico de receitas x despesas por mês
- Listagem com filtro por tipo e período
- Relatório mensal detalhado

## Como executar

**1. Clone o repositório**
```bash
git clone <url-do-repositorio>
cd sgfp
```

**2. Crie e ative o ambiente virtual**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

**3. Instale as dependências**
```bash
pip install -r requirements.txt
```

**4. Configure as variáveis de ambiente**
```bash
cp .env.example .env
# Edite o .env e defina um SECRET_KEY seguro
```

**5. Execute a aplicação**
```bash
python app.py
```

Acesse em: [http://localhost:5000](http://localhost:5000)

## Estrutura de pastas

```
sgfp/
├── app.py              # Configuração e inicialização do Flask
├── models.py           # Models do banco de dados (SQLAlchemy)
├── routes.py           # Rotas e lógica da aplicação
├── templates/          # Templates HTML (Jinja2)
│   ├── base.html
│   ├── login.html
│   ├── cadastro.html
│   ├── dashboard.html
│   ├── movimentacoes.html
│   ├── form_movimentacao.html
│   └── relatorio.html
├── static/
│   └── css/
│       └── style.css
├── .env.example
├── requirements.txt
└── README.md
```

## Capturas de tela

> *Em breve*

## Possíveis melhorias futuras

- Exportar relatório em PDF ou CSV
- Categorias personalizadas por usuário
- Metas de gastos por categoria
- Suporte a múltiplas moedas
- Notificações de gastos acima do limite
