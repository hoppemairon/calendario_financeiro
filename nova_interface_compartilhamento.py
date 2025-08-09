def mostrar_interface_compartilhamento(supabase_client: SupabaseClient):
    """Interface para gerenciar licenças de acesso entre usuários."""
    st.header("👥 Gerenciamento de Licenças de Usuários")
    
    # Mostrar status de admin
    st.success("🔧 **ADMIN GERAL** - Gerencie qual usuário pode ver **TODAS as movimentações** de outros usuários")
    
    # Buscar dados necessários
    usuarios_df = supabase_client.listar_todos_usuarios()
    
    # Estatísticas gerais do sistema
    st.subheader("📊 Estatísticas do Sistema")
    col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
    
    with col_stats1:
        st.metric("👥 Total de Usuários", len(usuarios_df))
    
    with col_stats2:
        df_todas_a_pagar = supabase_client.buscar_todas_contas_a_pagar()
        st.metric("📋 Total Contas a Pagar", len(df_todas_a_pagar))
    
    with col_stats3:
        df_todas_pagas = supabase_client.buscar_todas_contas_pagas()
        st.metric("✅ Total Contas Pagas", len(df_todas_pagas))
    
    with col_stats4:
        empresas = supabase_client.listar_todas_empresas()
        st.metric("🏢 Total de Empresas", len(empresas))
    
    st.divider()
    
    # Interface para conceder licença
    st.subheader("🤝 Conceder Licença de Acesso Total")
    
    # Explicação clara
    st.info("""
    💡 **Como funciona a licença:**
    - Selecione o **usuário que vai ganhar acesso** 
    - Selecione o **usuário proprietário dos dados**
    - O primeiro usuário poderá ver **TODAS as movimentações (contas a pagar e pagas)** do segundo usuário
    """)
    
    if not usuarios_df.empty:
        with st.form("conceder_licenca"):
            col1, col2, col3 = st.columns([4, 4, 2])
            
            with col1:
                # Usuário que VAI ACESSAR
                usuarios_options = [""] + [f"{row['nome']} ({row['email']})" for _, row in usuarios_df.iterrows()]
                usuario_acessante = st.selectbox(
                    "👤 Usuário que vai ganhar acesso:", 
                    usuarios_options, 
                    help="Este usuário poderá ver os dados de outro usuário"
                )
            
            with col2:
                # Usuário PROPRIETÁRIO DOS DADOS  
                usuario_proprietario = st.selectbox(
                    "🗂️ Usuário proprietário dos dados:", 
                    usuarios_options, 
                    help="Usuário cujas movimentações serão visualizadas"
                )
            
            with col3:
                # Nível de acesso
                nivel_acesso = st.selectbox("🔐 Nível:", ["viewer", "editor"], index=0)
            
            conceder_button = st.form_submit_button("🤝 Conceder Licença", type="primary", use_container_width=True)
            
            if conceder_button:
                if usuario_acessante and usuario_proprietario and usuario_acessante != usuario_proprietario:
                    # Extrair dados dos usuários
                    email_acessante = usuario_acessante.split("(")[1].replace(")", "")
                    email_proprietario = usuario_proprietario.split("(")[1].replace(")", "")
                    
                    usuario_acessante_info = usuarios_df[usuarios_df['email'] == email_acessante]
                    usuario_proprietario_info = usuarios_df[usuarios_df['email'] == email_proprietario]
                    
                    if not usuario_acessante_info.empty and not usuario_proprietario_info.empty:
                        # Criar licença usando session_state temporário
                        if 'licencas_usuarios' not in st.session_state:
                            st.session_state['licencas_usuarios'] = []
                        
                        licenca = {
                            "usuario_acessante_id": usuario_acessante_info.iloc[0]['id'],
                            "usuario_acessante_nome": usuario_acessante_info.iloc[0]['nome'],
                            "usuario_acessante_email": email_acessante,
                            "usuario_proprietario_id": usuario_proprietario_info.iloc[0]['id'],
                            "usuario_proprietario_nome": usuario_proprietario_info.iloc[0]['nome'],
                            "usuario_proprietario_email": email_proprietario,
                            "nivel_acesso": nivel_acesso,
                            "concedido_por": supabase_client.user_id,
                            "ativo": True,
                            "data_concessao": datetime.now().isoformat()
                        }
                        
                        # Remover licença existente se houver
                        st.session_state['licencas_usuarios'] = [
                            l for l in st.session_state['licencas_usuarios'] 
                            if not (l['usuario_acessante_id'] == licenca['usuario_acessante_id'] and 
                                   l['usuario_proprietario_id'] == licenca['usuario_proprietario_id'])
                        ]
                        
                        # Adicionar nova licença
                        st.session_state['licencas_usuarios'].append(licenca)
                        
                        st.success(f"""
                        ✅ **Licença concedida com sucesso!**
                        
                        **{usuario_acessante_info.iloc[0]['nome']}** agora pode visualizar **TODAS as movimentações** de **{usuario_proprietario_info.iloc[0]['nome']}**
                        """)
                        st.rerun()
                    else:
                        st.error("❌ Usuários não encontrados")
                elif usuario_acessante == usuario_proprietario:
                    st.error("❌ Um usuário não pode ser proprietário e acessante ao mesmo tempo")
                else:
                    st.error("❌ Selecione ambos os usuários")
    
    st.divider()
    
    # Mostrar licenças existentes
    st.subheader("📋 Licenças Ativas no Sistema")
    
    licencas_temp = st.session_state.get('licencas_usuarios', [])
    if licencas_temp:
        licencas_ativas = [l for l in licencas_temp if l['ativo']]
        
        if licencas_ativas:
            for idx, licenca in enumerate(licencas_ativas):
                with st.container():
                    col_info, col_action = st.columns([5, 1])
                    
                    with col_info:
                        st.write(f"👤 **{licenca['usuario_acessante_nome']}** ➡️ 🗂️ **{licenca['usuario_proprietario_nome']}**")
                        st.caption(f"📧 {licenca['usuario_acessante_email']} pode ver **TODAS as movimentações** de {licenca['usuario_proprietario_email']}")
                        st.caption(f"🔐 Nível: {licenca['nivel_acesso']} | 📅 Desde: {licenca['data_concessao'][:10]}")
                    
                    with col_action:
                        if st.button("🗑️", key=f"revogar_licenca_{idx}", help="Revogar esta licença"):
                            # Encontrar e desativar licença
                            for i, l in enumerate(st.session_state['licencas_usuarios']):
                                if (l['usuario_acessante_id'] == licenca['usuario_acessante_id'] and 
                                    l['usuario_proprietario_id'] == licenca['usuario_proprietario_id']):
                                    st.session_state['licencas_usuarios'][i]['ativo'] = False
                                    break
                            
                            st.success(f"🗑️ Licença revogada! **{licenca['usuario_acessante_nome']}** não pode mais acessar dados de **{licenca['usuario_proprietario_nome']}**")
                            st.rerun()
                    
                    st.divider()
        else:
            st.info("📝 Todas as licenças foram revogadas")
    else:
        st.info("📝 Nenhuma licença configurada ainda")
    
    # Seção de usuários disponíveis com estatísticas
    st.divider()
    st.subheader("👥 Usuários e suas Movimentações")
    
    if not usuarios_df.empty:
        # Calcular estatísticas para cada usuário
        usuarios_com_stats = []
        
        with st.spinner("📊 Calculando estatísticas dos usuários..."):
            for _, user in usuarios_df.iterrows():
                try:
                    # Buscar quantos registros cada usuário tem
                    response_a_pagar = supabase_client.supabase.table("contas_a_pagar").select("id").eq("usuario_id", user['id']).execute()
                    response_pagas = supabase_client.supabase.table("contas_pagas").select("id").eq("usuario_id", user['id']).execute()
                    
                    user_a_pagar = len(response_a_pagar.data or [])
                    user_pagas = len(response_pagas.data or [])
                    
                    usuarios_com_stats.append({
                        'Nome': user['nome'],
                        'Email': user['email'],
                        'Empresa Padrão': user.get('empresa_padrao', 'N/A'),
                        'Contas a Pagar': user_a_pagar,
                        'Contas Pagas': user_pagas,
                        'Total Movimentações': user_a_pagar + user_pagas
                    })
                except Exception as e:
                    print(f"Erro ao buscar dados do usuário {user['nome']}: {e}")
        
        if usuarios_com_stats:
            df_stats = pd.DataFrame(usuarios_com_stats)
            # Ordenar por total de movimentações
            df_stats = df_stats.sort_values('Total Movimentações', ascending=False)
            
            st.dataframe(
                df_stats, 
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Total Movimentações': st.column_config.NumberColumn(
                        'Total Movimentações',
                        help="Soma de contas a pagar + contas pagas",
                        format="%d"
                    )
                }
            )
        else:
            st.warning("⚠️ Erro ao calcular estatísticas dos usuários")
    else:
        st.info("❌ Nenhum usuário encontrado")
