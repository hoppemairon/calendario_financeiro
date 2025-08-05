# 📅 Calendário Financeiro

Sistema de gerenciamento de calendário financeiro para análise de contas a pagar e pagas por empresa.

## 🚀 Funcionalidades

### 📊 Principais Recursos
- **Upload de Arquivos Excel**: Suporte a arquivos de contas a pagar e contas pagas
- **Calendário Interativo**: Visualização mensal com valores diários clicáveis
- **Análise por Empresa**: Filtros e relatórios detalhados por empresa
- **Formatação Brasileira**: Datas (dd/mm/yyyy) e valores (R$ 1.234,56) no padrão nacional
- **Dashboard Completo**: Métricas principais e gráficos de análise

### 🗑️ Limpeza de Dados
- **Limpeza Seletiva**: Remove apenas contas a pagar ou contas pagas
- **Limpeza Total**: Remove todos os dados do usuário
- **Confirmação Visual**: Mostra quantidade de registros removidos

### 🔄 Verificação de Duplicatas
- **Detecção Automática**: Identifica registros duplicados antes da importação
- **Controle Configurável**: Opção para ativar/desativar verificação
- **Relatório Detalhado**: Mostra quantos registros foram ignorados por serem duplicatas

### 📅 Calendário Interativo
- **Dias Clicáveis**: Clique em qualquer dia para ver detalhes
- **Tabelas Detalhadas**: Visualização completa de fornecedores e valores
- **Totais Automáticos**: Soma de valores por dia automaticamente
- **Navegação Intuitiva**: Fácil navegação entre meses e anos

## 🛠️ Instalação

### Pré-requisitos
- Python 3.8+
- Conta no Supabase (banco de dados)

### Configuração
1. Clone o repositório:
```bash
git clone https://github.com/hoppemairon/calendario_financeiro.git
cd calendario_financeiro
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
Crie um arquivo `.env` na raiz do projeto:
```env
SUPABASE_URL=sua_url_do_supabase
SUPABASE_KEY=sua_chave_do_supabase
```

4. Execute o aplicativo:
```bash
streamlit run main_with_auth.py
```

## 📋 Como Usar

### 1. Upload de Arquivos
- **Contas a Pagar**: Faça upload dos arquivos Excel na seção correspondente
- **Contas Pagas**: Faça upload dos arquivos Excel de contas já pagas
- **Verificação**: Ative/desative a verificação de duplicatas conforme necessário

### 2. Limpeza de Dados
⚠️ **Atenção**: Operações de limpeza são irreversíveis!

- **Limpar Contas a Pagar**: Remove apenas registros de contas a pagar
- **Limpar Contas Pagas**: Remove apenas registros de contas pagas  
- **Limpar Todos os Dados**: Remove TODOS os dados do usuário

### 3. Visualização
- **Calendário**: Visualize valores por dia, clique para ver detalhes
- **Dados Atuais**: Tabelas completas com filtros por empresa
- **Por Empresa**: Análise específica por empresa
- **Exportar**: Gere relatórios em Excel

## 🔧 Estrutura do Projeto

```
calendario_financeiro/
├── main_with_auth.py           # Aplicação principal
├── src/
│   ├── auth/
│   │   └── auth_manager.py     # Gerenciamento de autenticação
│   ├── database/
│   │   ├── models.py           # Modelos de dados
│   │   └── supabase_client.py  # Cliente do banco de dados
│   ├── client_file_converter.py # Conversão de arquivos
│   ├── data_processor.py       # Processamento de dados
│   ├── payment_analyzer.py     # Análise de pagamentos
│   ├── report_generator.py     # Geração de relatórios
│   └── utils.py               # Utilitários e formatação brasileira
├── data/                      # Dados processados
├── reports/                   # Relatórios gerados
├── templates/                 # Modelos de arquivos
└── ArquivosModeloCliente/     # Arquivos de exemplo
```

## 🎯 Formatação Brasileira

O sistema utiliza formatação nacional em todos os aspectos:
- **Moeda**: R$ 1.234,56 (separador de milhares: ponto, decimais: vírgula)
- **Data**: 15/08/2025 (dia/mês/ano)
- **Meses**: Janeiro, Fevereiro, Março... (nomes em português)
- **Interface**: Textos e mensagens em português brasileiro

## 🔒 Verificação de Duplicatas

### Como Funciona
O sistema verifica duplicatas baseado em:
- **Empresa**: Nome da empresa (exato)
- **Valor**: Valor da conta (exato)
- **Data**: Data de vencimento/pagamento (exata)
- **Descrição**: Descrição da conta (exata)

### Configuração
- **Ativada por padrão**: A verificação vem habilitada
- **Configurável**: Pode ser desativada na seção "Configurações"
- **Relatório**: Mostra quantas duplicatas foram encontradas e ignoradas

## 📊 Métricas do Dashboard

O dashboard apresenta:
- **Total a Pagar**: Soma de todas as contas pendentes
- **Total Pago**: Soma de todas as contas quitadas
- **Saldo**: Diferença entre a pagar e pago
- **% Pago**: Percentual de contas quitadas
- **Empresas**: Número total de empresas cadastradas

## 🚨 Avisos Importantes

1. **Limpeza de Dados**: Operações são irreversíveis
2. **Backup**: Sempre faça backup antes de limpar dados
3. **Duplicatas**: Configure adequadamente para evitar dados desnecessários
4. **Formato**: Use arquivos Excel no formato esperado pelo sistema

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte, abra uma issue no repositório ou entre em contato através do email de suporte.

---

**Desenvolvido com ❤️ para otimizar o controle financeiro empresarial**
