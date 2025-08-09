"""
Lógica do dashboard e resumos financeiros.

Contém funções para exibição de métricas, resumos e dados do banco de dados.
"""

import streamlit as st
import os
from src.database.supabase_client import SupabaseClient
from src.utils import formatar_moeda_brasileira, formatar_data_brasileira
from src.contas_pagas_interface import mostrar_interface_validacao_contas_pagas
from .calendar_logic import criar_calendario_financeiro

def mostrar_resumo_dashboard(supabase_client: SupabaseClient):
    """
    Mostra resumo financeiro do dashboard.
    
    Args:
        supabase_client: Cliente do Supabase para buscar dados
    """
    
    with st.spinner("Carregando resumo financeiro..."):
        resumo = supabase_client.get_resumo_financeiro()
        
        if resumo:
            # Métricas principais em colunas
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(
                    "💰 Total a Pagar",
                    formatar_moeda_brasileira(resumo.get('total_a_pagar', 0)),
                    f"{resumo.get('quantidade_a_pagar', 0)} contas"
                )
            
            with col2:
                st.metric(
                    "✅ Total Pago",
                    formatar_moeda_brasileira(resumo.get('total_pago', 0)),
                    f"{resumo.get('quantidade_pagas', 0)} contas"
                )
            
            with col3:
                total_a_pagar = resumo.get('total_a_pagar', 0)
                total_pago = resumo.get('total_pago', 0)
                saldo = total_a_pagar - total_pago
                
                # Lógica correta: saldo positivo = bom (sobrou dinheiro)
                if saldo > 0:
                    delta_texto = "✅ Economia (Bom)"
                elif saldo < 0:
                    delta_texto = "❌ Estouro (Ruim)"
                else:
                    delta_texto = "⚖️ Equilibrado"
                
                st.metric(
                    "📊 Saldo",
                    formatar_moeda_brasileira(saldo),
                    delta_texto
                )
            
            with col4:
                if total_a_pagar > 0:
                    percentual = (total_pago / total_a_pagar) * 100
                else:
                    percentual = 0
                st.metric(
                    "📈 % Pago",
                    f"{percentual:.1f}%"
                )
            
            with col5:
                st.metric(
                    "🏢 Empresas",
                    resumo.get('empresas_total', 0),
                    "Total"
                )

def mostrar_dados_banco(supabase_client: SupabaseClient, analyzer, report_gen):
    """
    Mostra dados carregados do banco de dados em diferentes abas.
    
    Args:
        supabase_client: Cliente do Supabase
        analyzer: Analisador de pagamentos
        report_gen: Gerador de relatórios
    """
    
    # Tabs para diferentes visões
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗓️ Calendário", 
        "📊 Dados Atuais", 
        "🏢 Por Empresa", 
        "📋 Exportar", 
        "🔍 Validação Contas Pagas"
    ])
    
    # Buscar dados uma vez para usar em todas as abas
    df_a_pagar = supabase_client.buscar_contas_a_pagar()
    df_pagas = supabase_client.buscar_contas_pagas()
    
    with tab1:
        criar_calendario_financeiro(df_a_pagar, df_pagas)
    
    with tab2:
        st.header("📊 Dados do Banco")
        
        col1, col2 = st.columns(2)
        
        with col1:            
            st.subheader("💰 Contas a Pagar")
            if not df_a_pagar.empty:
                # Mostrar resumo
                total_valor = df_a_pagar['valor'].sum()
                st.metric("Total", formatar_moeda_brasileira(total_valor), f"{len(df_a_pagar)} contas")
                
                # Mostrar dados (primeiros 10)
                df_display = df_a_pagar[['empresa', 'valor', 'data_vencimento', 'descricao']].head(10).copy()
                df_display['valor'] = df_display['valor'].apply(formatar_moeda_brasileira)
                df_display['data_vencimento'] = df_display['data_vencimento'].apply(formatar_data_brasileira)
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                
                if len(df_a_pagar) > 10:
                    st.caption(f"Mostrando 10 de {len(df_a_pagar)} registros")
            else:
                st.info("Nenhuma conta a pagar encontrada.")
        
        with col2:            
            st.subheader("✅ Contas Pagas")
            if not df_pagas.empty:
                # Mostrar resumo
                total_valor = df_pagas['valor'].sum()
                st.metric("Total", formatar_moeda_brasileira(total_valor), f"{len(df_pagas)} contas")
                
                # Mostrar dados (primeiros 10)
                df_display = df_pagas[['empresa', 'valor', 'data_pagamento', 'descricao']].head(10).copy()
                df_display['valor'] = df_display['valor'].apply(formatar_moeda_brasileira)
                df_display['data_pagamento'] = df_display['data_pagamento'].apply(formatar_data_brasileira)
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                
                if len(df_pagas) > 10:
                    st.caption(f"Mostrando 10 de {len(df_pagas)} registros")
            else:
                st.info("Nenhuma conta paga encontrada.")
    
    with tab3:
        st.header("🏢 Análise por Empresa")
        
        empresas = supabase_client.listar_empresas()
        
        if empresas:
            empresa_selecionada = st.selectbox("Selecione uma empresa:", ["Todas"] + empresas)
            
            if empresa_selecionada == "Todas":
                df_a_pagar = supabase_client.buscar_contas_a_pagar()
                df_pagas = supabase_client.buscar_contas_pagas()
            else:
                df_a_pagar = supabase_client.buscar_contas_a_pagar(empresa=empresa_selecionada)
                df_pagas = supabase_client.buscar_contas_pagas()
                # Filtrar pagas por conta_corrente se necessário (já que empresa não existe mais)
                if not df_pagas.empty and 'conta_corrente' in df_pagas.columns:
                    df_pagas = df_pagas[df_pagas['conta_corrente'].str.contains(empresa_selecionada, na=False, case=False)]
            
            if not df_a_pagar.empty or not df_pagas.empty:
                # Usar analyzer para gerar correspondências
                correspondencias = analyzer.encontrar_correspondencias(df_a_pagar, df_pagas)
                resumo_empresa = analyzer.gerar_relatorio_por_empresa(correspondencias)
                
                if not resumo_empresa.empty:
                    st.dataframe(resumo_empresa, use_container_width=True, hide_index=True)
                    
                    # Gráfico
                    fig = report_gen.criar_grafico_resumo_por_empresa(resumo_empresa)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Nenhum dado encontrado para análise.")
            else:
                st.info("Nenhum dado encontrado para a empresa selecionada.")
        else:
            st.info("Nenhuma empresa encontrada. Faça upload de arquivos primeiro.")
    
    with tab4:
        st.header("📋 Exportar Relatórios")
        
        if st.button("📄 Gerar Relatório Excel Completo", type="primary"):
            with st.spinner("Gerando relatório..."):
                try:                    
                    if not df_a_pagar.empty or not df_pagas.empty:
                        # Gerar análise
                        correspondencias = analyzer.encontrar_correspondencias(df_a_pagar, df_pagas)
                        resumo = analyzer.calcular_resumo_financeiro(correspondencias)
                        resumo_empresa = analyzer.gerar_relatorio_por_empresa(correspondencias)
                        
                        # Gerar Excel
                        arquivo_excel = report_gen.gerar_relatorio_excel(
                            correspondencias, resumo, resumo_empresa
                        )
                        
                        if arquivo_excel:
                            st.success(f"Relatório gerado: {arquivo_excel}")
                            
                            # Download
                            with open(arquivo_excel, "rb") as file:
                                st.download_button(
                                    label="⬇️ Download Relatório",
                                    data=file.read(),
                                    file_name=os.path.basename(arquivo_excel),
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                        else:
                            st.error("Erro ao gerar relatório Excel.")
                    else:
                        st.warning("Nenhum dado disponível para gerar relatório.")
                        
                except Exception as e:
                    st.error(f"Erro ao gerar relatório: {str(e)}")
    
    with tab5:
        # Interface de validação de contas pagas
        mostrar_interface_validacao_contas_pagas(supabase_client)
