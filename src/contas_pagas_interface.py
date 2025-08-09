"""
Interface para validação e análise de contas pagas.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import io

from contas_pagas_validator import ContasPagasValidator, ComparadorContasAPagarVsPagas
from utils import formatar_moeda_brasileira, formatar_data_brasileira


def mostrar_interface_validacao_contas_pagas(supabase_client):
    """
    Interface principal para validação de contas pagas.
    """
    
    st.header("🔍 Validação de Contas Pagas")
    
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Validação", "⚖️ Comparação A Pagar vs Pagas", "📊 Relatórios"])
    
    with tab1:
        mostrar_upload_validacao(supabase_client)
    
    with tab2:
        mostrar_comparacao_datasets(supabase_client)
    
    with tab3:
        mostrar_relatorios_diferencas(supabase_client)


def mostrar_upload_validacao(supabase_client):
    """
    Interface para upload e validação do arquivo de contas pagas.
    """
    
    st.subheader("📤 Upload do Arquivo de Contas Pagas")
    
    # Upload do arquivo
    uploaded_file = st.file_uploader(
        "Selecione o arquivo de contas pagas:",
        type=['xlsx', 'xls', 'csv'],
        help="Formatos suportados: Excel (.xlsx, .xls) ou CSV"
    )
    
    if uploaded_file:
        validator = ContasPagasValidator()
        
        # Mostrar informações do arquivo
        st.info(f"📁 **Arquivo:** {uploaded_file.name} ({uploaded_file.size} bytes)")
        
        try:
            # Ler arquivo
            if uploaded_file.name.endswith('.csv'):
                df_original = pd.read_csv(uploaded_file)
            else:
                df_original = pd.read_excel(uploaded_file)
            
            st.success(f"✅ Arquivo carregado com sucesso! {len(df_original)} registros encontrados")
            
            # Detectar formato
            formato = validator.detectar_formato(df_original)
            st.info(f"🔍 **Formato detectado:** {formato}")
            
            # Mostrar preview dos dados originais
            with st.expander("👁️ Preview dos Dados Originais"):
                st.dataframe(df_original.head(10), use_container_width=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de registros", len(df_original))
                with col2:
                    st.metric("Total de colunas", len(df_original.columns))
                with col3:
                    if 'Saída' in df_original.columns:
                        valor_total = df_original['Saída'].fillna(0).sum()
                        st.metric("Valor Total (Saída)", formatar_moeda_brasileira(valor_total))
            
            # Validar colunas
            validacao_colunas = validator.validar_colunas_obrigatorias(df_original, formato)
            
            if validacao_colunas['valido']:
                st.success("✅ Todas as colunas obrigatórias estão presentes!")
            else:
                st.error(f"❌ Colunas faltando: {', '.join(validacao_colunas['colunas_faltando'])}")
            
            # Mostrar colunas encontradas
            if validacao_colunas['colunas_encontradas']:
                st.info(f"📋 **Colunas encontradas:** {', '.join(validacao_colunas['colunas_encontradas'])}")
            
            # Mostrar warnings
            for warning in validacao_colunas['warnings']:
                st.warning(f"⚠️ {warning}")
            
            # Converter dados se formato suportado
            if formato == 'novo_modelo' and validacao_colunas['valido']:
                st.divider()
                st.subheader("🔄 Conversão para Formato Padrão")
                
                df_convertido = validator.converter_novo_modelo(df_original)
                
                if not df_convertido.empty:
                    st.success(f"✅ Conversão realizada! {len(df_convertido)} registros convertidos")
                    
                    # Validar dados convertidos
                    validacao_dados = validator.validar_dados_convertidos(df_convertido)
                    
                    # Mostrar estatísticas da validação
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Registros válidos", validacao_dados['registros_validos'])
                    with col2:
                        st.metric("Total registros", validacao_dados['total_registros'])
                    with col3:
                        percentual_validos = (validacao_dados['registros_validos'] / validacao_dados['total_registros']) * 100
                        st.metric("% Válidos", f"{percentual_validos:.1f}%")
                    with col4:
                        if validacao_dados['estatisticas'].get('valor_total'):
                            st.metric("Valor Total", formatar_moeda_brasileira(validacao_dados['estatisticas']['valor_total']))
                    
                    # Mostrar problemas e warnings
                    if validacao_dados['problemas']:
                        st.error("🚨 **Problemas encontrados:**")
                        for problema in validacao_dados['problemas']:
                            st.error(f"• {problema}")
                    
                    if validacao_dados['warnings']:
                        st.warning("⚠️ **Atenções:**")
                        for warning in validacao_dados['warnings']:
                            st.warning(f"• {warning}")
                    
                    # Preview dos dados convertidos
                    with st.expander("👁️ Preview dos Dados Convertidos"):
                        st.dataframe(df_convertido.head(10), use_container_width=True)
                    
                    # Mostrar distribuição por categoria
                    if 'categoria' in df_convertido.columns:
                        st.subheader("📊 Distribuição por Categoria")
                        
                        cat_stats = df_convertido.groupby('categoria').agg({
                            'valor': ['sum', 'count'],
                        }).round(2)
                        
                        cat_stats.columns = ['Valor Total', 'Quantidade']
                        cat_stats = cat_stats.sort_values('Valor Total', ascending=False)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig = px.pie(
                                values=cat_stats['Valor Total'], 
                                names=cat_stats.index,
                                title="Distribuição de Valores por Categoria"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            st.dataframe(cat_stats, use_container_width=True)
                    
                    # Mostrar evolução temporal
                    if 'data_pagamento' in df_convertido.columns:
                        st.subheader("📈 Evolução Temporal dos Pagamentos")
                        
                        df_temp = df_convertido.copy()
                        df_temp['mes_ano'] = df_temp['data_pagamento'].dt.to_period('M')
                        
                        evolucao = df_temp.groupby('mes_ano')['valor'].agg(['sum', 'count']).reset_index()
                        evolucao['mes_ano_str'] = evolucao['mes_ano'].astype(str)
                        
                        fig = make_subplots(
                            rows=2, cols=1,
                            subplot_titles=('Valor Total por Mês', 'Quantidade de Pagamentos por Mês'),
                            vertical_spacing=0.1
                        )
                        
                        fig.add_trace(
                            go.Bar(x=evolucao['mes_ano_str'], y=evolucao['sum'], name='Valor Total'),
                            row=1, col=1
                        )
                        
                        fig.add_trace(
                            go.Bar(x=evolucao['mes_ano_str'], y=evolucao['count'], name='Quantidade'),
                            row=2, col=1
                        )
                        
                        fig.update_layout(height=600, showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Botão para salvar no banco
                    st.divider()
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        if st.button("💾 Salvar Contas Pagas no Banco", type="primary", use_container_width=True):
                            with st.spinner("Salvando dados no banco..."):
                                try:
                                    # Usar o método mais eficiente para múltiplas inserções
                                    resultado = supabase_client.inserir_contas_pagas(
                                        df=df_convertido,
                                        arquivo_origem=uploaded_file.name,
                                        verificar_duplicatas=True
                                    )
                                    
                                    if resultado['success']:
                                        st.success(f"✅ {resultado['registros_inseridos']} contas pagas salvas com sucesso!")
                                        if resultado.get('duplicatas_ignoradas', 0) > 0:
                                            st.info(f"ℹ️ {resultado['duplicatas_ignoradas']} duplicatas foram ignoradas")
                                        st.balloons()
                                    else:
                                        st.error(f"❌ Erro ao salvar: {resultado.get('message', resultado.get('error', 'Erro desconhecido'))}")
                                        
                                except Exception as e:
                                    st.error(f"❌ Erro ao salvar no banco: {str(e)}")
                    
                    with col2:
                        # Botão para download dos dados convertidos
                        excel_buffer = io.BytesIO()
                        df_convertido.to_excel(excel_buffer, index=False, engine='openpyxl')
                        excel_buffer.seek(0)
                        
                        st.download_button(
                            label="📥 Download Excel",
                            data=excel_buffer.getvalue(),
                            file_name=f"contas_pagas_convertido_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    
                    with col3:
                        # Botão para download CSV
                        csv_buffer = io.StringIO()
                        df_convertido.to_csv(csv_buffer, index=False)
                        
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv_buffer.getvalue(),
                            file_name=f"contas_pagas_convertido_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                
                else:
                    st.error("❌ Falha na conversão dos dados")
            
            elif formato == 'desconhecido':
                st.error("❌ Formato de arquivo não reconhecido")
                st.info("📋 **Formatos suportados:**")
                st.info("• **Novo Modelo:** IdBanco, Datapagamento, Saída, DescriçãoConta, Histórico")
                st.info("• **Formato Padrão:** data_pagamento, valor, empresa, fornecedor, descricao")
        
        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo: {str(e)}")


def mostrar_comparacao_datasets(supabase_client):
    """
    Interface para comparação entre contas a pagar e pagas.
    """
    
    st.subheader("⚖️ Comparação: Contas a Pagar vs Contas Pagas")
    
    # Buscar dados do banco
    with st.spinner("Carregando dados do banco..."):
        df_a_pagar = supabase_client.buscar_contas_a_pagar()
        df_pagas = supabase_client.buscar_contas_pagas()
    
    if df_a_pagar.empty and df_pagas.empty:
        st.info("ℹ️ Nenhum dado encontrado. Faça upload dos arquivos primeiro.")
        return
    
    # Mostrar estatísticas básicas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "📋 Contas a Pagar", 
            len(df_a_pagar),
            delta=f"{formatar_moeda_brasileira(df_a_pagar['valor'].sum()) if not df_a_pagar.empty else 'R$ 0,00'}"
        )
    
    with col2:
        st.metric(
            "✅ Contas Pagas", 
            len(df_pagas),
            delta=f"{formatar_moeda_brasileira(df_pagas['valor'].sum()) if not df_pagas.empty else 'R$ 0,00'}"
        )
    
    with col3:
        if not df_a_pagar.empty and not df_pagas.empty:
            diferenca = df_pagas['valor'].sum() - df_a_pagar['valor'].sum()
            st.metric(
                "💰 Diferença", 
                formatar_moeda_brasileira(abs(diferenca)),
                delta=f"{'Superávit' if diferenca > 0 else 'Déficit'}"
            )
    
    if not df_a_pagar.empty and not df_pagas.empty:
        # Executar comparação
        comparador = ComparadorContasAPagarVsPagas()
        
        with st.spinner("Analisando correspondências..."):
            resultado_comparacao = comparador.comparar_datasets(df_a_pagar, df_pagas)
        
        # Mostrar resumo da comparação
        st.divider()
        st.subheader("📊 Resumo da Comparação")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("🎯 Exatas", resultado_comparacao['resumo']['correspondencias_exatas'])
        with col2:
            st.metric("� Por Histórico", resultado_comparacao['resumo'].get('correspondencias_por_historico', 0))
        with col3:
            st.metric("�🔍 Aproximadas", resultado_comparacao['resumo']['correspondencias_aproximadas'])
        with col4:
            st.metric("❌ Não Pagas", resultado_comparacao['resumo']['contas_nao_pagas'])
        with col5:
            st.metric("❓ Sem Conta", resultado_comparacao['resumo']['pagamentos_sem_conta'])
        
        # Tabs para diferentes análises
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🎯 Correspondências Exatas", 
            "� Por Histórico 100%",
            "🆔 Por ID",
            "🔑 Por Chave",
            "❌ Contas Não Pagas",
            "❓ Pagamentos Sem Conta"
        ])
        
        with tab1:
            if not resultado_comparacao['correspondencias_exatas'].empty:
                st.success(f"✅ {len(resultado_comparacao['correspondencias_exatas'])} correspondências exatas encontradas")
                
                # Mostrar estatísticas por tipo
                por_id = len(resultado_comparacao.get('correspondencias_por_id', pd.DataFrame()))
                por_historico = len(resultado_comparacao.get('correspondencias_por_historico', pd.DataFrame()))
                por_chave = len(resultado_comparacao.get('correspondencias_por_chave', pd.DataFrame()))
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"🆔 Por ID: {por_id}")
                with col2:
                    st.info(f"📋 Por Histórico: {por_historico}")
                with col3:
                    st.info(f"🔑 Por Chave: {por_chave}")
                
                st.dataframe(resultado_comparacao['correspondencias_exatas'], use_container_width=True)
            else:
                st.info("ℹ️ Nenhuma correspondência exata encontrada")
        
        with tab2:
            # Tab específica para correspondências por histórico
            correspondencias_historico = resultado_comparacao.get('correspondencias_por_historico', pd.DataFrame())
            if not correspondencias_historico.empty:
                st.success(f"📋 {len(correspondencias_historico)} correspondências por histórico 100% exato encontradas!")
                
                st.info("✨ **Históricos que bateram perfeitamente:**")
                
                # Mostrar apenas as colunas mais importantes
                colunas_historico = []
                for col in ['historico_a_pagar', 'valor_a_pagar', 'descricao_a_pagar', 
                           'historico_pagas', 'valor_pagas', 'descricao_pagas']:
                    if col in correspondencias_historico.columns:
                        colunas_historico.append(col)
                
                if colunas_historico:
                    st.dataframe(correspondencias_historico[colunas_historico], use_container_width=True)
                else:
                    st.dataframe(correspondencias_historico, use_container_width=True)
                
                # Estatísticas das correspondências por histórico
                if 'valor_a_pagar' in correspondencias_historico.columns:
                    valor_total = correspondencias_historico['valor_a_pagar'].sum()
                    st.metric("💰 Valor Total das Correspondências por Histórico", f"R$ {valor_total:,.2f}")
                
            else:
                st.info("ℹ️ Nenhuma correspondência por histórico 100% encontrada")
        
        with tab3:
            # Tab para correspondências por ID
            correspondencias_id = resultado_comparacao.get('correspondencias_por_id', pd.DataFrame())
            if not correspondencias_id.empty:
                st.success(f"🆔 {len(correspondencias_id)} correspondências por ID encontradas")
                st.dataframe(correspondencias_id, use_container_width=True)
            else:
                st.info("ℹ️ Nenhuma correspondência por ID encontrada")
        
        with tab4:
            # Tab para correspondências por chave
            correspondencias_chave = resultado_comparacao.get('correspondencias_por_chave', pd.DataFrame())
            if not correspondencias_chave.empty:
                st.success(f"🔑 {len(correspondencias_chave)} correspondências por chave (descrição + valor) encontradas")
                st.dataframe(correspondencias_chave, use_container_width=True)
            else:
                st.info("ℹ️ Nenhuma correspondência por chave encontrada")
        
        with tab5:
            # Contas Não Pagas
            if not resultado_comparacao['contas_nao_pagas'].empty:
                st.error(f"❌ {len(resultado_comparacao['contas_nao_pagas'])} contas ainda não foram pagas")
                
                # Análise por empresa (se disponível) ou fornecedor
                if 'empresa' in resultado_comparacao['contas_nao_pagas'].columns:
                    grupo_col = 'empresa'
                    titulo_grupo = 'Empresa'
                elif 'fornecedor' in resultado_comparacao['contas_nao_pagas'].columns:
                    grupo_col = 'fornecedor'
                    titulo_grupo = 'Fornecedor'
                else:
                    grupo_col = 'categoria'
                    titulo_grupo = 'Categoria'
                
                if grupo_col in resultado_comparacao['contas_nao_pagas'].columns:
                    contas_nao_pagas_grupo = resultado_comparacao['contas_nao_pagas'].groupby(grupo_col).agg({
                        'valor': ['sum', 'count']
                    }).round(2)
                    contas_nao_pagas_grupo.columns = ['Valor Total', 'Quantidade']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.dataframe(contas_nao_pagas_grupo, use_container_width=True)
                    
                    with col2:
                        fig = px.bar(
                            x=contas_nao_pagas_grupo.index,
                            y=contas_nao_pagas_grupo['Valor Total'],
                            title=f"Contas Não Pagas por {titulo_grupo}"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(resultado_comparacao['contas_nao_pagas'], use_container_width=True)
            else:
                st.success("✅ Todas as contas foram pagas!")
        
        with tab6:
            # Pagamentos Sem Conta
            if not resultado_comparacao['pagamentos_sem_conta'].empty:
                st.warning(f"❓ {len(resultado_comparacao['pagamentos_sem_conta'])} pagamentos sem conta correspondente")
                st.dataframe(resultado_comparacao['pagamentos_sem_conta'], use_container_width=True)
        with tab6:
            # Pagamentos Sem Conta
            if not resultado_comparacao['pagamentos_sem_conta'].empty:
                st.warning(f"❓ {len(resultado_comparacao['pagamentos_sem_conta'])} pagamentos sem conta correspondente")
                st.dataframe(resultado_comparacao['pagamentos_sem_conta'], use_container_width=True)
            else:
                st.success("✅ Todos os pagamentos têm conta correspondente")


def mostrar_relatorios_diferencas(supabase_client):
    """
    Interface para relatórios de diferenças e inconsistências.
    """
    
    st.subheader("📊 Relatórios de Diferenças")
    
    # Buscar dados
    df_a_pagar = supabase_client.buscar_contas_a_pagar()
    df_pagas = supabase_client.buscar_contas_pagas()
    
    if df_a_pagar.empty or df_pagas.empty:
        st.info("ℹ️ Dados insuficientes para gerar relatórios. Carregue contas a pagar e contas pagas.")
        return
    
    # Executar análise completa
    comparador = ComparadorContasAPagarVsPagas()
    resultado = comparador.comparar_datasets(df_a_pagar, df_pagas)
    
    # Relatório de diferenças de valor
    st.subheader("💰 Diferenças de Valor")
    
    if not resultado['diferencas_valor'].empty:
        st.warning(f"⚠️ {len(resultado['diferencas_valor'])} diferenças de valor detectadas")
        
        # Estatísticas das diferenças
        dif_stats = resultado['diferencas_valor']['diferenca_valor'].describe()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Diferença Média", f"R$ {dif_stats['mean']:.2f}")
        with col2:
            st.metric("Maior Diferença", f"R$ {dif_stats['max']:.2f}")
        with col3:
            st.metric("Menor Diferença", f"R$ {dif_stats['min']:.2f}")
        
        st.dataframe(resultado['diferencas_valor'], use_container_width=True)
    else:
        st.success("✅ Nenhuma diferença significativa de valor encontrada")
    
    # Relatório de diferenças de prazo
    st.divider()
    st.subheader("⏰ Diferenças de Prazo")
    
    if not resultado['diferencas_prazo'].empty:
        st.info(f"📅 {len(resultado['diferencas_prazo'])} diferenças de prazo detectadas")
        
        # Análise de pagamentos antecipados vs atrasados
        prazo_stats = resultado['diferencas_prazo']['status_prazo'].value_counts()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("⏳ Pagamentos Atrasados", prazo_stats.get('Atrasado', 0))
        with col2:
            st.metric("⚡ Pagamentos Antecipados", prazo_stats.get('Antecipado', 0))
        
        # Gráfico de distribuição de prazos
        fig = px.histogram(
            resultado['diferencas_prazo'], 
            x='diferenca_dias',
            title="Distribuição das Diferenças de Prazo (dias)",
            nbins=20
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(resultado['diferencas_prazo'], use_container_width=True)
    else:
        st.success("✅ Nenhuma diferença significativa de prazo encontrada")
    
    # Botão para gerar relatório completo
    st.divider()
    if st.button("📄 Gerar Relatório Completo Excel", type="primary", use_container_width=True):
        with st.spinner("Gerando relatório..."):
            try:
                # Criar arquivo Excel com múltiplas abas
                excel_buffer = io.BytesIO()
                
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    # Aba resumo
                    resumo_df = pd.DataFrame([resultado['resumo']])
                    resumo_df.to_excel(writer, sheet_name='Resumo', index=False)
                    
                    # Correspondências exatas
                    if not resultado['correspondencias_exatas'].empty:
                        resultado['correspondencias_exatas'].to_excel(writer, sheet_name='Correspondencias_Exatas', index=False)
                    
                    # Correspondências aproximadas
                    if not resultado['correspondencias_aproximadas'].empty:
                        resultado['correspondencias_aproximadas'].to_excel(writer, sheet_name='Correspondencias_Aproximadas', index=False)
                    
                    # Contas não pagas
                    if not resultado['contas_nao_pagas'].empty:
                        resultado['contas_nao_pagas'].to_excel(writer, sheet_name='Contas_Nao_Pagas', index=False)
                    
                    # Pagamentos sem conta
                    if not resultado['pagamentos_sem_conta'].empty:
                        resultado['pagamentos_sem_conta'].to_excel(writer, sheet_name='Pagamentos_Sem_Conta', index=False)
                    
                    # Diferenças de valor
                    if not resultado['diferencas_valor'].empty:
                        resultado['diferencas_valor'].to_excel(writer, sheet_name='Diferencas_Valor', index=False)
                    
                    # Diferenças de prazo
                    if not resultado['diferencas_prazo'].empty:
                        resultado['diferencas_prazo'].to_excel(writer, sheet_name='Diferencas_Prazo', index=False)
                
                excel_buffer.seek(0)
                
                st.download_button(
                    label="📥 Download Relatório Completo",
                    data=excel_buffer.getvalue(),
                    file_name=f"relatorio_diferencas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                st.success("✅ Relatório gerado com sucesso!")
                
            except Exception as e:
                st.error(f"❌ Erro ao gerar relatório: {str(e)}")
