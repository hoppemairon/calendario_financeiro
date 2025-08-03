"""
Aplicação Principal do Calendário Financeiro com Autenticação.
"""

import streamlit as st
import sys
import os
import pandas as pd
import calendar
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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

def criar_calendario_financeiro(df_a_pagar: pd.DataFrame, df_pagas: pd.DataFrame, mes: int = None, ano: int = None):
    """
    Cria um calendário visual com informações financeiras.
    
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
    
    # Obter informações do calendário
    # Configurar para começar com domingo (padrão brasileiro)
    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(ano, mes)
    nome_mes = calendar.month_name[mes]
    
    # Preparar dados agregados por dia
    dados_calendario = {}
    
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
    
    def buscar_transferencias_do_mes_anterior(df, coluna_data, mes_atual, ano_atual):
        """
        Busca valores de fins de semana do mês anterior que foram transferidos para o mês atual.
        """
        transferencias = {}
        
        if df.empty:
            return transferencias
        
        # Calcular mês anterior
        if mes_atual == 1:
            mes_anterior = 12
            ano_anterior = ano_atual - 1
        else:
            mes_anterior = mes_atual - 1
            ano_anterior = ano_atual
        
        # Buscar dados do mês anterior
        df_mes_anterior = df[
            (df[coluna_data].dt.month == mes_anterior) & 
            (df[coluna_data].dt.year == ano_anterior)
        ]
        
        for _, row in df_mes_anterior.iterrows():
            data_original = row[coluna_data]
            data_ajustada = ajustar_para_dia_util(data_original)
            
            # Se a data ajustada caiu no mês atual, é uma transferência
            if data_ajustada.month == mes_atual and data_ajustada.year == ano_atual:
                dia = data_ajustada.day
                
                if dia not in transferencias:
                    transferencias[dia] = {'a_pagar': 0, 'pagas': 0, 'qtd_a_pagar': 0, 'qtd_pagas': 0}
                
                # Determinar se é conta a pagar ou paga baseado na coluna
                if coluna_data == 'data_vencimento':
                    transferencias[dia]['a_pagar'] += float(row['valor'])
                    transferencias[dia]['qtd_a_pagar'] += 1
                else:  # data_pagamento
                    transferencias[dia]['pagas'] += float(row['valor'])
                    transferencias[dia]['qtd_pagas'] += 1
        
        return transferencias
    
    # Processar contas a pagar
    if not df_a_pagar.empty:
        df_mes_a_pagar = df_a_pagar[
            (df_a_pagar['data_vencimento'].dt.month == mes) & 
            (df_a_pagar['data_vencimento'].dt.year == ano)
        ]
        
        for _, row in df_mes_a_pagar.iterrows():
            data_original = row['data_vencimento']
            data_ajustada = ajustar_para_dia_util(data_original)
            
            # Só processar se a data ajustada ainda estiver no mês atual
            # Se sair do mês, significa que foi transferida para o próximo mês
            if data_ajustada.month == mes and data_ajustada.year == ano:
                dia = data_ajustada.day
                
                if dia not in dados_calendario:
                    dados_calendario[dia] = {'a_pagar': 0, 'pagas': 0, 'qtd_a_pagar': 0, 'qtd_pagas': 0}
                dados_calendario[dia]['a_pagar'] += float(row['valor'])
                dados_calendario[dia]['qtd_a_pagar'] += 1
    
    # Processar contas pagas
    if not df_pagas.empty:
        df_mes_pagas = df_pagas[
            (df_pagas['data_pagamento'].dt.month == mes) & 
            (df_pagas['data_pagamento'].dt.year == ano)
        ]
        
        for _, row in df_mes_pagas.iterrows():
            data_original = row['data_pagamento']
            data_ajustada = ajustar_para_dia_util(data_original)
            
            # Só processar se a data ajustada ainda estiver no mês atual
            # Se sair do mês, significa que foi transferida para o próximo mês
            if data_ajustada.month == mes and data_ajustada.year == ano:
                dia = data_ajustada.day
                
                if dia not in dados_calendario:
                    dados_calendario[dia] = {'a_pagar': 0, 'pagas': 0, 'qtd_a_pagar': 0, 'qtd_pagas': 0}
                dados_calendario[dia]['pagas'] += float(row['valor'])
                dados_calendario[dia]['qtd_pagas'] += 1
    
    # Buscar transferências do mês anterior (fins de semana que viraram para este mês)
    transferencias_a_pagar = buscar_transferencias_do_mes_anterior(df_a_pagar, 'data_vencimento', mes, ano)
    transferencias_pagas = buscar_transferencias_do_mes_anterior(df_pagas, 'data_pagamento', mes, ano)
    
    # Aplicar transferências
    for dia, valores in transferencias_a_pagar.items():
        if dia not in dados_calendario:
            dados_calendario[dia] = {'a_pagar': 0, 'pagas': 0, 'qtd_a_pagar': 0, 'qtd_pagas': 0}
        dados_calendario[dia]['a_pagar'] += valores['a_pagar']
        dados_calendario[dia]['qtd_a_pagar'] += valores['qtd_a_pagar']
    
    for dia, valores in transferencias_pagas.items():
        if dia not in dados_calendario:
            dados_calendario[dia] = {'a_pagar': 0, 'pagas': 0, 'qtd_a_pagar': 0, 'qtd_pagas': 0}
        dados_calendario[dia]['pagas'] += valores['pagas']
        dados_calendario[dia]['qtd_pagas'] += valores['qtd_pagas']
    
    # Criar título
    st.subheader(f"📅 Calendário Financeiro - {nome_mes} {ano}")
    
    # Seletor de mês/ano
    col_mes, col_ano = st.columns(2)
    with col_mes:
        meses = list(calendar.month_name)[1:]  # Remove o primeiro elemento vazio
        mes_selecionado = st.selectbox("Mês", meses, index=mes-1, key="mes_calendario")
        novo_mes = meses.index(mes_selecionado) + 1
    
    with col_ano:
        novo_ano = st.number_input("Ano", min_value=2020, max_value=2030, value=ano, key="ano_calendario")
    
    # Se mudou mês ou ano, usar os novos valores
    if novo_mes != mes or novo_ano != ano:
        mes = novo_mes
        ano = novo_ano
        # Recalcular calendário com novos valores (mantendo domingo como primeiro dia)
        calendar.setfirstweekday(calendar.SUNDAY)
        cal = calendar.monthcalendar(ano, mes)
        nome_mes = calendar.month_name[mes]
        
        # Recalcular dados do mês
        dados_calendario = {}
        
        # Processar contas a pagar
        if not df_a_pagar.empty:
            df_mes_a_pagar = df_a_pagar[
                (df_a_pagar['data_vencimento'].dt.month == mes) & 
                (df_a_pagar['data_vencimento'].dt.year == ano)
            ]
            
            for _, row in df_mes_a_pagar.iterrows():
                data_original = row['data_vencimento']
                data_ajustada = ajustar_para_dia_util(data_original)
                
                # Só processar se a data ajustada ainda estiver no mês atual
                # Se sair do mês, significa que foi transferida para o próximo mês
                if data_ajustada.month == mes and data_ajustada.year == ano:
                    dia = data_ajustada.day
                    
                    if dia not in dados_calendario:
                        dados_calendario[dia] = {'a_pagar': 0, 'pagas': 0, 'qtd_a_pagar': 0, 'qtd_pagas': 0}
                    dados_calendario[dia]['a_pagar'] += float(row['valor'])
                    dados_calendario[dia]['qtd_a_pagar'] += 1
        
        # Processar contas pagas
        if not df_pagas.empty:
            df_mes_pagas = df_pagas[
                (df_pagas['data_pagamento'].dt.month == mes) & 
                (df_pagas['data_pagamento'].dt.year == ano)
            ]
            
            for _, row in df_mes_pagas.iterrows():
                data_original = row['data_pagamento']
                data_ajustada = ajustar_para_dia_util(data_original)
                
                # Só processar se a data ajustada ainda estiver no mês atual
                # Se sair do mês, significa que foi transferida para o próximo mês
                if data_ajustada.month == mes and data_ajustada.year == ano:
                    dia = data_ajustada.day
                    
                    if dia not in dados_calendario:
                        dados_calendario[dia] = {'a_pagar': 0, 'pagas': 0, 'qtd_a_pagar': 0, 'qtd_pagas': 0}
                    dados_calendario[dia]['pagas'] += float(row['valor'])
                    dados_calendario[dia]['qtd_pagas'] += 1
        
        # Buscar transferências do mês anterior (fins de semana que viraram para este mês)
        transferencias_a_pagar = buscar_transferencias_do_mes_anterior(df_a_pagar, 'data_vencimento', mes, ano)
        transferencias_pagas = buscar_transferencias_do_mes_anterior(df_pagas, 'data_pagamento', mes, ano)
        
        # Aplicar transferências
        for dia, valores in transferencias_a_pagar.items():
            if dia not in dados_calendario:
                dados_calendario[dia] = {'a_pagar': 0, 'pagas': 0, 'qtd_a_pagar': 0, 'qtd_pagas': 0}
            dados_calendario[dia]['a_pagar'] += valores['a_pagar']
            dados_calendario[dia]['qtd_a_pagar'] += valores['qtd_a_pagar']
        
        for dia, valores in transferencias_pagas.items():
            if dia not in dados_calendario:
                dados_calendario[dia] = {'a_pagar': 0, 'pagas': 0, 'qtd_a_pagar': 0, 'qtd_pagas': 0}
            dados_calendario[dia]['pagas'] += valores['pagas']
            dados_calendario[dia]['qtd_pagas'] += valores['qtd_pagas']
    
    # Criar grid do calendário
    st.markdown("---")
    st.markdown("### 📋 Legenda:")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("🔴 **A Pagar** - Valores pendentes")
    with col2:
        st.markdown("🟢 **Pago** - Valores pagos")
    with col3:
        st.markdown("🔵 **Diferença** - Pago - A Pagar")
    with col4:
        st.markdown("📅 **Hoje** - Dia atual (azul)")
    
    st.info("💡 **Regra de Negócio**: Valores de sábados e domingos são automaticamente transferidos para a próxima segunda-feira.")
    
    # Criar tabela do calendário
    dias_semana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
    
    # Cabeçalho dos dias da semana
    st.markdown("---")
    cols = st.columns(7)
    for i, dia in enumerate(dias_semana):
        with cols[i]:
            st.markdown(f"""
            <div style="
                text-align: center; 
                font-weight: bold; 
                padding: 10px; 
                background-color: #f8f9fa; 
                border-radius: 5px; 
                margin-bottom: 5px;
                color: #495057;
            ">
                {dia}
            </div>
            """, unsafe_allow_html=True)
    
    # Criar linhas do calendário
    for semana in cal:
        cols = st.columns(7)
        for i, dia in enumerate(semana):
            with cols[i]:
                if dia == 0:  # Dia vazio
                    st.markdown("""
                    <div style="
                        padding: 8px; 
                        margin: 2px;
                        min-height: 100px;
                    ">
                        &nbsp;
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Obter dados do dia
                    dados_dia = dados_calendario.get(dia, {'a_pagar': 0, 'pagas': 0, 'qtd_a_pagar': 0, 'qtd_pagas': 0})
                    
                    # Determinar cor de fundo baseada na atividade
                    cor_fundo = "#f0f0f0"  # Cinza claro padrão
                    
                    # Verificar se é fim de semana
                    data_dia = datetime(ano, mes, dia)
                    eh_fim_de_semana = data_dia.weekday() >= 5  # 5=sábado, 6=domingo
                    
                    if dados_dia['a_pagar'] > 0 and dados_dia['pagas'] == 0:
                        cor_fundo = "#ffebee"  # Vermelho claro (só a pagar)
                    elif dados_dia['pagas'] > 0 and dados_dia['a_pagar'] == 0:
                        cor_fundo = "#e8f5e8"  # Verde claro (só pagas)
                    elif dados_dia['a_pagar'] > 0 and dados_dia['pagas'] > 0:
                        cor_fundo = "#fff3e0"  # Laranja claro (ambos)
                    
                    # Destacar fim de semana com valores zerados (transferidos)
                    if eh_fim_de_semana and dados_dia['a_pagar'] == 0 and dados_dia['pagas'] == 0:
                        cor_fundo = "#f5f5f5"  # Cinza mais escuro para fim de semana
                    
                    # Verificar se é hoje
                    if dia == hoje.day and mes == hoje.month and ano == hoje.year:
                        cor_fundo = "#e3f2fd"  # Azul claro para hoje
                    
                    # Criar conteúdo do dia
                    diferenca = dados_dia['pagas'] - dados_dia['a_pagar']
                    
                    if dados_dia['a_pagar'] > 0 or dados_dia['pagas'] > 0:
                        # Container com dados financeiros
                        
                        # Verificar se é segunda-feira (pode ter recebido transferências)
                        data_dia = datetime(ano, mes, dia)
                        eh_segunda = data_dia.weekday() == 0
                        indicador_transferencia = "📈 " if eh_segunda else ""
                        
                        st.markdown(f"""
                        <div style="
                            background-color: {cor_fundo}; 
                            padding: 8px; 
                            border-radius: 8px; 
                            margin: 2px;
                            min-height: 100px;
                            border: 2px solid #ddd;
                            text-align: center;
                        ">
                            <div style="font-weight: bold; font-size: 16px; margin-bottom: 8px; color: #333;">
                                {indicador_transferencia}{dia}
                            </div>
                            <div style="font-size: 11px; line-height: 1.4;">
                                <div style="color: #d32f2f; margin-bottom: 2px;">A Pagar: R$ {dados_dia['a_pagar']:,.0f}</div>
                                <div style="color: #388e3c; margin-bottom: 2px;">Pago: R$ {dados_dia['pagas']:,.0f}</div>
                                <div style="color: #1976d2; font-weight: bold; font-size: 12px;">
                                    Dif: R$ {diferenca:,.0f}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Dia sem dados
                        st.markdown(f"""
                        <div style="
                            background-color: {cor_fundo}; 
                            padding: 8px; 
                            border-radius: 8px; 
                            margin: 2px;
                            min-height: 100px;
                            border: 1px solid #eee;
                            text-align: center;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        ">
                            <div style="font-weight: bold; font-size: 16px; color: #666;">
                                {dia}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Mostrar resumo do mês
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    total_a_pagar_mes = sum(dados['a_pagar'] for dados in dados_calendario.values())
    total_pagas_mes = sum(dados['pagas'] for dados in dados_calendario.values())
    diferenca_mes = total_pagas_mes - total_a_pagar_mes
    dias_com_atividade = len([d for d in dados_calendario.values() if d['a_pagar'] > 0 or d['pagas'] > 0])
    
    with col1:
        st.metric("Total A Pagar", f"R$ {total_a_pagar_mes:,.2f}")
    with col2:
        st.metric("Total Pago", f"R$ {total_pagas_mes:,.2f}")
    with col3:
        st.metric("Diferença", f"R$ {diferenca_mes:,.2f}", 
                 f"{'✅' if diferenca_mes >= 0 else '❌'}")
    with col4:
        st.metric("Dias com Atividade", f"{dias_com_atividade}")

def mostrar_dados_banco(supabase_client: SupabaseClient, analyzer, report_gen):
    """Mostra dados carregados do banco."""
    
    # Tabs para diferentes visões
    tab1, tab2, tab3, tab4 = st.tabs(["� Calendário", "�📊 Dados Atuais", "🏢 Por Empresa", "📋 Exportar"])
    
    # Buscar dados uma vez para usar em todas as abas
    df_a_pagar = supabase_client.buscar_contas_a_pagar()
    df_pagas = supabase_client.buscar_contas_pagas()
    
    with tab1:
        st.header("📅 Calendário Financeiro")
        criar_calendario_financeiro(df_a_pagar, df_pagas)
    
    with tab2:
        st.header("📊 Dados do Banco")
        
        col1, col2 = st.columns(2)
        
        with col1:            
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

if __name__ == "__main__":
    main()
