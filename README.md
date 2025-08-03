# 📊 Calendário Financeiro

Sistema completo para gerenciamento de contas a pagar e pagas por empresa, com autenticação de usuários e armazenamento em nuvem.

## ✨ Funcionalidades

### 🔐 Autenticação e Segurança
- Sistema de login e registro de usuários
- Confirmação por email
- Dados isolados por usuário
- Integração com Supabase Auth

### � Calendário Visual
- Visualização mensal dos dados financeiros
- Cores diferenciadas por tipo de transação
- Navegação entre meses e anos
- Regras de negócio automáticas (fins de semana → segunda-feira)

### �📁 Processamento de Arquivos
- Upload de arquivos Excel (.xls, .xlsx)
- Conversão automática de formatos antigos
- Validação e limpeza de dados
- Detecção automática de estrutura

### 📈 Análise Financeira
- Comparação automática entre contas a pagar e pagas
- Identificação de correspondências
- Relatórios detalhados por empresa
- Dashboard com métricas em tempo real

### 💾 Banco de Dados
- Armazenamento em PostgreSQL (Supabase)
- Sincronização em tempo real
- Backup automático na nuvem
- Histórico completo de processamentos

## 🚀 Como Executar

### Pré-requisitos
- Python 3.8+
- Conta no Supabase

### Configuração

1. **Clone o repositório:**
```bash
git clone <url-do-repositorio>
cd calendario_financeiro
```

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

3. **Configure o Supabase:**
   - Crie um projeto no [Supabase](https://supabase.com)
   - Execute o script SQL do banco (arquivo `fix_rls.sql`)
   - Copie `.env.example` para `.env` e configure suas credenciais

4. **Execute a aplicação:**
```bash
streamlit run main_with_auth.py
```

## 🛠️ Tecnologias

- **Backend:** Python, Pandas, Supabase
- **Frontend:** Streamlit, Plotly
- **Banco:** PostgreSQL (Supabase)
- **Autenticação:** Supabase Auth
- **Deploy:** Streamlit Cloud (preparado)

## 📋 Estrutura do Projeto

```
calendario_financeiro/
├── src/
│   ├── auth/           # Sistema de autenticação
│   ├── database/       # Cliente Supabase
│   ├── calendar_app.py # Interface principal
│   ├── data_processor.py # Processamento de dados
│   └── payment_analyzer.py # Análise de pagamentos
├── templates/          # Modelos de arquivos
├── data/              # Dados processados (local)
├── reports/           # Relatórios gerados
├── main_with_auth.py  # Aplicação principal com auth
└── main.py           # Versão sem autenticação (legacy)
```

## 🔧 Configuração do Banco

Execute o arquivo `fix_rls.sql` no seu projeto Supabase para criar o schema completo.

## 📄 Formato dos Arquivos

### Contas a Pagar:
- Empresa, Valor, Data de Vencimento, Descrição, Categoria

### Contas Pagas:
- Empresa, Valor, Data de Pagamento, Descrição, Categoria

## 📄 Licença

Este projeto está licenciado sob a MIT License.

## 👨‍💻 Autor

Mairon Hoppe - [hoppe.mairon@gmail.com](mailto:hoppe.mairon@gmail.com)
