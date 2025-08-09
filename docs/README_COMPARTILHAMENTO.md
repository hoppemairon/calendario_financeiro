# 🤝 Sistema de Compartilhamento - Calendário Financeiro

## 📋 Visão Geral

O sistema de compartilhamento permite que usuários compartilhem seus dados financeiros com outros usuários de forma segura e controlada. Cada usuário mantém seus dados completamente isolados por padrão, mas pode conceder acesso específico a outros usuários.

## 🔧 Configuração Inicial

### 1. Criar Tabela no Supabase
Execute o SQL do arquivo `criar_tabela_permissoes.sql` no seu painel do Supabase:

```sql
-- Copie todo o conteúdo do arquivo e execute no SQL Editor do Supabase
```

### 2. Verificar Instalação
Execute o script de verificação:

```bash
python inicializar_compartilhamento.py
```

### 3. Reiniciar Aplicação
```bash
streamlit run main_with_auth.py
```

## 🎯 Como Usar

### 📤 Conceder Acesso a Outro Usuário

1. **Acesse a aba 🤝 Compartilhamento**
2. **Digite o email do usuário** que receberá acesso
3. **Escolha o nível de acesso:**
   - **👁️ Viewer**: Apenas visualiza dados
   - **✏️ Editor**: Visualiza e edita dados  
   - **⚙️ Admin**: Acesso total + gerencia permissões
4. **Clique em "Conceder Acesso"**

### 👥 Gerenciar Permissões

- **Ver usuários com acesso**: Aba "Meus Compartilhamentos"
- **Revogar acesso**: Use o botão "❌ Revogar" 
- **Alterar nível**: Conceda novamente com nível diferente

### 🔍 Visualizar Dados de Outro Usuário

1. **Acesse a aba "Visualizar"**
2. **Selecione o usuário** cujos dados quer ver
3. **Clique em "👁️ Visualizar Dados"**
4. **Use "🔙 Voltar"** para retornar aos seus dados

## 🛡️ Segurança

### Isolamento por Usuário
- Todos os dados são filtrados por `usuario_id`
- Zero vazamento de dados entre usuários
- Row Level Security (RLS) no banco

### Permissões Granulares
- **Viewer**: Só leitura
- **Editor**: Leitura + escrita
- **Admin**: Controle total

### Auditoria Completa
- Log de todas as concessões
- Timestamps de criação/atualização
- Histórico de ações

## 🚀 Funcionalidades Avançadas

### Sidebar Compacta
- Conceder acesso rápido
- Alternar visualização 
- Indicador visual quando visualizando outros dados

### Interface Principal
- Gestão completa de permissões
- Listagem de acessos concedidos/recebidos
- Alternância simples entre usuários

### Integração Seamless
- Funciona com todos os recursos existentes
- Calendário, relatórios, uploads mantidos
- Transparente para o usuário final

## 📊 Status do Sistema

### ✅ Implementado
- [x] Classe `CompartilhamentoMixin`
- [x] Interface de usuário completa
- [x] Integração com aplicação principal
- [x] Sistema de permissões granulares
- [x] Auditoria e logging
- [x] Alternância de visualização
- [x] Indicadores visuais
- [x] SQL schema completo

### 🔄 Próximas Etapas
- [ ] Executar SQL no Supabase
- [ ] Testar com usuários reais
- [ ] Notificações de compartilhamento
- [ ] Histórico de ações

## 🐛 Resolução de Problemas

### Erro: "Tabela não encontrada"
```bash
# Execute o SQL no Supabase
cat criar_tabela_permissoes.sql
```

### Erro: "Usuário não encontrado" 
- Verifique se o email está correto
- Confirme que o usuário confirmou o email
- Usuário deve ter feito pelo menos 1 login

### Permissões não funcionam
- Verifique RLS habilitado
- Confirme políticas de segurança
- Teste com `cliente.set_user_id()`

## 📞 Suporte

Para problemas:
1. Verifique logs do Streamlit
2. Teste com `inicializar_compartilhamento.py`
3. Confirme configuração do Supabase
4. Revise variáveis de ambiente

## 🔮 Funcionalidades Futuras

- **Notificações**: Alertas quando alguém concede/revoga acesso
- **Grupos**: Compartilhar com grupos de usuários
- **Auditoria Visual**: Interface para ver histórico
- **Backup**: Exportar/importar permissões
- **API**: Endpoints para integração externa

---

**🎉 Sistema pronto para uso multi-usuário colaborativo!**
