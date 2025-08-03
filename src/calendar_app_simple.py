"""
Aplicação Streamlit para o Calendário Financeiro - Versão Simplificada.
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import sys

# Adicionar src ao path
sys.path.append('src')

from data_processor import ExcelProcessor
from payment_analyzer import PaymentAnalyzer
from report_generator import ReportGenerator
from client_file_converter import ClientFileConverter

# Inicializar classes
@st.cache_resource
def init_classes():
    processor = ExcelProcessor()
    analyzer = PaymentAnalyzer()
    report_gen = ReportGenerator()
    converter = ClientFileConverter()
    return processor, analyzer, report_gen, converter

processor, analyzer, report_gen, converter = init_classes()

# Título principal
st.title("💰 Calendário Financeiro - Controle de Contas a Pagar")

# Sidebar
st.sidebar.header("📁 Upload de Arquivos")

# Upload de arquivos de contas a pagar
st.sidebar.subheader("Contas a Pagar")

formato_arquivo = st.sidebar.radio(
    "Formato do arquivo:",
    ["Formato Padrão", "Formato do Cliente (Sistema ERP)"]
)

uploaded_a_pagar = st.sidebar.file_uploader(
    "Selecione arquivos de contas a pagar",
    type=['xlsx', 'xls'],
    accept_multiple_files=True,
    key="a_pagar"
)

# Upload de arquivos de contas pagas
st.sidebar.subheader("Contas Pagas")
uploaded_pagas = st.sidebar.file_uploader(
    "Selecione arquivos de contas pagas",
    type=['xlsx', 'xls'],
    accept_multiple_files=True,
    key="pagas"
)

# Botão para processar
processar = st.sidebar.button("🔄 Processar Dados", type="primary")

# Função para salvar arquivos uploadados
def salvar_arquivos_upload(uploaded_files, diretorio):
    """Salva arquivos uploadados no diretório especificado."""
    os.makedirs(diretorio, exist_ok=True)
    arquivos_salvos = []
    
    for uploaded_file in uploaded_files:
        arquivo_path = os.path.join(diretorio, uploaded_file.name)
        with open(arquivo_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        arquivos_salvos.append(arquivo_path)
    
    return arquivos_salvos

# Função para processar arquivos do cliente
def processar_arquivos_cliente(uploaded_files):
    """Processa arquivos no formato do cliente e os converte."""
    arquivos_convertidos = []
    
    for uploaded_file in uploaded_files:
        # Salvar arquivo temporário
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        try:
            # Processar com o conversor
            resultado = converter.processar_arquivo_completo(temp_path, salvar_convertido=True)
            
            if resultado['sucesso']:
                st.success(f"✅ {uploaded_file.name} convertido com sucesso!")
                
                # Mostrar relatório da conversão
                relatorio = resultado['relatorio']
                st.info(f"""
                📊 **Relatório de Conversão:**
                - **Registros:** {relatorio['registros_convertidos']} convertidos
                - **Valor Total:** R$ {relatorio['valor_total']:,.2f}
                - **Empresas:** {relatorio['empresas_unicas']} únicas
                """)
                
                arquivos_convertidos.append(resultado['arquivo_convertido'])
            else:
                st.error(f"❌ Erro ao converter {uploaded_file.name}: {resultado['erro']}")
        
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")
        finally:
            # Remover arquivo temporário
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    return arquivos_convertidos

# Processamento dos dados
if processar and (uploaded_a_pagar or uploaded_pagas):
    with st.spinner("Processando arquivos..."):
        try:
            # Processar arquivos de contas a pagar
            if uploaded_a_pagar:
                if formato_arquivo == "Formato do Cliente (Sistema ERP)":
                    # Usar conversor para arquivos do cliente
                    st.info("🔄 Convertendo arquivos do formato do cliente...")
                    processar_arquivos_cliente(uploaded_a_pagar)
                else:
                    # Salvar arquivos no formato padrão
                    salvar_arquivos_upload(uploaded_a_pagar, "data/contas_a_pagar")
                    st.success("✅ Arquivos de contas a pagar salvos!")
            
            # Salvar arquivos de contas pagas (sempre formato padrão)
            if uploaded_pagas:
                salvar_arquivos_upload(uploaded_pagas, "data/contas_pagas")
                st.success("✅ Arquivos de contas pagas salvos!")
            
            # Carregar e processar dados
            df_a_pagar = processor.carregar_todos_arquivos_a_pagar()
            df_pagas = processor.carregar_todos_arquivos_pagos()
            
            if df_a_pagar.empty and df_pagas.empty:
                st.error("Nenhum dado foi encontrado nos arquivos processados.")
            else:
                # Encontrar correspondências
                correspondencias = analyzer.encontrar_correspondencias(df_a_pagar, df_pagas)
                
                # Calcular resumo
                resumo = analyzer.calcular_resumo_financeiro(correspondencias)
                
                # Gerar resumo por empresa
                resumo_empresa = analyzer.gerar_relatorio_por_empresa(correspondencias)
                
                # Salvar dados processados na sessão
                st.session_state['df_a_pagar'] = df_a_pagar
                st.session_state['df_pagas'] = df_pagas
                st.session_state['correspondencias'] = correspondencias
                st.session_state['resumo'] = resumo
                st.session_state['resumo_empresa'] = resumo_empresa
                st.session_state['data_processamento'] = datetime.now()
                
                st.success("Dados processados com sucesso!")
        
        except Exception as e:
            st.error(f"Erro ao processar dados: {str(e)}")

# Exibir resultados se existirem dados processados
if 'resumo' in st.session_state:
    resumo = st.session_state['resumo']
    correspondencias = st.session_state['correspondencias']
    resumo_empresa = st.session_state['resumo_empresa']
    df_a_pagar = st.session_state['df_a_pagar']
    df_pagas = st.session_state['df_pagas']
    
    st.success(f"Dados processados em: {st.session_state['data_processamento'].strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total a Pagar",
            f"R$ {resumo['total_a_pagar'] + resumo['total_pendente']:,.2f}",
            f"{resumo['quantidade_exatas'] + resumo['quantidade_aproximadas'] + resumo['quantidade_pendentes']} contas"
        )
    
    with col2:
        st.metric(
            "Total Pago",
            f"R$ {resumo['total_pago']:,.2f}",
            f"{resumo['quantidade_exatas'] + resumo['quantidade_aproximadas']} contas"
        )
    
    with col3:
        st.metric(
            "Pendente",
            f"R$ {resumo['total_pendente']:,.2f}",
            f"{resumo['quantidade_pendentes']} contas"
        )
    
    with col4:
        st.metric(
            "% Pago",
            f"{resumo['percentual_pago']:.1f}%"
        )
    
    # Tabs para diferentes visões
    tab1, tab2, tab3 = st.tabs(["📊 Resumo por Empresa", "✅ Correspondências", "⏰ Pendências"])
    
    with tab1:
        st.header("Resumo por Empresa")
        
        if not resumo_empresa.empty:
            # Formatar valores para exibição
            resumo_display = resumo_empresa.copy()
            colunas_valor = ['valor_a_pagar', 'valor_pago', 'valor_pendente', 'diferenca_valor']
            for col in colunas_valor:
                if col in resumo_display.columns:
                    resumo_display[col] = resumo_display[col].apply(lambda x: f"R$ {x:,.2f}")
            
            st.dataframe(resumo_display, use_container_width=True)
            
            # Gráfico de resumo por empresa
            fig_empresa = report_gen.criar_grafico_resumo_por_empresa(resumo_empresa)
            st.plotly_chart(fig_empresa, use_container_width=True)
        else:
            st.info("Nenhum dado de empresa encontrado.")
    
    with tab2:
        st.header("Correspondências Encontradas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✅ Correspondências Exatas")
            if correspondencias['exatas']:
                df_exatas = pd.DataFrame([
                    {
                        'Empresa': c['conta_a_pagar']['empresa'],
                        'Valor A Pagar': f"R$ {c['conta_a_pagar']['valor']:,.2f}",
                        'Valor Pago': f"R$ {c['conta_paga']['valor']:,.2f}",
                        'Diferença': f"R$ {c['diferenca_valor']:,.2f}"
                    }
                    for c in correspondencias['exatas'][:10]  # Mostrar apenas os primeiros 10
                ])
                st.dataframe(df_exatas, use_container_width=True)
                if len(correspondencias['exatas']) > 10:
                    st.info(f"Mostrando 10 de {len(correspondencias['exatas'])} correspondências exatas.")
            else:
                st.info("Nenhuma correspondência exata encontrada.")
        
        with col2:
            st.subheader("🔍 Correspondências Aproximadas")
            if correspondencias['aproximadas']:
                df_aproximadas = pd.DataFrame([
                    {
                        'Empresa': c['conta_a_pagar']['empresa'],
                        'Valor A Pagar': f"R$ {c['conta_a_pagar']['valor']:,.2f}",
                        'Valor Pago': f"R$ {c['conta_paga']['valor']:,.2f}",
                        'Diferença': f"R$ {c['diferenca_valor']:,.2f}"
                    }
                    for c in correspondencias['aproximadas'][:10]  # Mostrar apenas os primeiros 10
                ])
                st.dataframe(df_aproximadas, use_container_width=True)
                if len(correspondencias['aproximadas']) > 10:
                    st.info(f"Mostrando 10 de {len(correspondencias['aproximadas'])} correspondências aproximadas.")
            else:
                st.info("Nenhuma correspondência aproximada encontrada.")
    
    with tab3:
        st.header("Contas Pendentes")
        
        if correspondencias['nao_encontradas']:
            df_pendentes = pd.DataFrame(correspondencias['nao_encontradas'])
            if not df_pendentes.empty:
                df_pendentes_display = df_pendentes[[
                    'empresa', 'descricao', 'valor', 'data_vencimento'
                ]].copy()
                df_pendentes_display['valor'] = df_pendentes_display['valor'].apply(lambda x: f"R$ {x:,.2f}")
                df_pendentes_display['data_vencimento'] = pd.to_datetime(df_pendentes_display['data_vencimento']).dt.strftime('%d/%m/%Y')
                st.dataframe(df_pendentes_display.head(20), use_container_width=True)
                if len(df_pendentes_display) > 20:
                    st.info(f"Mostrando 20 de {len(df_pendentes_display)} contas pendentes.")
        else:
            st.success("✅ Todas as contas foram pagas!")
    
    # Botão para gerar relatório Excel
    st.header("📋 Exportar Relatório")
    
    if st.button("📄 Gerar Relatório Excel", type="primary"):
        with st.spinner("Gerando relatório..."):
            try:
                arquivo_excel = report_gen.gerar_relatorio_excel(
                    correspondencias, resumo, resumo_empresa
                )
                
                if arquivo_excel:
                    st.success(f"Relatório gerado: {arquivo_excel}")
                    
                    # Oferecer download
                    with open(arquivo_excel, "rb") as file:
                        st.download_button(
                            label="⬇️ Download Relatório",
                            data=file.read(),
                            file_name=os.path.basename(arquivo_excel),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.error("Erro ao gerar relatório Excel.")
            except Exception as e:
                st.error(f"Erro ao gerar relatório: {str(e)}")

else:
    # Instruções iniciais
    st.info("""
    ### 📋 Como usar o sistema:
    
    1. **Upload de Arquivos**: Use a barra lateral:
       - **Formato Padrão**: empresa, valor, data_vencimento, descricao, categoria
       - **Formato do Cliente**: Arquivo exportado diretamente do sistema ERP
    
    2. **Processamento**: Clique em "Processar Dados"
    
    3. **Análise**: Visualize resumos, correspondências e pendências
    
    4. **Relatório**: Exporte um relatório completo em Excel
    """)
    
    # Botão para testar com arquivo modelo
    if st.button("🧪 Testar com Arquivo Modelo", type="secondary"):
        with st.spinner("Processando arquivo modelo..."):
            try:
                # Processar arquivo modelo
                arquivo_modelo = "ArquivosModeloCliente/Mov_Financeiro_Data_Vencimento_02082025.xls"
                resultado = converter.processar_arquivo_completo(arquivo_modelo, salvar_convertido=True)
                
                if resultado['sucesso']:
                    # Salvar na sessão para exibir
                    st.session_state['df_a_pagar'] = resultado['dados_convertidos']
                    st.session_state['df_pagas'] = pd.DataFrame()  # Vazio para teste
                    
                    # Processar análise
                    correspondencias = analyzer.encontrar_correspondencias(
                        resultado['dados_convertidos'], 
                        pd.DataFrame()
                    )
                    resumo = analyzer.calcular_resumo_financeiro(correspondencias)
                    resumo_empresa = analyzer.gerar_relatorio_por_empresa(correspondencias)
                    
                    st.session_state['correspondencias'] = correspondencias
                    st.session_state['resumo'] = resumo
                    st.session_state['resumo_empresa'] = resumo_empresa
                    st.session_state['data_processamento'] = datetime.now()
                    
                    st.success("✅ Arquivo modelo processado com sucesso!")
                    st.rerun()
                else:
                    st.error(f"❌ Erro ao processar arquivo modelo: {resultado['erro']}")
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
    
    # Mostrar exemplo
    st.subheader("📁 Exemplo de Formato Padrão")
    exemplo_a_pagar = pd.DataFrame({
        'empresa': ['Fornecedor A', 'Fornecedor B'],
        'valor': [1500.00, 2800.50],
        'data_vencimento': ['2025-08-15', '2025-08-20'],
        'descricao': ['Material Escritório', 'Serviços TI'],
        'categoria': ['Material', 'Serviços']
    })
    st.dataframe(exemplo_a_pagar, use_container_width=True)
