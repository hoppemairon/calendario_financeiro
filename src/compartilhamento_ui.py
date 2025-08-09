"""
Interface de usuário para compartilhamento de dados.
"""

import streamlit as st
import pandas as pd
from src.database.supabase_client import SupabaseClient


def mostrar_interface_compartilhamento(supabase_client: SupabaseClient):
    """Interface para gerenciar compartilhamento de dados."""
    
    st.subheader("🤝 Compartilhamento de Dados")
    st.info("💡 Compartilhe seus dados financeiros com outros usuários ou acesse dados compartilhados com você.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📤 Conceder Acesso", "👥 Meus Compartilhamentos", "🔍 Meus Acessos", "👁️ Visualizar"])
    
    with tab1:
        st.markdown("### 📤 Conceder Acesso aos Meus Dados")
        
        with st.form("conceder_acesso"):
            st.markdown("**Permita que outro usuário visualize seus dados financeiros:**")
            
            email_usuario = st.text_input(
                "📧 Email do usuário:", 
                placeholder="usuario@exemplo.com",
                help="Digite o email do usuário que receberá acesso"
            )
            
            nivel_acesso = st.selectbox(
                "🔐 Nível de acesso:", 
                ["viewer", "editor", "admin"],
                help="""
                • **viewer**: Só visualiza dados, não pode alterar
                • **editor**: Pode visualizar e editar dados  
                • **admin**: Acesso total, incluindo gerenciar permissões
                """
            )
            
            col1, col2 = st.columns([2, 1])
            with col1:
                conceder = st.form_submit_button("✅ Conceder Acesso", type="primary", use_container_width=True)
            
            with col2:
                revogar = st.form_submit_button("❌ Revogar", type="secondary", use_container_width=True)
            
            if conceder and email_usuario:
                with st.spinner("Processando..."):
                    resultado = supabase_client.conceder_acesso_usuario(email_usuario, nivel_acesso)
                    
                    if resultado["success"]:
                        st.success(f"✅ {resultado['message']}")
                        st.rerun()
                    else:
                        st.error(f"❌ {resultado['error']}")
            
            elif revogar and email_usuario:
                with st.spinner("Revogando acesso..."):
                    resultado = supabase_client.revogar_acesso_usuario(email_usuario)
                    
                    if resultado["success"]:
                        st.success(f"✅ {resultado['message']}")
                        st.rerun()
                    else:
                        st.error(f"❌ {resultado['error']}")
    
    with tab2:
        st.markdown("### 👥 Usuários com Acesso aos Meus Dados")
        
        df_compartilhamentos = supabase_client.listar_usuarios_com_acesso()
        
        if not df_compartilhamentos.empty:
            # Formatar dados para exibição
            df_display = df_compartilhamentos.copy()
            df_display['data_concessao'] = pd.to_datetime(df_display['data_concessao']).dt.strftime('%d/%m/%Y')
            
            # Renomear colunas
            df_display = df_display.rename(columns={
                'nome': 'Nome',
                'email': 'Email',
                'nivel_acesso': 'Nível',
                'data_concessao': 'Data'
            })
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            st.success(f"📊 **{len(df_compartilhamentos)} usuário(s)** têm acesso aos seus dados")
        else:
            st.info("ℹ️ Nenhum usuário tem acesso aos seus dados no momento")
            st.markdown("💡 Use a aba **'📤 Conceder Acesso'** para compartilhar seus dados")
    
    with tab3:
        st.markdown("### 🔍 Dados que Posso Acessar")
        
        df_meus_acessos = supabase_client.listar_meus_acessos()
        
        if not df_meus_acessos.empty:
            # Formatar dados para exibição
            df_display = df_meus_acessos.copy()
            df_display['data_concessao'] = pd.to_datetime(df_display['data_concessao']).dt.strftime('%d/%m/%Y')
            
            # Renomear colunas (remover usuario_id da exibição)
            df_display = df_display[['nome', 'email', 'nivel_acesso', 'data_concessao']].rename(columns={
                'nome': 'Proprietário',
                'email': 'Email',
                'nivel_acesso': 'Meu Nível',
                'data_concessao': 'Desde'
            })
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            st.success(f"🎯 **Você tem acesso** aos dados de {len(df_meus_acessos)} usuário(s)")
        else:
            st.info("ℹ️ Você não tem acesso aos dados de outros usuários")
            st.markdown("💡 Solicite acesso a outros usuários para aparecerem aqui")
    
    with tab4:
        st.markdown("### 👁️ Visualizar Dados de Outro Usuário")
        
        # Verificar se está visualizando outro usuário
        if 'visualizando_usuario' in st.session_state:
            st.warning(f"🔍 **Visualizando dados de**: {st.session_state['visualizando_usuario']}")
            st.info(f"📧 Email: {st.session_state['visualizando_email']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔙 Voltar aos Meus Dados", type="primary", use_container_width=True):
                    resultado = supabase_client.voltar_visualizacao_original()
                    if resultado["success"]:
                        st.success(resultado["message"])
                        st.rerun()
                    else:
                        st.error(resultado["error"])
            
            with col2:
                st.button("🔄 Atualizar", use_container_width=True, on_click=lambda: st.rerun())
        
        else:
            # Mostrar usuários disponíveis para visualizar
            df_acessos = supabase_client.listar_meus_acessos()
            
            if not df_acessos.empty:
                st.markdown("**Selecione o usuário cujos dados deseja visualizar:**")
                
                # Criar lista de opções
                opcoes = []
                emails = []
                for _, row in df_acessos.iterrows():
                    opcao = f"{row['nome']} ({row['email']}) - {row['nivel_acesso']}"
                    opcoes.append(opcao)
                    emails.append(row['email'])
                
                usuario_selecionado_idx = st.selectbox(
                    "Escolha o usuário:", 
                    range(len(opcoes)),
                    format_func=lambda x: opcoes[x],
                    help="Você só pode visualizar dados de usuários que te concederam acesso"
                )
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    if st.button("👁️ Visualizar Dados Deste Usuário", type="primary", use_container_width=True):
                        email_selecionado = emails[usuario_selecionado_idx]
                        
                        with st.spinner("Alternando visualização..."):
                            resultado = supabase_client.alternar_visualizacao_usuario(email_selecionado)
                            
                            if resultado["success"]:
                                st.success(resultado["message"])
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(resultado["error"])
                
                with col2:
                    st.button("🔄 Atualizar Lista", use_container_width=True, on_click=lambda: st.rerun())
                
                st.markdown("---")
                st.info("""
                **📋 Como funciona:**
                1. Clique em **'👁️ Visualizar Dados'** para alternar
                2. Você verá todos os dados financeiros do usuário selecionado
                3. Use **'🔙 Voltar aos Meus Dados'** para retornar aos seus dados
                """)
            
            else:
                st.info("ℹ️ Você não tem permissão para visualizar dados de outros usuários")
                st.markdown("💡 Solicite acesso na aba **'🔍 Meus Acessos'** primeiro")


def mostrar_indicador_visualizacao(supabase_client: SupabaseClient):
    """Mostra indicador na sidebar se estiver visualizando outro usuário."""
    
    if 'visualizando_usuario' in st.session_state:
        st.sidebar.warning(f"👁️ **Visualizando**: {st.session_state['visualizando_usuario']}")
        
        if st.sidebar.button("🔙 Voltar aos Meus Dados", use_container_width=True, type="primary"):
            resultado = supabase_client.voltar_visualizacao_original()
            if resultado["success"]:
                st.success(resultado["message"])
                st.rerun()


def mostrar_compartilhamento_compacto(supabase_client: SupabaseClient):
    """Versão compacta do compartilhamento para a sidebar."""
    
    st.sidebar.divider()
    st.sidebar.subheader("🤝 Compartilhamento")
    
    # Mostrar se está visualizando outro usuário
    mostrar_indicador_visualizacao(supabase_client)
    
    # Formulário compacto para conceder acesso
    with st.sidebar.expander("📤 Conceder Acesso"):
        email = st.text_input("📧 Email:", key="share_email_compact", placeholder="usuario@exemplo.com")
        nivel = st.selectbox("🔐 Nível:", ["viewer", "editor", "admin"], key="share_level_compact")
        
        if st.button("✅ Conceder", key="conceder_compact", use_container_width=True):
            if email:
                resultado = supabase_client.conceder_acesso_usuario(email, nivel)
                if resultado["success"]:
                    st.success("✅ Acesso concedido!")
                else:
                    st.error(resultado["error"])
    
    # Formulário compacto para visualizar dados
    with st.sidebar.expander("👁️ Visualizar Dados"):
        df_acessos = supabase_client.listar_meus_acessos()
        
        if not df_acessos.empty:
            email_ver = st.selectbox(
                "Usuário:", 
                df_acessos['email'].tolist(),
                key="view_email_compact",
                format_func=lambda x: df_acessos[df_acessos['email'] == x]['nome'].iloc[0]
            )
            
            if st.button("👁️ Visualizar", key="visualizar_compact", use_container_width=True):
                resultado = supabase_client.alternar_visualizacao_usuario(email_ver)
                if resultado["success"]:
                    st.success("✅ Visualização alterada!")
                    st.rerun()
                else:
                    st.error(resultado["error"])
        else:
            st.info("Sem acessos disponíveis")
