# 🛠️ Scripts de Desenvolvimento

Esta pasta contém scripts utilizados durante o desenvolvimento e debugging do projeto.

## 📁 Estrutura

### 🐛 Scripts de Debug
- `debug_comparacao.py` - Compara consultas SQL diretas vs função Streamlit
- `debug_fornecedor.py` - Debug de processamento de fornecedores
- `debug_interface.py` - Debug da interface Streamlit
- `debug_valores.py` - Investiga discrepâncias de valores
- `debug_supabase.sql` - Queries SQL para diagnóstico do banco

### 🧪 Scripts de Teste
- `test_cadastro.py` - Testes de cadastro de usuários
- `test_conversao_fornecedor.py` - Testes de conversão de fornecedores
- `test_converter.py` - Testes do conversor de arquivos
- `test_novo_cadastro.py` - Testes de novo cadastro
- `test_supabase.py` - Testes de integração com Supabase
- `teste_final.py` - Teste final de funcionamento completo

### 🔧 Utilitários
- `analyze_file.py` - Análise de estrutura de arquivos
- `fix_rls.sql` - Fix aplicado para Row Level Security no Supabase

## 📝 Histórico de Problemas Resolvidos

### 1. Limite de 1000 Registros no Calendário (Agosto 2025)
**Sintomas**: Calendário mostrava dados apenas até o dia 20, faltando informações
**Causa**: Supabase limitando retorno a 1000 registros por query
**Solução**: Implementação de visualização semanal ao invés de mensal
**Arquivos**: `main_with_auth.py` - funções `calcular_semanas_do_mes()`, `mostrar_calendario_semanal()`

### 2. Renderização HTML no Streamlit (Agosto 2025) 
**Sintomas**: HTML aparecia como texto puro ao invés de ser renderizado
**Causa**: Formatação complexa de HTML com múltiplas quebras de linha
**Solução**: Substituição por componentes Streamlit nativos (st.metric, st.container)
**Arquivos**: `main_with_auth.py` - função `mostrar_dia_semana()`

### 3. Problema de Ordenação (Agosto 2025)
**Sintomas**: Interface mostrava apenas 10 registros de 20 para uma data específica
**Causa**: Função `buscar_contas_a_pagar()` sem ordenação determinística
**Solução**: Adicionada ordenação por `data_vencimento` e `id`
**Arquivos**: `debug_comparacao.py`, `teste_final.py`

### 4. Row Level Security (RLS)
**Sintomas**: API retornava 0 registros, mas SQL Editor mostrava dados
**Causa**: RLS bloqueando acesso via API
**Solução**: RLS desabilitado temporariamente
**Arquivos**: `debug_supabase.sql`, `fix_rls.sql`

## 🚨 Importante

Estes scripts são apenas para desenvolvimento e debugging. 
**NÃO** devem ser incluídos na aplicação de produção.
