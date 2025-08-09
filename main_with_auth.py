"""
Aplicação Principal do Calendário Financeiro com Autenticação.
"""

import streamlit as st
import sys
import os
import pandas as pd
import uuid
import calendar
import time
from datetime import datetime, timedelta

# Adicionar src ao path ANTES das importações locais
sys.path.append('src')

# Configurar página DEVE ser a primeira coisa
st.set_page_config(
    page_title="Calendário Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS global para reduzir tamanho de todas as métricas
st.markdown("""
<style>
/* CSS super agressivo para forçar tamanhos menores */
div[data-testid="metric-container"], 
.stMetric, 
[data-testid="metric-container"] {
    background-color: transparent !important;
    border: none !important;
    padding: 1px 0 !important;
    margin: 1px 0 !important;
    height: auto !important;
    min-height: unset !important;
}

/* Labels das métricas */
div[data-testid="metric-container"] > div:first-child,
div[data-testid="metric-container"] > div[data-testid="metric-label"],
.stMetric > div:first-child {
    font-size: 0.5rem !important;
    font-weight: normal !important;
    color: #6b7280 !important;
    line-height: 1.1 !important;
    height: auto !important;
    white-space: nowrap !important;
}

/* Valores das métricas */
div[data-testid="metric-container"] > div:nth-child(2),
div[data-testid="metric-container"] > div[data-testid="metric-value"],
.stMetric > div:nth-child(2) {
    font-size: 0.65rem !important;
    font-weight: bold !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.0 !important;
    height: auto !important;
    white-space: nowrap !important;
}

/* Delta das métricas */
div[data-testid="metric-container"] > div:last-child,
div[data-testid="metric-container"] > div[data-testid="metric-delta"],
.stMetric > div:last-child {
    font-size: 0.45rem !important;
    color: #9ca3af !important;
    line-height: 1.0 !important;
    height: auto !important;
    white-space: nowrap !important;
}

/* Forçar em todos os spans e textos dentro das métricas */
div[data-testid="metric-container"] span,
div[data-testid="metric-container"] p,
div[data-testid="metric-container"] div,
.stMetric span,
.stMetric p,
.stMetric div {
    font-size: 0.65rem !important;
    line-height: 1.0 !important;
    white-space: nowrap !important;
}

/* Especificamente para valores monetários */
div[data-testid="metric-container"] div[data-testid="metric-value"] span,
div[data-testid="metric-container"] div[data-testid="metric-value"] {
    font-size: 0.65rem !important;
    font-weight: bold !important;
    line-height: 1.0 !important;
}

/* Forçar altura mínima pequena */
div[data-testid="metric-container"],
.stMetric {
    max-height: 60px !important;
    height: auto !important;
}
</style>
""", unsafe_allow_html=True)

from src.auth.auth_manager import AuthManager
from src.database.supabase_client import SupabaseClient

# Importar utilitários de formatação
from src.utils import formatar_moeda_brasileira, formatar_data_brasileira, obter_mes_nome_brasileiro

# Importar módulos de processamento
from src.data_processor import ExcelProcessor
from src.payment_analyzer import PaymentAnalyzer
from src.report_generator import ReportGenerator
from src.client_file_converter import ClientFileConverter

# Importar interface de compartilhamento
from src.compartilhamento_ui import mostrar_compartilhamento_compacto, mostrar_interface_compartilhamento

# Importar interface de validação de contas pagas
from src.contas_pagas_interface import mostrar_interface_validacao_contas_pagas

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
    
    # Seção de Limpeza de Dados
    st.sidebar.divider()
    st.sidebar.header("🗑️ Limpeza de Dados")
    
    st.sidebar.warning("⚠️ **Atenção:** As operações de limpeza são irreversíveis!")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("🗑️ Limpar\nContas a Pagar", help="Remove todas as contas a pagar do banco", use_container_width=True):
            resultado = supabase_client.limpar_contas_a_pagar()
            if resultado["success"]:
                st.sidebar.success(resultado["message"])
                st.rerun()
            else:
                st.sidebar.error(resultado["message"])
    
    with col2:
        if st.button("🗑️ Limpar\nContas Pagas", help="Remove todas as contas pagas do banco", use_container_width=True):
            resultado = supabase_client.limpar_contas_pagas()
            if resultado["success"]:
                st.sidebar.success(resultado["message"])
                st.rerun()
            else:
                st.sidebar.error(resultado["message"])
    
    if st.sidebar.button("🗑️ Limpar Todos os Dados", help="Remove TODOS os dados do usuário", type="secondary", use_container_width=True):
        resultado = supabase_client.limpar_dados_usuario()
        if resultado["success"]:
            st.sidebar.success(resultado["message"])
            st.rerun()
        else:
            st.sidebar.error(resultado["message"])
    
    # Checkbox para verificar duplicatas
    st.sidebar.divider()
    st.sidebar.subheader("⚙️ Configurações")
    verificar_duplicatas = st.sidebar.checkbox(
        "✅ Verificar duplicatas ao importar", 
        value=True, 
        help="Quando ativado, ignora registros duplicados durante a importação"
    )
    
    # Armazenar configuração no session state
    st.session_state['verificar_duplicatas'] = verificar_duplicatas
    
    # Adicionar compartilhamento compacto na sidebar
    mostrar_compartilhamento_compacto(supabase_client)
    
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

def processar_arquivos(uploaded_a_pagar, uploaded_pagas, supabase_client, converter, processor):
    """Processa arquivos e salva no banco."""
    
    # Obter configuração de duplicatas
    verificar_duplicatas = st.session_state.get('verificar_duplicatas', True)
    
    with st.spinner("Processando arquivos e salvando no banco..."):
        try:
            processamento_id = supabase_client.registrar_processamento(
                tipo="upload_completo",
                status="em_andamento",
                detalhes={"inicio": str(st.session_state.get('user_data', {}).get('nome', 'Usuário'))},
                arquivos=[]
            )
            
            total_registros = 0
            total_duplicatas = 0
            arquivos_processados = []
            
            # Processar arquivos de contas a pagar
            if uploaded_a_pagar:
                st.info(f"📁 Processando {len(uploaded_a_pagar)} arquivo(s) de contas a pagar...")
                
                for uploaded_file in uploaded_a_pagar:
                    try:
                        # Detectar formato e processar
                        df_processado = detectar_e_processar_arquivo(uploaded_file, converter, processor)
                        
                        if not df_processado.empty:
                            # Salvar no banco com verificação de duplicatas
                            resultado = supabase_client.inserir_contas_a_pagar(
                                df_processado, 
                                arquivo_origem=uploaded_file.name,
                                processamento_id=processamento_id,
                                verificar_duplicatas=verificar_duplicatas
                            )
                            
                            if resultado["success"]:
                                total_registros += resultado["registros_inseridos"]
                                total_duplicatas += resultado.get("duplicatas_ignoradas", 0)
                                arquivos_processados.append(uploaded_file.name)
                                st.success(f"✅ {uploaded_file.name}: {resultado['registros_inseridos']} registros salvos")
                                if resultado.get("duplicatas_ignoradas", 0) > 0:
                                    st.info(f"ℹ️ {uploaded_file.name}: {resultado['duplicatas_ignoradas']} duplicatas ignoradas")
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
                            # Salvar no banco com verificação de duplicatas
                            resultado = supabase_client.inserir_contas_pagas(
                                df_processado,
                                arquivo_origem=uploaded_file.name,
                                processamento_id=processamento_id,
                                verificar_duplicatas=verificar_duplicatas
                            )
                            
                            if resultado["success"]:
                                total_registros += resultado["registros_inseridos"]
                                total_duplicatas += resultado.get("duplicatas_ignoradas", 0)
                                arquivos_processados.append(uploaded_file.name)
                                st.success(f"✅ {uploaded_file.name}: {resultado['registros_inseridos']} registros salvos")
                                if resultado.get("duplicatas_ignoradas", 0) > 0:
                                    st.info(f"ℹ️ {uploaded_file.name}: {resultado['duplicatas_ignoradas']} duplicatas ignoradas")
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
                    "total_duplicatas": total_duplicatas,
                    "arquivos_processados": len(arquivos_processados),
                    "verificar_duplicatas": verificar_duplicatas
                },
                arquivos=arquivos_processados
            )
            
            if total_registros > 0:
                mensagem = f"🎉 Processamento concluído! {total_registros} registros salvos no banco de dados."
                if total_duplicatas > 0:
                    mensagem += f" {total_duplicatas} duplicatas foram ignoradas."
                st.success(mensagem)
                st.balloons()
                # Forçar atualização dos dados
                st.rerun()
            else:
                if total_duplicatas > 0:
                    st.info(f"ℹ️ Processamento concluído! Nenhum registro novo encontrado. {total_duplicatas} duplicatas foram ignoradas.")
                else:
                    st.warning("⚠️ Nenhum registro foi processado.")
                
        except Exception as e:
            st.error(f"❌ Erro geral no processamento: {str(e)}")

def detectar_e_processar_arquivo(uploaded_file, converter, processor):
    """Detecta formato do arquivo e processa adequadamente."""
    
    # Reset do buffer
    uploaded_file.seek(0)
    
    # Salvar arquivo temporário com nome único
    temp_path = f"temp_{uuid.uuid4().hex[:8]}_{uploaded_file.name}"
    
    try:
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        uploaded_file.seek(0)
        
        # Detectar formato Modelo_Contas_Pagar primeiro (mais específico)
        if converter.detectar_formato_modelo_contas_pagar(temp_path):
            st.info(f"📊 {uploaded_file.name} - Formato Modelo_Contas_Pagar detectado, convertendo...")
            df_convertido = converter.converter_modelo_contas_pagar(temp_path)
            
            if df_convertido is not None and not df_convertido.empty:
                st.success(f"✅ {uploaded_file.name} - {len(df_convertido)} registros convertidos do formato Modelo_Contas_Pagar")
                return df_convertido
            else:
                st.error(f"❌ Erro na conversão do formato Modelo_Contas_Pagar: {uploaded_file.name}")
                return pd.DataFrame()
        
        # Detectar se é formato ERP do cliente
        elif converter.detectar_formato_cliente(temp_path):
            st.info(f"🔄 {uploaded_file.name} - Formato ERP detectado, convertendo...")
            resultado = converter.processar_arquivo_completo(temp_path, salvar_convertido=False)
            
            if resultado['sucesso']:
                return resultado['dados_convertidos']
            else:
                st.error(f"❌ Erro na conversão ERP: {resultado['erro']}")
                return pd.DataFrame()
        
        # Formato padrão
        else:
            st.info(f"📋 {uploaded_file.name} - Formato padrão detectado")
            return processar_arquivo_padrao(uploaded_file, processor)
    
    finally:
        # Limpar arquivo temporário
        remover_arquivo_temporario(temp_path)

def processar_arquivo_padrao(uploaded_file, processor):
    """Processa arquivo no formato padrão."""
    
    # Salvar temporariamente com nome único
    temp_path = f"temp_padrao_{uuid.uuid4().hex[:8]}_{uploaded_file.name}"
    
    try:
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Carregar com o processor
        df = processor.carregar_arquivo_excel(temp_path)
        return df
    
    finally:
        remover_arquivo_temporario(temp_path)

def criar_calendario_financeiro(df_a_pagar: pd.DataFrame, df_pagas: pd.DataFrame, mes: int = None, ano: int = None):
    """
    Cria um calendário visual com informações financeiras com opção de visualização mensal ou semanal.
    
    Args:
        df_a_pagar: DataFrame com contas a pagar
        df_pagas: DataFrame com contas pagas
        mes: Mês para exibir (padrão: mês atual)
        ano: Ano para exibir (padrão: ano atual)
    """
    # Usar mês e ano atuais se não especificados
    hoje = datetime.now()
    if not mes:
        mes = hoje.month
    if not ano:
        ano = hoje.year
    
    # Preparar dados
    if not df_a_pagar.empty:
        df_a_pagar = df_a_pagar.copy()
        df_a_pagar['data_vencimento'] = pd.to_datetime(df_a_pagar['data_vencimento'], errors='coerce')
        df_a_pagar = df_a_pagar.dropna(subset=['data_vencimento'])
    
    if not df_pagas.empty:
        df_pagas = df_pagas.copy()
        df_pagas['data_pagamento'] = pd.to_datetime(df_pagas['data_pagamento'], errors='coerce')
        df_pagas = df_pagas.dropna(subset=['data_pagamento'])
    
    nome_mes = obter_mes_nome_brasileiro(mes)
    
    # Criar título e seletores
    st.subheader(f"📅 Calendário Financeiro - {nome_mes} {ano}")
    
    # Seletor de modo de visualização, mês e ano
    col_modo, col_mes, col_ano = st.columns(3)
    
    with col_modo:
        modo_visualizacao = st.selectbox(
            "🔍 Modo de Visualização",
            ["📅 Semanal", "🗓️ Mensal"],
            key="modo_calendario",
            help="Escolha como deseja visualizar o calendário"
        )
    
    with col_mes:
        meses_brasileiros = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        mes_selecionado = st.selectbox("Mês", meses_brasileiros, index=mes-1, key="mes_calendario")
        novo_mes = meses_brasileiros.index(mes_selecionado) + 1
    
    with col_ano:
        novo_ano = st.number_input("Ano", min_value=2020, max_value=2030, value=ano, key="ano_calendario")
    
    # Se mudou mês ou ano, atualizar
    if novo_mes != mes or novo_ano != ano:
        mes = novo_mes
        ano = novo_ano
        nome_mes = obter_mes_nome_brasileiro(mes)
    
    # Mostrar calendário baseado no modo selecionado
    if modo_visualizacao == "📅 Semanal":
        # Calcular semanas do mês
        semanas = calcular_semanas_do_mes(ano, mes)
        
        # Seletor de semana
        st.markdown("---")
        st.markdown("### 📅 Selecione a Semana")
        
        opcoes_semanas = []
        for i, semana in enumerate(semanas):
            inicio = semana['inicio'].strftime('%d/%m')
            fim = semana['fim'].strftime('%d/%m')
            opcoes_semanas.append(f"Semana {i+1}: {inicio} - {fim}")
        
        semana_selecionada_idx = st.selectbox(
            "Semana",
            range(len(opcoes_semanas)),
            format_func=lambda x: opcoes_semanas[x],
            key="semana_selecionada"
        )
        
        semana_selecionada = semanas[semana_selecionada_idx]
        
        # Mostrar calendário semanal
        mostrar_calendario_semanal(
            semana_selecionada, df_a_pagar, df_pagas, mes, ano
        )
        
    else:  # Modo Mensal
        st.markdown("---")
        st.markdown("### 🗓️ Visualização Mensal")
        mostrar_calendario_mensal(df_a_pagar, df_pagas, mes, ano)
    
    # Mostrar detalhes do dia selecionado
    if 'dia_selecionado' in st.session_state:
        mostrar_detalhes_dia(st.session_state['dia_selecionado'], df_a_pagar, df_pagas)

def mostrar_detalhes_dia(dia_info, df_a_pagar, df_pagas):
    """
    Mostra os detalhes de um dia específico com tabela de fornecedores.
    
    Args:
        dia_info: Informações do dia selecionado
        df_a_pagar: DataFrame com contas a pagar
        df_pagas: DataFrame com contas pagas
    """
    dia = dia_info['dia']
    mes = dia_info['mes']
    ano = dia_info['ano']
    
    st.markdown("---")
    st.subheader(f"📋 Detalhes do Dia {dia:02d}/{mes:02d}/{ano}")
    
    # Criar data para filtrar
    data_filtro = datetime(ano, mes, dia).date()
    
    # Buscar dados do dia específico
    contas_a_pagar_dia = []
    contas_pagas_dia = []
    
    # Processar contas a pagar
    if not df_a_pagar.empty:
        for _, row in df_a_pagar.iterrows():
            data_vencimento = pd.to_datetime(row['data_vencimento'], errors='coerce')
            if pd.notna(data_vencimento):
                # Aplicar regra de fim de semana
                data_ajustada = ajustar_para_dia_util(data_vencimento)
                if data_ajustada.date() == data_filtro:
                    conta_info = {
                        'empresa': row['empresa'],
                        'fornecedor': row.get('fornecedor', 'N/A'),
                        'valor': row['valor'],
                        'descricao': row['descricao'],
                        'categoria': row.get('categoria', 'N/A'),
                        'data_original': data_vencimento.strftime('%d/%m/%Y'),
                        'transferida': data_vencimento.date() != data_filtro
                    }
                    contas_a_pagar_dia.append(conta_info)
    
    # Processar contas pagas
    if not df_pagas.empty:
        for _, row in df_pagas.iterrows():
            data_pagamento = pd.to_datetime(row['data_pagamento'], errors='coerce')
            if pd.notna(data_pagamento):
                # Aplicar regra de fim de semana
                data_ajustada = ajustar_para_dia_util(data_pagamento)
                if data_ajustada.date() == data_filtro:
                    conta_info = {
                        'empresa': row['empresa'],
                        'fornecedor': row.get('fornecedor', 'N/A'),
                        'valor': row['valor'],
                        'descricao': row['descricao'],
                        'categoria': row.get('categoria', 'N/A'),
                        'data_original': data_pagamento.strftime('%d/%m/%Y'),
                        'transferida': data_pagamento.date() != data_filtro
                    }
                    contas_pagas_dia.append(conta_info)
    
    # Mostrar as tabelas
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💸 Contas a Pagar")
        if contas_a_pagar_dia:
            df_a_pagar_dia = pd.DataFrame(contas_a_pagar_dia)
            # Formatar valores
            df_display = df_a_pagar_dia.copy()
            df_display['valor'] = df_display['valor'].apply(formatar_moeda_brasileira)
            
            # Renomear colunas
            df_display = df_display.rename(columns={
                'empresa': 'Empresa',
                'fornecedor': 'Fornecedor',
                'valor': 'Valor',
                'descricao': 'Descrição',
                'categoria': 'Categoria',
                'data_original': 'Data Original'
            })
            
            # Remover coluna transferida
            df_display = df_display.drop(columns=['transferida'], errors='ignore')
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma conta a pagar neste dia.")
    
    with col2:
        st.markdown("### ✅ Contas Pagas")
        if contas_pagas_dia:
            df_pagas_dia = pd.DataFrame(contas_pagas_dia)
            # Formatar valores
            df_display = df_pagas_dia.copy()
            df_display['valor'] = df_display['valor'].apply(formatar_moeda_brasileira)
            
            # Renomear colunas
            df_display = df_display.rename(columns={
                'empresa': 'Empresa',
                'fornecedor': 'Fornecedor',
                'valor': 'Valor',
                'descricao': 'Descrição',
                'categoria': 'Categoria',
                'data_original': 'Data Original'
            })
            
            # Remover coluna transferida
            df_display = df_display.drop(columns=['transferida'], errors='ignore')
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma conta paga neste dia.")
    
    # Resumo do dia
    st.markdown("### 📊 Resumo do Dia")
    
    col1, col2, col3 = st.columns(3)
    
    total_a_pagar = sum(conta['valor'] for conta in contas_a_pagar_dia)
    total_pagas = sum(conta['valor'] for conta in contas_pagas_dia)
    diferenca = total_a_pagar - total_pagas  # Corrigido: a_pagar - pago
    
    with col1:
        st.metric("Total a Pagar", formatar_moeda_brasileira(total_a_pagar), f"{len(contas_a_pagar_dia)} contas")
    with col2:
        st.metric("Total Pago", formatar_moeda_brasileira(total_pagas), f"{len(contas_pagas_dia)} contas")
    with col3:
        # Lógica correta: positivo = bom (sobrou dinheiro), negativo = ruim (estouro)
        if diferenca > 0:
            status_text = "✅ Economia"
        elif diferenca < 0:
            status_text = "❌ Estouro"
        else:
            status_text = "⚖️ Equilibrado"
            
        st.metric("Saldo do Dia", formatar_moeda_brasileira(diferenca), status_text)
    
    # Relatório de Fornecedores
    st.markdown("### 🏢 Relatório por Fornecedor")
    
    # Consolidar dados por fornecedor
    relatorio_fornecedores = {}
    
    # Processar contas a pagar
    for conta in contas_a_pagar_dia:
        fornecedor = conta['fornecedor']
        if fornecedor not in relatorio_fornecedores:
            relatorio_fornecedores[fornecedor] = {
                'fornecedor': fornecedor,
                'total_a_pagar': 0,
                'total_pago': 0,
                'qtd_a_pagar': 0,
                'qtd_pagas': 0
            }
        relatorio_fornecedores[fornecedor]['total_a_pagar'] += conta['valor']
        relatorio_fornecedores[fornecedor]['qtd_a_pagar'] += 1
    
    # Processar contas pagas
    for conta in contas_pagas_dia:
        fornecedor = conta['fornecedor']
        if fornecedor not in relatorio_fornecedores:
            relatorio_fornecedores[fornecedor] = {
                'fornecedor': fornecedor,
                'total_a_pagar': 0,
                'total_pago': 0,
                'qtd_a_pagar': 0,
                'qtd_pagas': 0
            }
        relatorio_fornecedores[fornecedor]['total_pago'] += conta['valor']
        relatorio_fornecedores[fornecedor]['qtd_pagas'] += 1
    
    if relatorio_fornecedores:
        # Converter para DataFrame
        df_fornecedores = pd.DataFrame(list(relatorio_fornecedores.values()))
        
        # Calcular diferença (total a pagar - total pago) = lógica correta
        df_fornecedores['diferenca'] = df_fornecedores['total_a_pagar'] - df_fornecedores['total_pago']
        
        # Formatar valores para exibição
        df_display_fornecedores = df_fornecedores.copy()
        df_display_fornecedores['total_a_pagar'] = df_display_fornecedores['total_a_pagar'].apply(formatar_moeda_brasileira)
        df_display_fornecedores['total_pago'] = df_display_fornecedores['total_pago'].apply(formatar_moeda_brasileira)
        df_display_fornecedores['diferenca'] = df_display_fornecedores['diferenca'].apply(formatar_moeda_brasileira)
        
        # Renomear colunas
        df_display_fornecedores = df_display_fornecedores.rename(columns={
            'fornecedor': 'Fornecedor',
            'total_a_pagar': 'Total a Pagar',
            'total_pago': 'Total Pago',
            'qtd_a_pagar': 'Qtd. a Pagar',
            'qtd_pagas': 'Qtd. Pagas',
            'diferenca': 'Saldo (A Pagar - Pago)'
        })
        
        # Ordenar por valor total (a pagar + pago) decrescente
        df_fornecedores['total_geral'] = df_fornecedores['total_a_pagar'] + df_fornecedores['total_pago']
        df_fornecedores = df_fornecedores.sort_values('total_geral', ascending=False)
        df_display_fornecedores = df_display_fornecedores.reindex(df_fornecedores.index)
        
        # Mostrar tabela
        st.dataframe(df_display_fornecedores, use_container_width=True, hide_index=True)
        
        # Resumo do relatório
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Fornecedores Únicos", len(relatorio_fornecedores))
        with col2:
            fornecedores_com_dividas = len([f for f in relatorio_fornecedores.values() if f['total_a_pagar'] > 0])
            st.metric("Com Valores a Pagar", fornecedores_com_dividas)
        with col3:
            fornecedores_com_pagamentos = len([f for f in relatorio_fornecedores.values() if f['total_pago'] > 0])
            st.metric("Com Pagamentos", fornecedores_com_pagamentos)
        
        # Botão para exportar relatório de fornecedores
        if st.button("📊 Exportar Relatório de Fornecedores (CSV)", type="secondary"):
            # Preparar dados para exportação
            df_export = df_fornecedores[['fornecedor', 'total_a_pagar', 'total_pago', 'qtd_a_pagar', 'qtd_pagas', 'diferenca']].copy()
            
            # Gerar CSV
            csv_data = df_export.to_csv(index=False, encoding='utf-8-sig')
            
            # Download
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"relatorio_fornecedores_{dia:02d}_{mes:02d}_{ano}.csv",
                mime="text/csv"
            )
    else:
        st.info("Nenhum fornecedor encontrado para este dia.")
    
    # Botão para limpar seleção
    if st.button("🔄 Voltar ao Calendário", type="secondary"):
        if 'dia_selecionado' in st.session_state:
            del st.session_state['dia_selecionado']
        st.rerun()
    
    # Seção de Auditoria
    st.markdown("---")
    st.markdown("### 🔍 Auditoria de Dados")
    
    col_audit1, col_audit2 = st.columns(2)
    
    with col_audit1:
        st.info("📋 **Como fazer auditoria:**\n"
                "1. Faça upload do arquivo Excel original\n"
                "2. Compare os totais com o sistema\n"
                "3. Identifique registros faltantes")
    
    with col_audit2:
        # Upload para auditoria
        arquivo_auditoria = st.file_uploader(
            "📤 Upload do Excel para auditoria",
            type=['xlsx', 'xls'],
            key=f"auditoria_{dia}_{mes}_{ano}",
            help="Faça upload do arquivo Excel original para comparar com os dados do sistema"
        )
    
    if arquivo_auditoria:
        if st.button("🔍 Executar Auditoria", type="primary"):
            executar_auditoria_dia(arquivo_auditoria, data_filtro, contas_a_pagar_dia, contas_pagas_dia)

def remover_arquivo_temporario(caminho_arquivo):
    """
    Remove arquivo temporário de forma segura, com tentativas múltiplas.
    
    Args:
        caminho_arquivo: Caminho para o arquivo temporário
    """
    
    if not os.path.exists(caminho_arquivo):
        return True
    
    # Tentar remover até 5 vezes com intervalos
    for tentativa in range(5):
        try:
            os.remove(caminho_arquivo)
            return True
        except (PermissionError, OSError):
            if tentativa < 4:  # Não é a última tentativa
                time.sleep(0.5)  # Aguardar 500ms antes da próxima tentativa
                continue
            else:
                # Última tentativa - apenas avisar que não foi possível remover
                st.warning(f"⚠️ Não foi possível remover arquivo temporário: {os.path.basename(caminho_arquivo)}")
                return False
    
    return False

def executar_auditoria_dia(arquivo_excel, data_filtro, contas_sistema_a_pagar, _contas_sistema_pagas):
    """
    Executa auditoria comparando dados do Excel com dados do sistema para um dia específico.
    
    Args:
        arquivo_excel: Arquivo Excel para auditoria
        data_filtro: Data do dia sendo auditado
        contas_sistema_a_pagar: Contas a pagar do sistema
        _contas_sistema_pagas: Contas pagas do sistema (não utilizado atualmente)
    """
    try:
        # Usar classes já importadas globalmente
        converter = ClientFileConverter()
        processor = ExcelProcessor()
        
        # Salvar arquivo temporário
        temp_path = f"temp_audit_{uuid.uuid4().hex[:8]}_{arquivo_excel.name}"
        
        with open(temp_path, "wb") as f:
            f.write(arquivo_excel.getbuffer())
        
        # DIAGNÓSTICO DETALHADO DE PROCESSAMENTO
        st.markdown("### 🔍 Diagnóstico de Processamento")
        
        # Ler arquivo bruto primeiro para diagnóstico
        try:
            if 'Modelo_Contas_Pagar' in arquivo_excel.name:
                df_bruto = pd.read_excel(temp_path, sheet_name='Contas a Pagar')
                formato_detectado = "Modelo_Contas_Pagar"
            else:
                df_bruto = pd.read_excel(temp_path)
                formato_detectado = "Padrão/ERP"
                
            st.info(f"📄 **Arquivo bruto**: {len(df_bruto)} linhas encontradas | **Formato**: {formato_detectado}")
            
            # Mostrar primeiras linhas para debug
            with st.expander("🔍 Ver primeiras 5 linhas do arquivo bruto"):
                st.dataframe(df_bruto.head(), use_container_width=True, hide_index=True)
                
        except Exception as e:
            st.error(f"❌ Erro ao ler arquivo bruto: {str(e)}")
            return
        
        # Processar arquivo com diagnóstico detalhado
        df_excel = None
        registros_removidos = {
            'empresas_vazias': 0,
            'valores_zero_ou_nan': 0,
            'datas_invalidas': 0,
            'outros_filtros': 0
        }
        
        # Contar filtros no arquivo bruto
        if formato_detectado == "Modelo_Contas_Pagar":
            # Verificar campos problemáticos no formato Modelo_Contas_Pagar
            if 'Empresa' in df_bruto.columns:
                registros_removidos['empresas_vazias'] = df_bruto['Empresa'].isna().sum()
            if 'ValorDoc' in df_bruto.columns:
                registros_removidos['valores_zero_ou_nan'] = (df_bruto['ValorDoc'].isna() | (df_bruto['ValorDoc'] == 0)).sum()
            if 'DataVencimento' in df_bruto.columns:
                registros_removidos['datas_invalidas'] = df_bruto['DataVencimento'].isna().sum()
        
        # Processar arquivo
        if converter.detectar_formato_modelo_contas_pagar(temp_path):
            st.info("📊 **Formato confirmado**: Modelo_Contas_Pagar")
            df_excel = converter.converter_modelo_contas_pagar(temp_path)
        elif converter.detectar_formato_cliente(temp_path):
            st.info("🔄 **Formato confirmado**: ERP do cliente")
            resultado = converter.processar_arquivo_completo(temp_path, salvar_convertido=False)
            if resultado['sucesso']:
                df_excel = resultado['dados_convertidos']
        else:
            st.info("📋 **Formato confirmado**: Padrão")
            df_excel = processor.carregar_arquivo_excel(temp_path)
        
        if df_excel is None or df_excel.empty:
            st.error("❌ Não foi possível processar o arquivo de auditoria")
            return
        
        # Mostrar estatísticas de processamento
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Registros Iniciais", len(df_bruto))
        with col2:
            st.metric("✅ Registros Processados", len(df_excel))
        with col3:
            registros_filtrados = len(df_bruto) - len(df_excel)
            st.metric("🚫 Registros Filtrados", registros_filtrados)
        
        # Detalhes dos filtros aplicados
        if registros_filtrados > 0:
            st.markdown("#### 🚫 Motivos dos Filtros Aplicados:")
            for motivo, quantidade in registros_removidos.items():
                if quantidade > 0:
                    st.warning(f"• **{motivo.replace('_', ' ').title()}**: {quantidade} registros removidos")
            
            # Explicação dos filtros
            st.info("""
            **ℹ️ Filtros automáticos aplicados pelo sistema:**
            - **Empresas vazias**: Registros sem nome da empresa são removidos
            - **Valores zero ou NaN**: Registros com valor 0 ou vazio são filtrados  
            - **Datas inválidas**: Registros sem data válida são excluídos
            - **Outros filtros**: Validações de formato e integridade de dados
            """)
        
        st.markdown("---")
        
        # Filtrar dados do Excel para o dia específico
        df_excel['data_vencimento'] = pd.to_datetime(df_excel['data_vencimento'], errors='coerce')
        
        # Aplicar regra de fim de semana para dados do Excel
        contas_excel_dia = []
        for _, row in df_excel.iterrows():
            if pd.notna(row['data_vencimento']):
                data_ajustada = ajustar_para_dia_util(row['data_vencimento'])
                if data_ajustada.date() == data_filtro:
                    contas_excel_dia.append({
                        'empresa': row['empresa'],
                        'fornecedor': row.get('fornecedor', 'N/A'),
                        'valor': row['valor'],
                        'descricao': row['descricao'],
                        'categoria': row.get('categoria', 'N/A'),
                        'data_original': row['data_vencimento'].strftime('%d/%m/%Y')
                    })
        
        # Calcular totais
        total_excel = sum(conta['valor'] for conta in contas_excel_dia)
        total_sistema = sum(conta['valor'] for conta in contas_sistema_a_pagar)
        diferenca = total_excel - total_sistema
        
        # Mostrar resultado da auditoria
        st.markdown("---")
        st.subheader("📊 Resultado da Auditoria")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "💼 Total Excel", 
                formatar_moeda_brasileira(total_excel),
                f"{len(contas_excel_dia)} registros"
            )
        
        with col2:
            st.metric(
                "💻 Total Sistema", 
                formatar_moeda_brasileira(total_sistema),
                f"{len(contas_sistema_a_pagar)} registros"
            )
        
        with col3:
            delta_color = "inverse" if diferenca < 0 else "normal"
            st.metric(
                "⚠️ Diferença", 
                formatar_moeda_brasileira(diferenca),
                f"{len(contas_excel_dia) - len(contas_sistema_a_pagar)} registros",
                delta_color=delta_color
            )
        
        # Análise detalhada
        if diferenca != 0:
            st.markdown("### 🔍 Análise Detalhada")
            
            # Criar DataFrames para comparação
            df_excel_comp = pd.DataFrame(contas_excel_dia)
            df_sistema_comp = pd.DataFrame(contas_sistema_a_pagar)
            
            if not df_excel_comp.empty and not df_sistema_comp.empty:
                # Comparar por chave única (empresa + valor + descrição)
                df_excel_comp['chave'] = (df_excel_comp['empresa'].astype(str) + "_" + 
                                        df_excel_comp['valor'].astype(str) + "_" + 
                                        df_excel_comp['descricao'].astype(str))
                
                df_sistema_comp['chave'] = (df_sistema_comp['empresa'].astype(str) + "_" + 
                                          df_sistema_comp['valor'].astype(str) + "_" + 
                                          df_sistema_comp['descricao'].astype(str))
                
                # Encontrar registros apenas no Excel
                chaves_excel = set(df_excel_comp['chave'])
                chaves_sistema = set(df_sistema_comp['chave'])
                
                apenas_excel = chaves_excel - chaves_sistema
                apenas_sistema = chaves_sistema - chaves_excel
                
                if apenas_excel:
                    st.markdown("#### 📤 Registros apenas no Excel (faltando no sistema):")
                    df_apenas_excel = df_excel_comp[df_excel_comp['chave'].isin(apenas_excel)].copy()
                    df_apenas_excel = df_apenas_excel.drop('chave', axis=1)
                    df_apenas_excel['valor'] = df_apenas_excel['valor'].apply(formatar_moeda_brasileira)
                    st.dataframe(df_apenas_excel, use_container_width=True, hide_index=True)
                    
                    total_faltando = df_excel_comp[df_excel_comp['chave'].isin(apenas_excel)]['valor'].sum()
                    st.error(f"💰 **Total faltando no sistema**: {formatar_moeda_brasileira(total_faltando)}")
                
                if apenas_sistema:
                    st.markdown("#### � Registros apenas no Sistema (não estão no Excel):")
                    df_apenas_sistema = df_sistema_comp[df_sistema_comp['chave'].isin(apenas_sistema)].copy()
                    df_apenas_sistema = df_apenas_sistema.drop('chave', axis=1)
                    df_apenas_sistema['valor'] = df_apenas_sistema['valor'].apply(formatar_moeda_brasileira)
                    st.dataframe(df_apenas_sistema, use_container_width=True, hide_index=True)
            
            elif df_excel_comp.empty and not df_sistema_comp.empty:
                st.warning("⚠️ Nenhum registro encontrado no Excel para este dia, mas existem registros no sistema.")
            elif not df_excel_comp.empty and df_sistema_comp.empty:
                st.warning("⚠️ Nenhum registro encontrado no sistema para este dia, mas existem registros no Excel.")
        else:
            st.success("✅ **Perfeito!** Os dados do Excel e do sistema estão idênticos para este dia.")
        
        # Simulação de re-importação
        st.markdown("---")
        st.markdown("### 🔄 **Simulação de Re-importação**")
        
        st.info("💡 **Quer saber o que aconteceria se você fizesse upload deste arquivo novamente?**")
        
        if st.button("🧪 Simular Re-importação do Arquivo Completo", type="secondary"):
            simular_reimportacao(df_excel, arquivo_excel.name)
        
        # Limpar arquivo temporário
        remover_arquivo_temporario(temp_path)
            
    except Exception as e:
        st.error(f"❌ Erro na auditoria: {str(e)}")
        if 'temp_path' in locals():
            remover_arquivo_temporario(temp_path)

def simular_reimportacao(df_excel, _nome_arquivo):
    """
    Simula o que aconteceria se o arquivo fosse reimportado.
    
    Args:
        df_excel: DataFrame processado do Excel
        _nome_arquivo: Nome do arquivo original (não utilizado atualmente)
    """
    try:
        # Importar cliente Supabase
        auth_mgr = st.session_state.get('auth_manager')
        if not auth_mgr:
            st.error("❌ Erro: Gerenciador de autenticação não encontrado")
            return
            
        supabase_client = auth_mgr.get_supabase_client()
        
        st.markdown("#### 🧪 Simulação de Re-importação")
        
        with st.spinner("Verificando duplicatas..."):
            # Simular verificação de duplicatas
            verificar_duplicatas = st.session_state.get('verificar_duplicatas', True)
            
            if verificar_duplicatas:
                duplicatas_info = supabase_client.verificar_duplicatas_contas_a_pagar(df_excel)
                
                registros_novos = duplicatas_info.get("novos", 0)
                duplicatas_encontradas = duplicatas_info.get("duplicatas", 0)
                total_registros = len(df_excel)
                
                st.markdown("##### 📊 Resultado da Simulação:")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "📄 Total no Arquivo",
                        total_registros,
                        "registros"
                    )
                
                with col2:
                    st.metric(
                        "✅ Seriam Importados",
                        registros_novos,
                        "novos registros"
                    )
                
                with col3:
                    st.metric(
                        "🔄 Duplicatas Ignoradas",
                        duplicatas_encontradas,
                        "já existem"
                    )
                
                # Explicação do que aconteceria
                if registros_novos > 0:
                    st.success(f"✅ **{registros_novos} registros novos** seriam importados para o banco de dados.")
                    
                    if duplicatas_encontradas > 0:
                        st.info(f"ℹ️ **{duplicatas_encontradas} registros duplicados** seriam ignorados (não importados novamente).")
                    
                    st.markdown("**🎯 Conclusão:** Fazer o upload novamente importaria apenas os registros que ainda não estão no banco.")
                    
                else:
                    if duplicatas_encontradas > 0:
                        st.warning(f"⚠️ **Todos os {total_registros} registros** já existem no banco de dados.")
                        st.markdown("**🎯 Conclusão:** Nenhum registro novo seria importado.")
                    else:
                        st.error("❌ **Problema detectado:** Nenhum registro seria importado e nenhuma duplicata foi encontrada.")
                
                # Mostrar registros que seriam importados
                if registros_novos > 0 and 'df_novos' in duplicatas_info:
                    df_novos = duplicatas_info['df_novos']
                    
                    if not df_novos.empty:
                        with st.expander(f"👀 Ver os {registros_novos} registros que seriam importados"):
                            df_display = df_novos.copy()
                            df_display['valor'] = df_display['valor'].apply(formatar_moeda_brasileira)
                            
                            # Selecionar colunas principais
                            colunas_display = ['empresa', 'fornecedor', 'valor', 'descricao', 'data_vencimento']
                            colunas_existentes = [col for col in colunas_display if col in df_display.columns]
                            
                            df_display = df_display[colunas_existentes].rename(columns={
                                'empresa': 'Empresa',
                                'fornecedor': 'Fornecedor', 
                                'valor': 'Valor',
                                'descricao': 'Descrição',
                                'data_vencimento': 'Data Vencimento'
                            })
                            
                            st.dataframe(df_display, use_container_width=True, hide_index=True)
                            
                            total_valor_novos = df_novos['valor'].sum()
                            st.metric("💰 Valor Total dos Novos Registros", formatar_moeda_brasileira(total_valor_novos))
            
            else:
                st.warning("⚠️ **Verificação de duplicatas desabilitada:** Todos os registros seriam importados, podendo gerar duplicatas no banco.")
                st.info("💡 **Recomendação:** Ative a verificação de duplicatas no sidebar antes de fazer o upload.")
        
        # Diagnóstico do motivo dos registros faltantes
        st.markdown("---")
        st.markdown("##### 🔍 **Por que alguns registros não foram importados?**")
        
        st.markdown("""
        **Possíveis motivos pelos quais registros podem ter sido excluídos na importação original:**
        
        1. **🚫 Valores zerados ou vazios**: Registros com valor = 0 ou campo vazio são automaticamente filtrados
        2. **📅 Datas inválidas**: Registros sem data de vencimento válida são removidos
        3. **🏢 Empresas vazias**: Registros sem nome da empresa são filtrados
        4. **🔄 Duplicatas**: Se a verificação estava ativada, registros duplicados foram ignorados
        5. **💥 Erros de conversão**: Campos que não puderam ser convertidos (ex: texto em campo numérico)
        """)
        
        # Recomendações
        st.markdown("##### 💡 **Recomendações:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🔧 Para importar registros faltantes:**
            - ✅ Verificar se verificação de duplicatas está ativada
            - ✅ Fazer upload novamente do mesmo arquivo
            - ✅ Apenas registros novos serão importados
            """)
        
        with col2:
            st.markdown("""
            **⚠️ Para evitar problemas futuros:**
            - 📊 Verificar dados antes do upload (sem valores zerados)  
            - 📅 Confirmar que todas as datas estão preenchidas
            - 🏢 Verificar se todas as empresas estão nomeadas
            """)
            
    except Exception as e:
        st.error(f"❌ Erro na simulação: {str(e)}")

def executar_auditoria_completa(arquivo_excel, supabase_client):
    """
    Executa auditoria completa comparando todos os dados do Excel com o sistema.
    
    Args:
        arquivo_excel: Arquivo Excel para auditoria
        supabase_client: Cliente do Supabase para buscar dados do sistema
    """
    try:
        # Usar classes já importadas globalmente
        converter = ClientFileConverter()
        processor = ExcelProcessor()
        
        with st.spinner("🔍 Executando auditoria completa..."):
            # Salvar arquivo temporário
            temp_path = f"temp_audit_completa_{uuid.uuid4().hex[:8]}_{arquivo_excel.name}"
            
            with open(temp_path, "wb") as f:
                f.write(arquivo_excel.getbuffer())
            
            # Processar arquivo
            df_excel = None
            
            if converter.detectar_formato_modelo_contas_pagar(temp_path):
                st.info("📊 Formato Modelo_Contas_Pagar detectado")
                df_excel = converter.converter_modelo_contas_pagar(temp_path)
            elif converter.detectar_formato_cliente(temp_path):
                st.info("🔄 Formato ERP detectado")
                resultado = converter.processar_arquivo_completo(temp_path, salvar_convertido=False)
                if resultado['sucesso']:
                    df_excel = resultado['dados_convertidos']
            else:
                st.info("📋 Formato padrão detectado")
                df_excel = processor.carregar_arquivo_excel(temp_path)
            
            if df_excel is None or df_excel.empty:
                st.error("❌ Não foi possível processar o arquivo de auditoria")
                return
            
            # Buscar dados do sistema
            df_sistema = supabase_client.buscar_contas_a_pagar()
            
            # Preparar dados para comparação
            df_excel['data_vencimento'] = pd.to_datetime(df_excel['data_vencimento'], errors='coerce')
            df_sistema['data_vencimento'] = pd.to_datetime(df_sistema['data_vencimento'], errors='coerce')
            
            # Calcular totais
            total_excel = df_excel['valor'].sum()
            total_sistema = df_sistema['valor'].sum()
            diferenca = total_excel - total_sistema
            
            # Mostrar resultado
            st.markdown("---")
            st.subheader("📊 Auditoria Completa - Resultado")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "💼 Total Excel", 
                    formatar_moeda_brasileira(total_excel),
                    f"{len(df_excel)} registros"
                )
            
            with col2:
                st.metric(
                    "💻 Total Sistema", 
                    formatar_moeda_brasileira(total_sistema),
                    f"{len(df_sistema)} registros"
                )
            
            with col3:
                delta_color = "inverse" if diferenca < 0 else "normal"
                st.metric(
                    "⚠️ Diferença", 
                    formatar_moeda_brasileira(diferenca),
                    f"{len(df_excel) - len(df_sistema)} registros",
                    delta_color=delta_color
                )
            
            # Análise por período
            if not df_excel.empty and not df_sistema.empty:
                st.markdown("### 📅 Análise por Período")
                
                # Agrupar por mês/ano
                df_excel['periodo'] = df_excel['data_vencimento'].dt.to_period('M')
                df_sistema['periodo'] = df_sistema['data_vencimento'].dt.to_period('M')
                
                resumo_excel = df_excel.groupby('periodo').agg({
                    'valor': 'sum',
                    'empresa': 'count'
                }).rename(columns={'empresa': 'quantidade'})
                
                resumo_sistema = df_sistema.groupby('periodo').agg({
                    'valor': 'sum',
                    'empresa': 'count'
                }).rename(columns={'empresa': 'quantidade'})
                
                # Combinar resumos
                resumo_comparativo = resumo_excel.join(resumo_sistema, lsuffix='_excel', rsuffix='_sistema', how='outer').fillna(0)
                resumo_comparativo['diferenca_valor'] = resumo_comparativo['valor_excel'] - resumo_comparativo['valor_sistema']
                resumo_comparativo['diferenca_qtd'] = resumo_comparativo['quantidade_excel'] - resumo_comparativo['quantidade_sistema']
                
                # Formatar para exibição
                df_display = resumo_comparativo.copy()
                df_display['valor_excel'] = df_display['valor_excel'].apply(formatar_moeda_brasileira)
                df_display['valor_sistema'] = df_display['valor_sistema'].apply(formatar_moeda_brasileira)
                df_display['diferenca_valor'] = df_display['diferenca_valor'].apply(formatar_moeda_brasileira)
                
                df_display = df_display.rename(columns={
                    'valor_excel': 'Valor Excel',
                    'valor_sistema': 'Valor Sistema',
                    'quantidade_excel': 'Qtd Excel',
                    'quantidade_sistema': 'Qtd Sistema',
                    'diferenca_valor': 'Diferença Valor',
                    'diferenca_qtd': 'Diferença Qtd'
                })
                
                st.dataframe(df_display, use_container_width=True, hide_index=False)
            
            # Sugestões de correção
            if diferenca != 0:
                st.markdown("### 💡 Sugestões para Correção")
                
                if diferenca > 0:
                    st.warning(f"⚠️ **Faltam dados no sistema:** {formatar_moeda_brasileira(diferenca)}")
                    st.markdown("""
                    **Possíveis causas:**
                    - Arquivos não foram importados completamente
                    - Dados foram filtrados durante a importação
                    - Duplicatas foram removidas incorretamente
                    - Formato de data incompatível
                    """)
                else:
                    st.warning(f"⚠️ **Excesso de dados no sistema:** {formatar_moeda_brasileira(abs(diferenca))}")
                    st.markdown("""
                    **Possíveis causas:**
                    - Dados duplicados no sistema
                    - Importações múltiplas do mesmo arquivo
                    - Dados de períodos diferentes
                    """)
                
                st.markdown("""
                **Recomendações:**
                1. 🗑️ Limpe os dados do sistema usando os botões na barra lateral
                2. 📤 Reimporte o arquivo com verificação de duplicatas ativada
                3. 🔍 Use a auditoria por dia específico para análise detalhada
                4. 📋 Verifique se o formato do arquivo está correto
                """)
            else:
                st.success("✅ **Auditoria OK!** Os dados estão consistentes entre Excel e sistema.")
            
            # Limpar arquivo temporário
            remover_arquivo_temporario(temp_path)
    
    except Exception as e:
        st.error(f"❌ Erro na auditoria completa: {str(e)}")
        if 'temp_path' in locals():
            remover_arquivo_temporario(temp_path)

def calcular_semanas_do_mes(ano, mes):
    """
    Calcula todas as semanas de um mês específico.
    Retorna lista com informações de cada semana.
    """
    # Configurar para começar com domingo
    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(ano, mes)
    
    semanas = []
    
    for semana_idx, semana in enumerate(cal):
        # Encontrar primeiro e último dia da semana que pertencem ao mês
        dias_validos = [dia for dia in semana if dia != 0]
        
        if dias_validos:
            primeiro_dia = min(dias_validos)
            ultimo_dia = max(dias_validos)
            
            inicio = datetime(ano, mes, primeiro_dia)
            fim = datetime(ano, mes, ultimo_dia)
            
            semanas.append({
                'numero': semana_idx + 1,
                'inicio': inicio,
                'fim': fim,
                'dias': dias_validos
            })
    
    return semanas

def mostrar_calendario_semanal(semana_info, df_a_pagar, df_pagas, mes, ano):
    """
    Mostra o calendário da semana selecionada com informações financeiras detalhadas.
    """
    # CSS global para reduzir botões do calendário
    st.markdown("""
    <style>
    /* Aplicar estilos específicos para botões do calendário */
    div[data-testid="stButton"] > button,
    .stButton > button,
    button[kind="primary"],
    button[kind="secondary"] {
        font-size: 0.55rem !important;
        padding: 3px 6px !important;
        height: auto !important;
        min-height: 24px !important;
        max-height: 32px !important;
        border-radius: 4px !important;
        font-weight: 500 !important;
        border: 1px solid #cbd5e1 !important;
        background: #f8fafc !important;
        color: #475569 !important;
        line-height: 1.2 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    div[data-testid="stButton"] > button:hover,
    .stButton > button:hover {
        background: #e2e8f0 !important;
        border-color: #94a3b8 !important;
        transform: none !important;
    }
    /* Força aplicação em todos os contextos */
    .stApp button {
        font-size: 0.55rem !important;
        padding: 3px 6px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(f"### 📅 Semana {semana_info['numero']} - {semana_info['inicio'].strftime('%d/%m')} a {semana_info['fim'].strftime('%d/%m')}")
    
    # Calcular dados da semana
    dados_semana = calcular_dados_semana(semana_info, df_a_pagar, df_pagas, mes, ano)
    
    # Mostrar legenda
    st.markdown("#### 📋 Legenda:")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("🔴 **A Pagar** - Valores pendentes")
    with col2:
        st.markdown("🟢 **Pago** - Valores pagos")
    with col3:
        st.markdown("🔵 **Saldo** - A Pagar - Pago (Positivo=Economia, Negativo=Estouro)")
    with col4:
        st.markdown("📅 **Hoje** - Dia atual (destaque azul)")
    
    st.info("💡 **Regra de Negócio**: Valores de sábados e domingos são automaticamente transferidos para a próxima segunda-feira.")
    
    # Criar grid da semana
    dias_semana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
    
    # Cabeçalho dos dias da semana
    cols_header = st.columns(7)
    for i, dia_nome in enumerate(dias_semana):
        with cols_header[i]:
            st.markdown(f"""
            <div style="
                text-align: center; 
                font-weight: bold; 
                padding: 12px 8px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 8px; 
                margin-bottom: 8px;
                font-size: 14px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                {dia_nome}
            </div>
            """, unsafe_allow_html=True)
    
    # Criar linha da semana
    cols_semana = st.columns(7)
    
    # Preencher dias da semana
    for dia_semana_idx in range(7):  # 0=domingo, 6=sábado
        with cols_semana[dia_semana_idx]:
            # Verificar se existe dia válido para esta posição na semana
            dia_mes = None
            
            # Encontrar o dia do mês correspondente a esta posição da semana
            for dia in semana_info['dias']:
                data_dia = datetime(ano, mes, dia)
                if data_dia.weekday() == (dia_semana_idx - 1) % 7:  # Ajustar porque datetime usa segunda=0
                    dia_mes = dia
                    break
            
            if dia_mes:
                mostrar_dia_semana(dia_mes, dados_semana.get(dia_mes, {}), mes, ano)
            else:
                # Dia vazio
                st.markdown("""
                <div style="
                    padding: 20px; 
                    margin: 4px 0;
                    min-height: 235px;
                    background: #f8fafc;
                    border: 2px dashed #cbd5e1;
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #94a3b8;
                    font-style: italic;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                ">
                    <span style='font-size: 14px;'>Dia não pertence ao mês</span>
                </div>
                """, unsafe_allow_html=True)
    
    # Resumo da semana
    mostrar_resumo_semana(dados_semana, semana_info)

def mostrar_calendario_mensal(df_a_pagar, df_pagas, mes, ano):
    """
    Mostra o calendário mensal completo com informações financeiras compactas.
    """
    # Importar calendar
    # CSS para calendário mensal - ainda mais compacto
    st.markdown("""
    <style>
    /* Estilos específicos para calendário mensal */
    .calendario-mensal {
        font-size: 0.7rem !important;
    }
    .calendario-mensal div[data-testid="stButton"] > button {
        font-size: 0.45rem !important;
        padding: 2px 4px !important;
        height: auto !important;
        min-height: 20px !important;
        max-height: 24px !important;
        line-height: 1.1 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Calcular dados do mês inteiro
    dados_mes = calcular_dados_mes_completo(df_a_pagar, df_pagas, mes, ano)
    
    # Configurar calendário para começar no domingo
    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(ano, mes)
    
    # Mostrar legenda
    st.markdown("#### 📋 Legenda:")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("🔴 **A Pagar** - Valores pendentes")
    with col2:
        st.markdown("🟢 **Pago** - Valores pagos") 
    with col3:
        st.markdown("🔵 **Saldo** - A Pagar - Pago (Positivo=Economia, Negativo=Estouro)")
    with col4:
        st.markdown("📅 **Hoje** - Dia atual (destaque azul)")
    
    st.info("💡 **Regra de Negócio**: Valores de sábados e domingos são automaticamente transferidos para a próxima segunda-feira.")
    
    # Cabeçalho dos dias da semana
    dias_semana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
    cols_header = st.columns(7)
    for i, dia_nome in enumerate(dias_semana):
        with cols_header[i]:
            st.markdown(f"""
            <div style="
                text-align: center; 
                font-weight: bold; 
                padding: 8px 4px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 6px; 
                margin-bottom: 4px;
                font-size: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            ">
                {dia_nome}
            </div>
            """, unsafe_allow_html=True)
    
    # Mostrar semanas do mês
    for semana in cal:
        cols_semana = st.columns(7)
        
        for dia_semana_idx, dia in enumerate(semana):
            with cols_semana[dia_semana_idx]:
                if dia == 0:
                    # Dia vazio (não pertence ao mês)
                    st.markdown("""
                    <div style="
                        padding: 20px; 
                        margin: 20px 0;
                        min-height: 150px;
                        background: #f8fafc;
                        border: 1px dashed #e2e8f0;
                        border-radius: 6px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: #cbd5e1;
                        font-style: italic;
                        font-size: 15px;
                    ">
                        -
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Dia válido - usar função compacta
                    with st.container():
                        st.markdown('<div class="calendario-mensal">', unsafe_allow_html=True)
                        mostrar_dia_mensal(dia, dados_mes.get(dia, {}), mes, ano)
                        st.markdown('</div>', unsafe_allow_html=True)
    
    # Resumo do mês
    st.markdown("---")
    st.markdown("### 📊 Resumo do Mês")
    mostrar_resumo_mes(dados_mes)

def calcular_dados_mes_completo(df_a_pagar, df_pagas, mes, ano):
    """
    Calcula os dados financeiros para todos os dias do mês.
    """
    # Obter número de dias no mês
    _, dias_no_mes = calendar.monthrange(ano, mes)
    
    dados_mes = {}
    
    # Inicializar todos os dias do mês
    for dia in range(1, dias_no_mes + 1):
        dados_mes[dia] = {
            'a_pagar': 0,
            'pagas': 0,
            'qtd_a_pagar': 0,
            'qtd_pagas': 0,
            'contas_a_pagar': [],
            'contas_pagas': []
        }
    
    # Processar contas a pagar
    if not df_a_pagar.empty:
        for _, row in df_a_pagar.iterrows():
            data_original = pd.to_datetime(row['data_vencimento'], errors='coerce')
            if pd.notna(data_original):
                data_ajustada = ajustar_para_dia_util(data_original)
                
                # Verificar se a data ajustada está no mês/ano atual
                if data_ajustada.month == mes and data_ajustada.year == ano:
                    dia = data_ajustada.day
                    valor = float(row['valor'])
                    
                    dados_mes[dia]['a_pagar'] += valor
                    dados_mes[dia]['qtd_a_pagar'] += 1
                    dados_mes[dia]['contas_a_pagar'].append({
                        'empresa': row['empresa'],
                        'fornecedor': row.get('fornecedor', 'N/A'),
                        'valor': valor,
                        'descricao': row['descricao'],
                        'data_original': data_original.strftime('%d/%m/%Y'),
                        'transferida': data_original.date() != data_ajustada.date()
                    })

    # Processar contas pagas
    if not df_pagas.empty:
        for _, row in df_pagas.iterrows():
            data_original = pd.to_datetime(row['data_pagamento'], errors='coerce')
            if pd.notna(data_original):
                data_ajustada = ajustar_para_dia_util(data_original)
                
                # Verificar se a data ajustada está no mês/ano atual
                if data_ajustada.month == mes and data_ajustada.year == ano:
                    dia = data_ajustada.day
                    valor = float(row['valor'])
                    
                    dados_mes[dia]['pagas'] += valor
                    dados_mes[dia]['qtd_pagas'] += 1
                    dados_mes[dia]['contas_pagas'].append({
                        'empresa': row['empresa'],
                        'fornecedor': row.get('fornecedor', 'N/A'),
                        'valor': valor,
                        'descricao': row['descricao'],
                        'data_original': data_original.strftime('%d/%m/%Y'),
                        'transferida': data_original.date() != data_ajustada.date()
                    })
    
    return dados_mes

def mostrar_dia_mensal(dia, dados_dia, mes, ano):
    """
    Mostra um dia específico na visualização mensal - versão ultra compacta.
    """
    hoje = datetime.now()
    
    # Verificar se é hoje
    eh_hoje = dia == hoje.day and mes == hoje.month and ano == hoje.year
    
    # Calcular diferença (lógica correta: a_pagar - pagas)
    diferenca = dados_dia.get('a_pagar', 0) - dados_dia.get('pagas', 0)
    
    if dados_dia.get('a_pagar', 0) > 0 or dados_dia.get('pagas', 0) > 0:
        # Dia com movimentação - versão ultra compacta
        with st.container():
            # Número do dia
            if eh_hoje:
                st.markdown(f"<div style='text-align: center; font-weight: bold; margin-bottom: 4px; color: #2563eb;'>📅 {dia}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align: center; font-weight: bold; margin-bottom: 4px;'>{dia}</div>", unsafe_allow_html=True)
            
            # Valores ultra compactos
            a_pagar_valor = formatar_moeda_brasileira(dados_dia.get('a_pagar', 0), com_simbolo=False)
            pago_valor = formatar_moeda_brasileira(dados_dia.get('pagas', 0), com_simbolo=False)
            diferenca_valor = formatar_moeda_brasileira(diferenca, com_simbolo=False)
            
            # A Pagar
            st.markdown(f"""
            <div style="margin: 1px 0; padding: 2px; border-radius: 3px; background: #fff5f5;">
                <div style="font-size: 0.8rem; color: #dc2626;">🔴 {a_pagar_valor}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Pago
            st.markdown(f"""
            <div style="margin: 1px 0; padding: 2px; border-radius: 3px; background: #f0fdf4;">
                <div style="font-size: 0.8rem; color: #16a34a;">🟢 {pago_valor}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Diferença
            cor_diferenca = "#16a34a" if diferenca > 0 else "#dc2626" if diferenca < 0 else "#6b7280"
            cor_fundo_diferenca = "#f0fdf4" if diferenca > 0 else "#fff5f5" if diferenca < 0 else "#f8fafc"
            icone_diferenca = "🔺" if diferenca > 0 else "🔻" if diferenca < 0 else "➖"
            
            st.markdown(f"""
            <div style="margin: 1px 0; padding: 2px; border-radius: 3px; background: {cor_fundo_diferenca};">
                <div style="font-size: 0.8rem; color: {cor_diferenca};">{icone_diferenca} {diferenca_valor}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Botão compacto para ver detalhes
        if st.button(
            f"📋 {dia}",
            key=f"dia_mensal_{dia}_{mes}_{ano}",
            help=f"Ver detalhes do dia {dia:02d}/{mes:02d}/{ano}",
            use_container_width=True
        ):
            st.session_state['dia_selecionado'] = {
                'dia': dia,
                'mes': mes,
                'ano': ano
            }
            st.rerun()
            
    else:
        # Dia sem movimentação - ultra compacto
        cor_fundo = "#dbeafe" if eh_hoje else "#f8fafc"
        icone_dia = "📅" if eh_hoje else ""
        
        st.markdown(f"""
        <div style="
            background: {cor_fundo};
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 4px;
            margin: 2px 0;
            min-height: 80px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        ">
            <div style="font-size: 14px; font-weight: bold; color: #6b7280; margin-bottom: 4px;">
                {icone_dia} {dia}
            </div>
            <div style="
                font-size: 0.45rem; 
                color: #9ca3af; 
                font-style: italic; 
                min-height: 116px; 
                text-align: center;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            ">
                Sem movimento
            </div>
        </div>
        """, unsafe_allow_html=True)

def mostrar_resumo_mes(dados_mes):
    """
    Mostra o resumo financeiro do mês completo.
    """
    # Calcular totais do mês
    total_a_pagar = sum(dados_dia.get('a_pagar', 0) for dados_dia in dados_mes.values())
    total_pagas = sum(dados_dia.get('pagas', 0) for dados_dia in dados_mes.values())
    total_contas_a_pagar = sum(dados_dia.get('qtd_a_pagar', 0) for dados_dia in dados_mes.values())
    total_contas_pagas = sum(dados_dia.get('qtd_pagas', 0) for dados_dia in dados_mes.values())
    diferenca_mes = total_a_pagar - total_pagas  # Corrigido: a_pagar - pagas
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Usar HTML personalizado para controle total do tamanho
    with col1:
        valor_a_pagar = formatar_moeda_brasileira(total_a_pagar)
        st.markdown(f"""
        <div style="padding: 12px; border-radius: 8px; background: #fff5f5; border: 2px solid #fecaca;">
            <div style="font-size: 0.65rem; font-weight: normal; color: #dc2626; margin-bottom: 4px;">💸 Total a Pagar</div>
            <div style="font-size: 0.9rem; font-weight: bold; color: #dc2626; margin-bottom: 4px;">{valor_a_pagar}</div>
            <div style="font-size: 0.6rem; color: #9ca3af;">{total_contas_a_pagar} contas</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        valor_pago = formatar_moeda_brasileira(total_pagas)
        st.markdown(f"""
        <div style="padding: 12px; border-radius: 8px; background: #f0fdf4; border: 2px solid #bbf7d0;">
            <div style="font-size: 0.65rem; font-weight: normal; color: #16a34a; margin-bottom: 4px;">✅ Total Pago</div>
            <div style="font-size: 0.9rem; font-weight: bold; color: #16a34a; margin-bottom: 4px;">{valor_pago}</div>
            <div style="font-size: 0.6rem; color: #9ca3af;">{total_contas_pagas} contas</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        valor_diferenca = formatar_moeda_brasileira(diferenca_mes)
        # Lógica correta: positivo = bom (sobrou dinheiro), negativo = ruim (estouro)
        cor_fundo = "#f0fdf4" if diferenca_mes >= 0 else "#fff5f5"
        cor_borda = "#bbf7d0" if diferenca_mes >= 0 else "#fecaca"
        cor_texto = "#16a34a" if diferenca_mes >= 0 else "#dc2626"
        status_texto = "✅ Economia" if diferenca_mes > 0 else ("❌ Estouro" if diferenca_mes < 0 else "⚖️ Equilibrado")
        
        st.markdown(f"""
        <div style="padding: 12px; border-radius: 8px; background: {cor_fundo}; border: 2px solid {cor_borda};">
            <div style="font-size: 0.65rem; font-weight: normal; color: {cor_texto}; margin-bottom: 4px;">📊 Saldo do Mês</div>
            <div style="font-size: 0.9rem; font-weight: bold; color: {cor_texto}; margin-bottom: 4px;">{valor_diferenca}</div>
            <div style="font-size: 0.6rem; color: #9ca3af;">{status_texto}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        dias_com_movimento = len([d for d in dados_mes.values() if d.get('a_pagar', 0) > 0 or d.get('pagas', 0) > 0])
        percentual = round(dias_com_movimento/len(dados_mes)*100)
        
        st.markdown(f"""
        <div style="padding: 12px; border-radius: 8px; background: #f1f5f9; border: 2px solid #cbd5e1;">
            <div style="font-size: 0.65rem; font-weight: normal; color: #475569; margin-bottom: 4px;">📅 Dias com Movimento</div>
            <div style="font-size: 0.9rem; font-weight: bold; color: #475569; margin-bottom: 4px;">{dias_com_movimento}/{len(dados_mes)}</div>
            <div style="font-size: 0.6rem; color: #9ca3af;">{percentual}% do mês</div>
        </div>
        """, unsafe_allow_html=True)

def calcular_dados_semana(semana_info, df_a_pagar, df_pagas, mes, ano):
    """
    Calcula os dados financeiros para cada dia da semana.
    """
    dados_semana = {}
    
    for dia in semana_info['dias']:
        dados_semana[dia] = {
            'a_pagar': 0,
            'pagas': 0,
            'qtd_a_pagar': 0,
            'qtd_pagas': 0,
            'contas_a_pagar': [],
            'contas_pagas': []
        }
    
    # Processar contas a pagar
    if not df_a_pagar.empty:
        for _, row in df_a_pagar.iterrows():
            data_original = pd.to_datetime(row['data_vencimento'], errors='coerce')
            if pd.notna(data_original):
                data_ajustada = ajustar_para_dia_util(data_original)
                
                # Verificar se a data ajustada está na semana atual
                if (data_ajustada.month == mes and 
                    data_ajustada.year == ano and 
                    data_ajustada.day in semana_info['dias']):
                    
                    dia = data_ajustada.day
                    valor = float(row['valor'])
                    
                    dados_semana[dia]['a_pagar'] += valor
                    dados_semana[dia]['qtd_a_pagar'] += 1
                    dados_semana[dia]['contas_a_pagar'].append({
                        'empresa': row['empresa'],
                        'fornecedor': row.get('fornecedor', 'N/A'),
                        'valor': valor,
                        'descricao': row['descricao'],
                        'data_original': data_original.strftime('%d/%m/%Y'),
                        'transferida': data_original.date() != data_ajustada.date()
                    })
    
    # Processar contas pagas
    if not df_pagas.empty:
        for _, row in df_pagas.iterrows():
            data_original = pd.to_datetime(row['data_pagamento'], errors='coerce')
            if pd.notna(data_original):
                data_ajustada = ajustar_para_dia_util(data_original)
                
                # Verificar se a data ajustada está na semana atual
                if (data_ajustada.month == mes and 
                    data_ajustada.year == ano and 
                    data_ajustada.day in semana_info['dias']):
                    
                    dia = data_ajustada.day
                    valor = float(row['valor'])
                    
                    dados_semana[dia]['pagas'] += valor
                    dados_semana[dia]['qtd_pagas'] += 1
                    dados_semana[dia]['contas_pagas'].append({
                        'empresa': row['empresa'],
                        'fornecedor': row.get('fornecedor', 'N/A'),
                        'valor': valor,
                        'descricao': row['descricao'],
                        'data_original': data_original.strftime('%d/%m/%Y'),
                        'transferida': data_original.date() != data_ajustada.date()
                    })
    
    return dados_semana

def mostrar_dia_semana(dia, dados_dia, mes, ano):
    """
    Mostra um dia específico na visualização semanal.
    """
    hoje = datetime.now()
    
    # Determinar cor de fundo baseada na atividade
    cor_fundo = "#f8f9fa"  # Cinza claro padrão
    cor_borda = "#dee2e6"
    
    # Verificar se é fim de semana
    data_dia = datetime(ano, mes, dia)
    eh_fim_de_semana = data_dia.weekday() >= 5  # 5=sábado, 6=domingo
    
    if dados_dia.get('a_pagar', 0) > 0 and dados_dia.get('pagas', 0) == 0:
        cor_fundo = "#fff5f5"  # Vermelho muito claro (só a pagar)
        cor_borda = "#fca5a5"
    elif dados_dia.get('pagas', 0) > 0 and dados_dia.get('a_pagar', 0) == 0:
        cor_fundo = "#f0fdf4"  # Verde muito claro (só pagas)
        cor_borda = "#86efac"
    elif dados_dia.get('a_pagar', 0) > 0 and dados_dia.get('pagas', 0) > 0:
        cor_fundo = "#fffbeb"  # Laranja muito claro (ambos)
        cor_borda = "#fbbf24"
    
    # Destacar fim de semana com valores zerados (transferidos)
    if eh_fim_de_semana and dados_dia.get('a_pagar', 0) == 0 and dados_dia.get('pagas', 0) == 0:
        cor_fundo = "#f1f5f9"  # Cinza azulado para fim de semana
        cor_borda = "#cbd5e1"
    
    # Verificar se é hoje
    if dia == hoje.day and mes == hoje.month and ano == hoje.year:
        cor_fundo = "#dbeafe"  # Azul claro para hoje
        cor_borda = "#60a5fa"
    
    # Calcular diferença (lógica correta: a_pagar - pagas)
    diferenca = dados_dia.get('a_pagar', 0) - dados_dia.get('pagas', 0)
    
    # Definir ícones baseados no contexto do dia
    icone_dia = ""
    
    # Verificar se é hoje (prioridade máxima)
    if dia == hoje.day and mes == hoje.month and ano == hoje.year:
        icone_dia = "📅"  # Ícone para o dia atual
    # Verificar se é segunda-feira (pode ter recebido transferências)
    elif data_dia.weekday() == 0:
        icone_dia = "📈"  # Ícone para segunda-feira (transferências)
    
    if dados_dia.get('a_pagar', 0) > 0 or dados_dia.get('pagas', 0) > 0:
        # Usar componentes nativos do Streamlit ao invés de HTML
        with st.container():
            # Criar um container com estilo baseado na atividade
            if dia == hoje.day and mes == hoje.month and ano == hoje.year:
                st.markdown(f"<div style='text-align: center; font-weight: bold; margin-bottom: 8px;'>📅 {dia}(Hoje)</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align: center; font-weight: bold; margin-bottom: 8px;'>{dia}</div>", unsafe_allow_html=True)
            
            # Usar HTML personalizado ao invés de st.metric para controle total do tamanho
            a_pagar_valor = formatar_moeda_brasileira(dados_dia.get('a_pagar', 0), com_simbolo=False)
            a_pagar_qtd = dados_dia.get('qtd_a_pagar', 0)
            pago_valor = formatar_moeda_brasileira(dados_dia.get('pagas', 0), com_simbolo=False)
            pago_qtd = dados_dia.get('qtd_pagas', 0)
        
            st.markdown(f"""
            <div style="margin: 4px 0; padding: 4px; border-radius: 4px; background: #fff5f5;">
                <div style="font-size: 0.5rem; font-weight: normal; color: #dc2626; margin-bottom: 1px;">🔴 A Pagar</div>
                <div style="font-size: 0.65rem; font-weight: bold; color: #dc2626; margin-bottom: 1px;">{a_pagar_valor}</div>
                <div style="font-size: 0.45rem; color: #9ca3af;">{a_pagar_qtd} contas</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="margin: 4px 0; padding: 4px; border-radius: 4px; background: #f0fdf4;">
                <div style="font-size: 0.5rem; font-weight: normal; color: #16a34a; margin-bottom: 1px;">🟢 Pago</div>
                <div style="font-size: 0.65rem; font-weight: bold; color: #16a34a; margin-bottom: 1px;">{pago_valor}</div>
                <div style="font-size: 0.45rem; color: #9ca3af;">{pago_qtd} contas</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Diferença com quadro igual aos outros componentes
            diferenca_valor = formatar_moeda_brasileira(diferenca, com_simbolo=False)
            # Determinar ícone e cores baseado na lógica correta
            # Positivo = bom (sobrou dinheiro), negativo = ruim (estouro)
            icone_diferenca = "✅" if diferenca > 0 else "❌" if diferenca < 0 else "➖"
            cor_diferenca = "#16a34a" if diferenca > 0 else "#dc2626" if diferenca < 0 else "#6b7280"
            cor_fundo_diferenca = "#f0fdf4" if diferenca > 0 else "#fff5f5" if diferenca < 0 else "#f8fafc"
            status_diferenca = "Economia" if diferenca > 0 else "Estouro" if diferenca < 0 else "Equilibrado"
            
            st.markdown(f"""
            <div style="margin: 4px 0; padding: 4px; border-radius: 4px; background: {cor_fundo_diferenca};">
                <div style="font-size: 0.5rem; font-weight: normal; color: {cor_diferenca}; margin-bottom: 1px;">{icone_diferenca} Saldo</div>
                <div style="font-size: 0.65rem; font-weight: bold; color: {cor_diferenca}; margin-bottom: 1px;">{diferenca_valor}</div>
                <div style="font-size: 0.45rem; color: #9ca3af;">{status_diferenca}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Botão para ver detalhes do dia
        if st.button(
            f"📋 Dia {dia}",
            key=f"dia_semanal_{dia}_{mes}_{ano}",
            help=f"Ver detalhes do dia {dia:02d}/{mes:02d}/{ano}",
            use_container_width=True
        ):
            st.session_state['dia_selecionado'] = {
                'dia': dia,
                'mes': mes,
                'ano': ano
            }
            st.rerun()
     
    else:
        # Dia sem dados com design proporcional aos dias com dados
        container_vazio = f"""
        <div style="
            background: {cor_fundo};
            border: 2px solid {cor_borda};
            border-radius: 12px;
            padding: 8px;
            margin: 4px 0;
            min-height: 200px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <div style="
                font-size: 18px; 
                font-weight: bold; 
                color: #6b7280; 
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 4px;
                min-height: 108px;
            ">
                {icone_dia} {dia}
            </div>
            <div style="
                font-size: 0.6rem; 
                color: #9ca3af;
                font-style: italic;
                padding: 12px;
                background: #f8fafc;
                border-radius: 6px;
                border: 1px dashed #cbd5e1;
                margin: 8px 0;
            ">
                Sem movimentação
            </div>
            <div style="
                font-size: 0.6rem;
                padding: 3px 8px;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                background: #f1f5f9;
                color: #64748b;
                margin-top: 8px;
            ">
                📋 {dia}
            </div>
        </div>
        """
        st.markdown(container_vazio, unsafe_allow_html=True)

def mostrar_resumo_semana(dados_semana, semana_info):
    """
    Mostra o resumo financeiro da semana.
    """
    st.markdown("---")
    st.markdown("### 📊 Resumo da Semana")
    
    # Calcular totais da semana
    total_a_pagar = sum(dados_dia.get('a_pagar', 0) for dados_dia in dados_semana.values())
    total_pagas = sum(dados_dia.get('pagas', 0) for dados_dia in dados_semana.values())
    total_contas_a_pagar = sum(dados_dia.get('qtd_a_pagar', 0) for dados_dia in dados_semana.values())
    total_contas_pagas = sum(dados_dia.get('qtd_pagas', 0) for dados_dia in dados_semana.values())
    diferenca_semana = total_a_pagar - total_pagas  # Corrigido: a_pagar - pagas
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Usar HTML personalizado para controle total do tamanho
    with col1:
        valor_a_pagar = formatar_moeda_brasileira(total_a_pagar)
        st.markdown(f"""
        <div style="padding: 8px; border-radius: 6px; background: #fff5f5; border: 1px solid #fecaca;">
            <div style="font-size: 0.55rem; font-weight: normal; color: #dc2626; margin-bottom: 2px;">💸 Total a Pagar</div>
            <div style="font-size: 0.95rem; font-weight: bold; color: #dc2626; margin-bottom: 2px;">{valor_a_pagar}</div>
            <div style="font-size: 0.5rem; color: #9ca3af;">{total_contas_a_pagar} contas</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        valor_pago = formatar_moeda_brasileira(total_pagas)
        st.markdown(f"""
        <div style="padding: 8px; border-radius: 6px; background: #f0fdf4; border: 1px solid #bbf7d0;">
            <div style="font-size: 0.55rem; font-weight: normal; color: #16a34a; margin-bottom: 2px;">✅ Total Pago</div>
            <div style="font-size: 0.95rem; font-weight: bold; color: #16a34a; margin-bottom: 2px;">{valor_pago}</div>
            <div style="font-size: 0.5rem; color: #9ca3af;">{total_contas_pagas} contas</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        valor_diferenca = formatar_moeda_brasileira(diferenca_semana)
        # Lógica correta: positivo = bom (sobrou dinheiro), negativo = ruim (estouro)
        cor_fundo = "#f0fdf4" if diferenca_semana >= 0 else "#fff5f5"
        cor_borda = "#bbf7d0" if diferenca_semana >= 0 else "#fecaca"
        cor_texto = "#16a34a" if diferenca_semana >= 0 else "#dc2626"
        status_texto = "✅ Economia" if diferenca_semana > 0 else ("❌ Estouro" if diferenca_semana < 0 else "⚖️ Equilibrado")
        
        st.markdown(f"""
        <div style="padding: 8px; border-radius: 6px; background: {cor_fundo}; border: 1px solid {cor_borda};">
            <div style="font-size: 0.55rem; font-weight: normal; color: {cor_texto}; margin-bottom: 2px;">📊 Saldo da Semana</div>
            <div style="font-size: 0.95rem; font-weight: bold; color: {cor_texto}; margin-bottom: 2px;">{valor_diferenca}</div>
            <div style="font-size: 0.5rem; color: #9ca3af;">{status_texto}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        dias_com_movimento = len([d for d in dados_semana.values() if d.get('a_pagar', 0) > 0 or d.get('pagas', 0) > 0])
        percentual = round(dias_com_movimento/len(semana_info['dias'])*100)
        
        st.markdown(f"""
        <div style="padding: 8px; border-radius: 6px; background: #f1f5f9; border: 1px solid #cbd5e1;">
            <div style="font-size: 0.55rem; font-weight: normal; color: #475569; margin-bottom: 2px;">📅 Dias com Movimento</div>
            <div style="font-size: 0.95rem; font-weight: bold; color: #475569; margin-bottom: 2px;">{dias_com_movimento}/{len(semana_info['dias'])}</div>
            <div style="font-size: 0.5rem; color: #9ca3af;">{percentual}% da semana</div>
        </div>
        """, unsafe_allow_html=True)

def ajustar_para_dia_util(data_original):
    """
    Ajusta datas de fim de semana para a próxima segunda-feira.
    Sábado (5) e Domingo (6) -> Segunda-feira
    """
    dia_semana = data_original.weekday()  # 0=segunda, 6=domingo
    
    if dia_semana == 5:  # Sábado
        # Mover para segunda (2 dias à frente)
        return data_original + timedelta(days=2)
    elif dia_semana == 6:  # Domingo
        # Mover para segunda (1 dia à frente)
        return data_original + timedelta(days=1)
    else:
        # Dia útil, manter como está
        return data_original

def mostrar_dados_banco(supabase_client: SupabaseClient, analyzer, report_gen):
    """Mostra dados carregados do banco."""
    
    # Tabs para diferentes visões
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🗓️ Calendário", 
        "📊 Dados Atuais", 
        "🏢 Por Empresa", 
        "📋 Exportar", 
        "🤝 Compartilhamento",
        "🔍 Validação Contas Pagas"
    ])
    
    # Buscar dados uma vez para usar em todas as abas
    df_a_pagar = supabase_client.buscar_contas_a_pagar()
    df_pagas = supabase_client.buscar_contas_pagas()
    
    with tab1:
        #st.header("📅 Calendário Financeiro")
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
                df_pagas = supabase_client.buscar_contas_pagas(empresa=empresa_selecionada)
            
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
        # Usar interface já importada
        mostrar_interface_compartilhamento(supabase_client)
    
    with tab6:
        # Interface de validação de contas pagas
        mostrar_interface_validacao_contas_pagas(supabase_client)

if __name__ == "__main__":
    main()
