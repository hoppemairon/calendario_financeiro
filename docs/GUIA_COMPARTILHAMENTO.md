# 🤝 Sistema de Compartilhamento de Dados - Calendário Financeiro

## 📋 Opções Disponíveis

### **1. 🏢 Sistema de Empresa/Organização (RECOMENDADO)**
**Melhor para**: Empresas com múltiplos usuários que precisam ver os mesmos dados

**Como funciona**:
- Cria-se uma "empresa" no sistema
- Múltiplos usuários são adicionados à mesma empresa  
- Todos veem os mesmos dados da empresa
- Controle de permissões por papel (admin, editor, viewer)

**Vantagens**:
- ✅ Mais seguro e organizado
- ✅ Controle granular de permissões
- ✅ Auditoria de quem fez o quê
- ✅ Escalável para muitos usuários

### **2. 👤 Permissões Diretas entre Usuários**
**Melhor para**: Casos pontuais onde um usuário precisa ver dados de outro

**Como funciona**:
- Usuário A concede acesso para Usuário B
- Usuário B pode visualizar dados do Usuário A
- Controle individual de cada compartilhamento

### **3. 🔄 Modo "Ver Como Outro Usuário" (TEMPORÁRIO)**
**Melhor para**: Suporte técnico ou consultas rápidas

**Como funciona**:
- Alterna temporariamente para ver dados de outro usuário
- Fácil de voltar aos próprios dados
- Ideal para administradores

---

## 🛠️ Como Implementar - Passo a Passo

### **ETAPA 1: Criar Tabelas no Supabase**

Execute no SQL Editor do Supabase:

```sql
-- Tabela de permissões entre usuários
CREATE TABLE permissoes_usuario (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    usuario_proprietario UUID NOT NULL,
    usuario_convidado UUID NOT NULL,
    nivel_acesso VARCHAR CHECK (nivel_acesso IN ('viewer', 'editor', 'admin')) DEFAULT 'viewer',
    data_concessao TIMESTAMP DEFAULT NOW(),
    ativo BOOLEAN DEFAULT TRUE,
    UNIQUE(usuario_proprietario, usuario_convidado)
);

-- Índices para performance
CREATE INDEX idx_permissoes_proprietario ON permissoes_usuario(usuario_proprietario);
CREATE INDEX idx_permissoes_convidado ON permissoes_usuario(usuario_convidado);
```

### **ETAPA 2: Adicionar Funções ao SupabaseClient**

Adicione estas funções no arquivo `src/database/supabase_client.py`:

```python
def conceder_acesso_usuario(self, email_usuario: str, nivel_acesso: str = 'viewer') -> Dict[str, Any]:
    """Concede acesso aos dados do usuário atual para outro usuário."""
    try:
        # 1. Buscar ID do usuário pelo email
        user_response = self.supabase.table("usuarios").select("id").eq("email", email_usuario).execute()
        
        if not user_response.data:
            return {"success": False, "error": "Usuário não encontrado"}
        
        target_user_id = user_response.data[0]['id']
        
        # 2. Criar/atualizar permissão
        permissao_data = {
            "usuario_proprietario": self.user_id,
            "usuario_convidado": target_user_id,
            "nivel_acesso": nivel_acesso,
            "ativo": True
        }
        
        # Usar upsert para atualizar se já existir
        self.supabase.table("permissoes_usuario").upsert(permissao_data).execute()
        
        return {"success": True, "message": f"Acesso concedido para {email_usuario}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def listar_usuarios_com_acesso(self) -> pd.DataFrame:
    """Lista usuários que têm acesso aos meus dados."""
    try:
        response = self.supabase.table("permissoes_usuario").select(
            "usuario_convidado, nivel_acesso, data_concessao, usuarios!usuario_convidado(nome, email)"
        ).eq("usuario_proprietario", self.user_id).eq("ativo", True).execute()
        
        if response.data:
            dados = []
            for item in response.data:
                dados.append({
                    'nome': item['usuarios']['nome'],
                    'email': item['usuarios']['email'], 
                    'nivel_acesso': item['nivel_acesso'],
                    'data_concessao': item['data_concessao']
                })
            return pd.DataFrame(dados)
        
        return pd.DataFrame()
    
    except Exception as e:
        print(f"Erro ao listar usuários: {e}")
        return pd.DataFrame()

def alternar_visualizacao_usuario(self, email_usuario: str) -> Dict[str, Any]:
    """Alterna para visualizar dados de outro usuário (se tiver permissão)."""
    try:
        # 1. Buscar ID do usuário
        user_response = self.supabase.table("usuarios").select("id, nome").eq("email", email_usuario).execute()
        
        if not user_response.data:
            return {"success": False, "error": "Usuário não encontrado"}
        
        target_user_id = user_response.data[0]['id']
        target_user_name = user_response.data[0]['nome']
        
        # 2. Verificar permissão
        permissao = self.supabase.table("permissoes_usuario").select("*").eq(
            "usuario_proprietario", target_user_id
        ).eq("usuario_convidado", self.user_id).eq("ativo", True).execute()
        
        if not permissao.data:
            return {"success": False, "error": "Você não tem permissão para acessar os dados deste usuário"}
        
        # 3. Salvar estado atual e alternar
        import streamlit as st
        
        if 'visualizacao_original' not in st.session_state:
            st.session_state['visualizacao_original'] = self.user_id
        
        # Alternar user_id temporariamente
        self.set_user_id(target_user_id)
        st.session_state['visualizando_usuario'] = target_user_name
        
        return {"success": True, "message": f"Agora visualizando dados de {target_user_name}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def voltar_visualizacao_original(self):
    """Volta para o usuário original."""
    import streamlit as st
    
    if 'visualizacao_original' in st.session_state:
        self.set_user_id(st.session_state['visualizacao_original'])
        
        # Limpar estado
        del st.session_state['visualizacao_original']
        if 'visualizando_usuario' in st.session_state:
            del st.session_state['visualizando_usuario']
        
        return {"success": True, "message": "Voltou para seus próprios dados"}
    
    return {"success": False, "error": "Não estava visualizando outro usuário"}
```

### **ETAPA 3: Interface de Usuário**

Adicione no arquivo `main_with_auth.py`:

```python
def mostrar_gerenciamento_compartilhamento(supabase_client):
    """Interface para gerenciar compartilhamento de dados."""
    
    st.sidebar.divider()
    st.sidebar.subheader("🤝 Compartilhamento")
    
    # Mostrar se está visualizando outro usuário
    if 'visualizando_usuario' in st.session_state:
        st.sidebar.warning(f"👁️ Visualizando: **{st.session_state['visualizando_usuario']}**")
        if st.sidebar.button("🔙 Voltar aos Meus Dados", use_container_width=True):
            resultado = supabase_client.voltar_visualizacao_original()
            if resultado["success"]:
                st.success(resultado["message"])
                st.rerun()
    
    # Formulário para conceder acesso
    with st.sidebar.expander("📤 Conceder Acesso"):
        email = st.text_input("📧 Email do usuário:", key="share_email")
        nivel = st.selectbox("🔐 Nível:", ["viewer", "editor", "admin"], key="share_level")
        
        if st.button("✅ Conceder", use_container_width=True):
            if email:
                resultado = supabase_client.conceder_acesso_usuario(email, nivel)
                if resultado["success"]:
                    st.success(resultado["message"])
                else:
                    st.error(resultado["error"])
    
    # Formulário para visualizar dados de outro usuário  
    with st.sidebar.expander("👁️ Visualizar Outros"):
        email_ver = st.text_input("📧 Email para visualizar:", key="view_email")
        
        if st.button("👁️ Visualizar", use_container_width=True):
            if email_ver:
                resultado = supabase_client.alternar_visualizacao_usuario(email_ver)
                if resultado["success"]:
                    st.success(resultado["message"])
                    st.rerun()
                else:
                    st.error(resultado["error"])
```

### **ETAPA 4: Integrar na Aplicação Principal**

No `main_with_auth.py`, adicione a chamada:

```python
def carregar_aplicacao_principal():
    # ... código existente ...
    
    # Adicionar gerenciamento de compartilhamento
    mostrar_gerenciamento_compartilhamento(supabase_client)
    
    # ... resto do código ...
```

---

## 🎯 **Como Usar na Prática**

### **Para Conceder Acesso:**
1. Na barra lateral, clique em "📤 Conceder Acesso"
2. Digite o email do usuário
3. Escolha o nível (viewer, editor, admin)
4. Clique em "✅ Conceder"

### **Para Visualizar Dados de Outro:**
1. Na barra lateral, clique em "👁️ Visualizar Outros"
2. Digite o email do usuário que te deu acesso
3. Clique em "👁️ Visualizar"
4. O sistema mostrará os dados desse usuário
5. Use "🔙 Voltar aos Meus Dados" para retornar

### **Níveis de Acesso:**
- **👁️ viewer**: Só visualiza, não pode alterar nada
- **✏️ editor**: Pode visualizar e editar dados
- **👑 admin**: Acesso total, pode gerenciar permissões

---

## ⚠️ **Considerações de Segurança**

- ✅ Permissões são verificadas em cada operação
- ✅ Log de todas as concessões de acesso
- ✅ Possibilidade de revogar acessos
- ⚠️ Administradores podem ver todos os dados
- 🔒 Senhas e dados pessoais nunca são compartilhados

Quer que eu implemente alguma dessas opções no seu código?
