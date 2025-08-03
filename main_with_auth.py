"""
Aplicação Principal do Calendário Financeiro com Autenticação.
"""

import streamlit as st
import sys
import os
import pandas as pd

# Configurar página DEVE ser a primeira coisa
st.set_page_config(
    page_title="Calendário Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Adicionar src ao path
sys.path.append('src')

from auth.auth_manager import AuthManager
from database.supabase_client import SupabaseClient

# Inicializar gerenciador de autenticação
@st.cache_resource
def init_auth_manager():
    return AuthManager()

auth_manager = init_auth_manager()

def main():
    """Função principal da aplicação."""
    
    # Título principal
    st.title("💰 Calendário Financeiro - Controle de Contas")
    
    # Verificar se é um redirect de confirmação de email
    query_params = st.query_params
    
    if "token" in query_params and "type" in query_params:
        if query_params["type"] == "signup":
            tratar_confirmacao_email(query_params)
            return
    
    # Verificar autenticação
    if not auth_manager.require_auth():
        # Mostrar informações sobre o sistema enquanto não está logado
        st.markdown("""
        ## 🚀 Sistema de Gestão Financeira
        
        ### ✨ Funcionalidades:
        - 📤 **Upload de Arquivos**: Excel/XLS com contas a pagar e pagas
        - 🤖 **Detecção Automática**: Identifica formato padrão ou ERP
        - 📊 **Dashboard Interativo**: Métricas e visualizações em tempo real
        - 🔍 **Análise de Correspondências**: Exatas e aproximadas
        - 📋 **Relatórios Excel**: Exportação completa dos dados
        - 🏢 **Multi-empresa**: Gestão separada por empresa
        - 💾 **Histórico**: Dados salvos na nuvem permanentemente
        
        ### 🔐 Faça login ou cadastre-se para começar!
        """)
        return
    
    # Usuário autenticado - carregar aplicação principal
    carregar_aplicacao_principal()

def tratar_confirmacao_email(query_params):
    """Trata a confirmação de email do Supabase."""
    
    st.header("📧 Confirmação de Email")
    
    try:
        # Tentar confirmar o email usando o token
        token = query_params["token"]
        
        # Usar o cliente Supabase para verificar o token
        supabase_client = auth_manager.get_supabase_client()
        
        # Tentar verificar o token
        result = supabase_client.supabase.auth.verify_otp({
            "token": token,
            "type": "signup"
        })
        
        if result.user:
            st.success("🎉 Email confirmado com sucesso!")
            st.info("✅ Sua conta está ativa. Você já pode fazer login.")
            
            # Limpar URL
            st.info("🔄 Redirecionando...")
            st.query_params.clear()
            st.rerun()
            
        else:
            st.error("❌ Erro ao confirmar email.")
            st.info("💡 O link pode ter expirado. Tente se cadastrar novamente.")
            
    except Exception as e:
        error_msg = str(e)
        
        if "expired" in error_msg.lower():
            st.error("⏰ Link expirado!")
            st.info("💡 Faça um novo cadastro ou solicite um novo link de confirmação.")
        elif "invalid" in error_msg.lower():
            st.error("❌ Link inválido!")
            st.info("💡 Verifique se você clicou no link correto do email.")
        else:
            st.error(f"❌ Erro: {error_msg}")
    
    # Botão para voltar ao login
    if st.button("🏠 Voltar ao Login", type="primary"):
        st.query_params.clear()
        st.rerun()

def carregar_aplicacao_principal():
    """Carrega a aplicação principal após autenticação."""
    
    # Importar módulos da aplicação
    from data_processor import ExcelProcessor
    from payment_analyzer import PaymentAnalyzer
    from report_generator import ReportGenerator
    from client_file_converter import ClientFileConverter
    
    # Obter cliente Supabase
    supabase_client = auth_manager.get_supabase_client()
    
    # Inicializar classes de processamento
    @st.cache_resource
    def init_processing_classes():
        processor = ExcelProcessor()
        analyzer = PaymentAnalyzer()
        report_gen = ReportGenerator()
        converter = ClientFileConverter()
        return processor, analyzer, report_gen, converter
    
    processor, analyzer, report_gen, converter = init_processing_classes()
    
    # Mostrar resumo financeiro
    mostrar_resumo_dashboard(supabase_client)
    
    # Sidebar para upload
    st.sidebar.header("📁 Upload de Arquivos")
    
    # Upload de arquivos de contas a pagar
    st.sidebar.subheader("Contas a Pagar")
    uploaded_a_pagar = st.sidebar.file_uploader(
        "Selecione arquivos de contas a pagar",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        key="a_pagar",
        help="O sistema detectará automaticamente o formato dos arquivos"
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
    processar = st.sidebar.button("🔄 Processar e Salvar no Banco", type="primary")
    
    # Processamento dos arquivos
    if processar and (uploaded_a_pagar or uploaded_pagas):
        processar_arquivos(
            uploaded_a_pagar, uploaded_pagas, 
            supabase_client, converter, processor
        )
    
    # Mostrar dados do banco
    mostrar_dados_banco(supabase_client, analyzer, report_gen)

def mostrar_resumo_dashboard(supabase_client: SupabaseClient):
    """Mostra resumo financeiro do dashboard."""
    
    with st.spinner("Carregando resumo financeiro..."):
        resumo = supabase_client.get_resumo_financeiro()
        
        if resumo:
            # Métricas principais em colunas
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(
                    "💰 Total a Pagar",
                    f"R$ {resumo.get('total_a_pagar', 0):,.2f}",
                    f"{resumo.get('quantidade_a_pagar', 0)} contas"
                )
            
            with col2:
                st.metric(
                    "✅ Total Pago",
                    f"R$ {resumo.get('total_pago', 0):,.2f}",
                    f"{resumo.get('quantidade_pagas', 0)} contas"
                )
            
            with col3:
                total_a_pagar = resumo.get('total_a_pagar', 0)
                total_pago = resumo.get('total_pago', 0)
                saldo = total_a_pagar - total_pago
                st.metric(
                    "📊 Saldo",
                    f"R$ {saldo:,.2f}",
                    "Diferença"
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

def processar_arquivos(uploaded_a_pagar, uploaded_pagas, supabase_client, converter, processor):
    """Processa arquivos e salva no banco."""
    
    with st.spinner("Processando arquivos e salvando no banco..."):
        try:
            processamento_id = supabase_client.registrar_processamento(
                tipo="upload_completo",
                status="em_andamento",
                detalhes={"inicio": str(st.session_state.get('user_data', {}).get('nome', 'Usuário'))},
                arquivos=[]
            )
            
            total_registros = 0
            arquivos_processados = []
            
            # Processar arquivos de contas a pagar
            if uploaded_a_pagar:
                st.info(f"📁 Processando {len(uploaded_a_pagar)} arquivo(s) de contas a pagar...")
                
                for uploaded_file in uploaded_a_pagar:
                    try:
                        # Detectar formato e processar
                        df_processado = detectar_e_processar_arquivo(uploaded_file, converter, processor)
                        
                        if not df_processado.empty:
                            # Salvar no banco
                            resultado = supabase_client.inserir_contas_a_pagar(
                                df_processado, 
                                arquivo_origem=uploaded_file.name,
                                processamento_id=processamento_id
                            )
                            
                            if resultado["success"]:
                                total_registros += resultado["registros_inseridos"]
                                arquivos_processados.append(uploaded_file.name)
                                st.success(f"✅ {uploaded_file.name}: {resultado['registros_inseridos']} registros salvos")
                            else:
                                st.error(f"❌ Erro ao salvar {uploaded_file.name}: {resultado['message']}")
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao processar {uploaded_file.name}: {str(e)}")
            
            # Processar arquivos de contas pagas
            if uploaded_pagas:
                st.info(f"📁 Processando {len(uploaded_pagas)} arquivo(s) de contas pagas...")
                
                for uploaded_file in uploaded_pagas:
                    try:
                        # Processar arquivo padrão
                        df_processado = processar_arquivo_padrao(uploaded_file, processor)
                        
                        if not df_processado.empty:
                            # Salvar no banco
                            resultado = supabase_client.inserir_contas_pagas(
                                df_processado,
                                arquivo_origem=uploaded_file.name,
                                processamento_id=processamento_id
                            )
                            
                            if resultado["success"]:
                                total_registros += resultado["registros_inseridos"]
                                arquivos_processados.append(uploaded_file.name)
                                st.success(f"✅ {uploaded_file.name}: {resultado['registros_inseridos']} registros salvos")
                            else:
                                st.error(f"❌ Erro ao salvar {uploaded_file.name}: {resultado['message']}")
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao processar {uploaded_file.name}: {str(e)}")
            
            # Finalizar processamento
            supabase_client.registrar_processamento(
                tipo="upload_completo",
                status="concluido",
                detalhes={
                    "total_registros": total_registros,
                    "arquivos_processados": len(arquivos_processados)
                },
                arquivos=arquivos_processados
            )
            
            if total_registros > 0:
                st.success(f"🎉 Processamento concluído! {total_registros} registros salvos no banco de dados.")
                st.balloons()
                # Forçar atualização dos dados
                st.rerun()
            else:
                st.warning("⚠️ Nenhum registro foi processado.")
                
        except Exception as e:
            st.error(f"❌ Erro geral no processamento: {str(e)}")

def detectar_e_processar_arquivo(uploaded_file, converter, processor):
    """Detecta formato do arquivo e processa adequadamente."""
    
    # Reset do buffer
    uploaded_file.seek(0)
    
    # Salvar arquivo temporário
    temp_path = f"temp_{uploaded_file.name}"
    
    try:
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        uploaded_file.seek(0)
        
        # Detectar se é formato do cliente
        if converter.detectar_formato_cliente(temp_path):
            st.info(f"🔄 {uploaded_file.name} - Formato ERP detectado, convertendo...")
            resultado = converter.processar_arquivo_completo(temp_path, salvar_convertido=False)
            
            if resultado['sucesso']:
                return resultado['dados_convertidos']
            else:
                st.error(f"Erro na conversão: {resultado['erro']}")
                return pd.DataFrame()
        else:
            st.info(f"📋 {uploaded_file.name} - Formato padrão detectado")
            return processar_arquivo_padrao(uploaded_file, processor)
    
    finally:
        # Limpar arquivo temporário
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

def processar_arquivo_padrao(uploaded_file, processor):
    """Processa arquivo no formato padrão."""
    
    # Salvar temporariamente
    temp_path = f"temp_padrao_{uploaded_file.name}"
    
    try:
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Carregar com o processor
        df = processor.carregar_arquivo_excel(temp_path)
        return df
    
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

def mostrar_dados_banco(supabase_client: SupabaseClient, analyzer, report_gen):
    """Mostra dados carregados do banco."""
    
    # Tabs para diferentes visões
    tab1, tab2, tab3 = st.tabs(["📊 Dados Atuais", "🏢 Por Empresa", "📋 Exportar"])
    
    with tab1:
        st.header("📊 Dados do Banco")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Buscar contas a pagar
            df_a_pagar = supabase_client.buscar_contas_a_pagar()
            
            st.subheader("💰 Contas a Pagar")
            if not df_a_pagar.empty:
                # Mostrar resumo
                total_valor = df_a_pagar['valor'].sum()
                st.metric("Total", f"R$ {total_valor:,.2f}", f"{len(df_a_pagar)} contas")
                
                # Mostrar dados (primeiros 10)
                df_display = df_a_pagar[['empresa', 'valor', 'data_vencimento', 'descricao']].head(10).copy()
                df_display['valor'] = df_display['valor'].apply(lambda x: f"R$ {x:,.2f}")
                st.dataframe(df_display, use_container_width=True)
                
                if len(df_a_pagar) > 10:
                    st.caption(f"Mostrando 10 de {len(df_a_pagar)} registros")
            else:
                st.info("Nenhuma conta a pagar encontrada.")
        
        with col2:
            # Buscar contas pagas
            df_pagas = supabase_client.buscar_contas_pagas()
            
            st.subheader("✅ Contas Pagas")
            if not df_pagas.empty:
                # Mostrar resumo
                total_valor = df_pagas['valor'].sum()
                st.metric("Total", f"R$ {total_valor:,.2f}", f"{len(df_pagas)} contas")
                
                # Mostrar dados (primeiros 10)
                df_display = df_pagas[['empresa', 'valor', 'data_pagamento', 'descricao']].head(10).copy()
                df_display['valor'] = df_display['valor'].apply(lambda x: f"R$ {x:,.2f}")
                st.dataframe(df_display, use_container_width=True)
                
                if len(df_pagas) > 10:
                    st.caption(f"Mostrando 10 de {len(df_pagas)} registros")
            else:
                st.info("Nenhuma conta paga encontrada.")
    
    with tab2:
        st.header("🏢 Análise por Empresa")
        
        empresas = supabase_client.listar_empresas()
        
        if empresas:
            empresa_selecionada = st.selectbox("Selecione uma empresa:", ["Todas"] + empresas)
            
            if empresa_selecionada == "Todas":
                df_a_pagar = supabase_client.buscar_contas_a_pagar()
                df_pagas = supabase_client.buscar_contas_pagas()
            else:
                df_a_pagar = supabase_client.buscar_contas_a_pagar(empresa=empresa_selecionada)
                df_pagas = supabase_client.buscar_contas_pagas(empresa=empresa_selecionada)
            
            if not df_a_pagar.empty or not df_pagas.empty:
                # Usar analyzer para gerar correspondências
                correspondencias = analyzer.encontrar_correspondencias(df_a_pagar, df_pagas)
                resumo_empresa = analyzer.gerar_relatorio_por_empresa(correspondencias)
                
                if not resumo_empresa.empty:
                    st.dataframe(resumo_empresa, use_container_width=True)
                    
                    # Gráfico
                    fig = report_gen.criar_grafico_resumo_por_empresa(resumo_empresa)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Nenhum dado encontrado para análise.")
            else:
                st.info("Nenhum dado encontrado para a empresa selecionada.")
        else:
            st.info("Nenhuma empresa encontrada. Faça upload de arquivos primeiro.")
    
    with tab3:
        st.header("📋 Exportar Relatórios")
        
        if st.button("📄 Gerar Relatório Excel Completo", type="primary"):
            with st.spinner("Gerando relatório..."):
                try:
                    # Buscar todos os dados
                    df_a_pagar = supabase_client.buscar_contas_a_pagar()
                    df_pagas = supabase_client.buscar_contas_pagas()
                    
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

if __name__ == "__main__":
    main()
