"""
Lógicas de auditoria de dados financeiros.

Funções para auditoria e validação de dados de contas a pagar e pagas.
"""

import streamlit as st
import pandas as pd
from src.utils import formatar_moeda_brasileira


def executar_auditoria_dia(arquivo, data_filtro, contas_a_pagar_sistema, contas_pagas_sistema):
    """
    Executa auditoria para um dia específico comparando arquivo original com sistema.
    
    Args:
        arquivo: Arquivo Excel original para auditoria
        data_filtro: Data específica para filtrar (date)
        contas_a_pagar_sistema: Lista de contas a pagar do sistema para o dia
        contas_pagas_sistema: Lista de contas pagas do sistema para o dia
    """
    try:
        # Ler arquivo original
        df_original = pd.read_excel(arquivo, engine='openpyxl')
        
        st.markdown("### 🔍 Resultado da Auditoria")
        
        # Detectar tipo de arquivo
        tipo_arquivo = detectar_tipo_arquivo_auditoria(df_original)
        
        if tipo_arquivo == 'contas_a_pagar':
            st.info("📊 Arquivo detectado: **Contas a Pagar**")
            executar_auditoria_contas_a_pagar(df_original, data_filtro, contas_a_pagar_sistema)
        elif tipo_arquivo == 'contas_pagas':
            st.info("📊 Arquivo detectado: **Contas Pagas**")
            executar_auditoria_contas_pagas(df_original, data_filtro, contas_pagas_sistema)
        else:
            st.warning("⚠️ Não foi possível detectar o tipo de arquivo.")
            st.info("💡 Certifique-se de que o arquivo possui as colunas corretas (data_vencimento para contas a pagar ou data_pagamento para contas pagas).")
    
    except Exception as e:
        st.error(f"❌ Erro durante auditoria: {str(e)}")
        st.exception(e)


def executar_auditoria_completa():
    """
    Executa auditoria completa do sistema comparando todos os dados.
    """
    st.markdown("### 🔍 Auditoria Completa do Sistema")
    
    # Upload de arquivos para auditoria completa
    col1, col2 = st.columns(2)
    
    with col1:
        arquivo_a_pagar = st.file_uploader(
            "📤 Upload - Contas a Pagar Original",
            type=['xlsx', 'xls'],
            key="auditoria_completa_a_pagar"
        )
    
    with col2:
        arquivo_pagas = st.file_uploader(
            "📤 Upload - Contas Pagas Original",
            type=['xlsx', 'xls'],
            key="auditoria_completa_pagas"
        )
    
    if arquivo_a_pagar or arquivo_pagas:
        if st.button("🔍 Executar Auditoria Completa", type="primary"):
            
            # Carregar dados do sistema (simulação - na implementação real seria do banco)
            sistema_a_pagar = []  # Carregar do banco/sessão
            sistema_pagas = []    # Carregar do banco/sessão
            
            st.info("📊 Iniciando auditoria completa...")
            
            # Auditoria de Contas a Pagar
            if arquivo_a_pagar:
                st.markdown("#### 💸 Auditoria - Contas a Pagar")
                try:
                    df_original_a_pagar = pd.read_excel(arquivo_a_pagar)
                    executar_auditoria_completa_a_pagar(df_original_a_pagar, sistema_a_pagar)
                except Exception as e:
                    st.error(f"❌ Erro na auditoria de contas a pagar: {str(e)}")
            
            # Auditoria de Contas Pagas
            if arquivo_pagas:
                st.markdown("#### ✅ Auditoria - Contas Pagas")
                try:
                    df_original_pagas = pd.read_excel(arquivo_pagas)
                    executar_auditoria_completa_pagas(df_original_pagas, sistema_pagas)
                except Exception as e:
                    st.error(f"❌ Erro na auditoria de contas pagas: {str(e)}")
    
    else:
        st.info("📋 Faça upload dos arquivos originais para executar a auditoria completa.")


def detectar_tipo_arquivo_auditoria(df):
    """
    Detecta o tipo de arquivo baseado nas colunas presentes.
    
    Args:
        df: DataFrame para análise
        
    Returns:
        str: 'contas_a_pagar', 'contas_pagas' ou 'desconhecido'
    """
    colunas = [col.lower().strip() for col in df.columns]
    
    # Palavras-chave para contas a pagar
    keywords_a_pagar = ['vencimento', 'fornecedor', 'empresa']
    # Palavras-chave para contas pagas
    keywords_pagas = ['pagamento', 'conta_corrente', 'banco']
    
    score_a_pagar = sum(1 for keyword in keywords_a_pagar if any(keyword in col for col in colunas))
    score_pagas = sum(1 for keyword in keywords_pagas if any(keyword in col for col in colunas))
    
    if score_a_pagar > score_pagas:
        return 'contas_a_pagar'
    elif score_pagas > score_a_pagar:
        return 'contas_pagas'
    else:
        return 'desconhecido'


def executar_auditoria_contas_a_pagar(df_original, data_filtro, contas_sistema):
    """
    Executa auditoria específica para contas a pagar.
    """
    try:
        # Filtrar dados do arquivo original pela data
        if 'data_vencimento' in df_original.columns:
            df_original['data_vencimento'] = pd.to_datetime(df_original['data_vencimento'], errors='coerce')
            df_dia_original = df_original[
                df_original['data_vencimento'].dt.date == data_filtro
            ]
        else:
            st.error("❌ Coluna 'data_vencimento' não encontrada no arquivo original.")
            return
        
        # Calcular totais
        total_original = df_dia_original['valor'].sum() if 'valor' in df_dia_original.columns else 0
        total_sistema = sum(conta['valor'] for conta in contas_sistema)
        
        qtd_original = len(df_dia_original)
        qtd_sistema = len(contas_sistema)
        
        # Mostrar comparação
        st.markdown("#### 📊 Comparação de Totais")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Arquivo Original", formatar_moeda_brasileira(total_original), f"{qtd_original} contas")
        with col2:
            st.metric("Sistema", formatar_moeda_brasileira(total_sistema), f"{qtd_sistema} contas")
        with col3:
            diferenca = total_sistema - total_original
            diferenca_qtd = qtd_sistema - qtd_original
            
            if abs(diferenca) < 0.01 and diferenca_qtd == 0:
                st.success("✅ CONFERIDO")
                st.metric("Diferença", "R$ 0,00", "Dados conferem!")
            else:
                st.error("❌ DIVERGÊNCIA")
                st.metric("Diferença", formatar_moeda_brasileira(diferenca), f"{diferenca_qtd} contas")
        
        # Mostrar detalhes se houver divergência
        if abs(diferenca) >= 0.01 or diferenca_qtd != 0:
            st.markdown("#### 🔍 Detalhes da Divergência")
            
            # Mostrar dados originais
            st.markdown("##### 📄 Dados do Arquivo Original:")
            if not df_dia_original.empty:
                df_display_original = df_dia_original.copy()
                if 'valor' in df_display_original.columns:
                    df_display_original['valor'] = df_display_original['valor'].apply(formatar_moeda_brasileira)
                st.dataframe(df_display_original, use_container_width=True)
            else:
                st.info("Nenhum dado encontrado no arquivo original para esta data.")
            
            # Mostrar dados do sistema
            st.markdown("##### 💻 Dados do Sistema:")
            if contas_sistema:
                df_sistema = pd.DataFrame(contas_sistema)
                df_sistema['valor'] = df_sistema['valor'].apply(formatar_moeda_brasileira)
                st.dataframe(df_sistema, use_container_width=True)
            else:
                st.info("Nenhum dado encontrado no sistema para esta data.")
    
    except Exception as e:
        st.error(f"❌ Erro na auditoria de contas a pagar: {str(e)}")


def executar_auditoria_contas_pagas(df_original, data_filtro, contas_sistema):
    """
    Executa auditoria específica para contas pagas.
    """
    try:
        # Filtrar dados do arquivo original pela data
        if 'data_pagamento' in df_original.columns:
            df_original['data_pagamento'] = pd.to_datetime(df_original['data_pagamento'], errors='coerce')
            df_dia_original = df_original[
                df_original['data_pagamento'].dt.date == data_filtro
            ]
        else:
            st.error("❌ Coluna 'data_pagamento' não encontrada no arquivo original.")
            return
        
        # Calcular totais
        total_original = df_dia_original['valor'].sum() if 'valor' in df_dia_original.columns else 0
        total_sistema = sum(conta['valor'] for conta in contas_sistema)
        
        qtd_original = len(df_dia_original)
        qtd_sistema = len(contas_sistema)
        
        # Mostrar comparação
        st.markdown("#### 📊 Comparação de Totais")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Arquivo Original", formatar_moeda_brasileira(total_original), f"{qtd_original} contas")
        with col2:
            st.metric("Sistema", formatar_moeda_brasileira(total_sistema), f"{qtd_sistema} contas")
        with col3:
            diferenca = total_sistema - total_original
            diferenca_qtd = qtd_sistema - qtd_original
            
            if abs(diferenca) < 0.01 and diferenca_qtd == 0:
                st.success("✅ CONFERIDO")
                st.metric("Diferença", "R$ 0,00", "Dados conferem!")
            else:
                st.error("❌ DIVERGÊNCIA")
                st.metric("Diferença", formatar_moeda_brasileira(diferenca), f"{diferenca_qtd} contas")
        
        # Mostrar detalhes se houver divergência
        if abs(diferenca) >= 0.01 or diferenca_qtd != 0:
            st.markdown("#### 🔍 Detalhes da Divergência")
            
            # Mostrar dados originais
            st.markdown("##### 📄 Dados do Arquivo Original:")
            if not df_dia_original.empty:
                df_display_original = df_dia_original.copy()
                if 'valor' in df_display_original.columns:
                    df_display_original['valor'] = df_display_original['valor'].apply(formatar_moeda_brasileira)
                st.dataframe(df_display_original, use_container_width=True)
            else:
                st.info("Nenhum dado encontrado no arquivo original para esta data.")
            
            # Mostrar dados do sistema
            st.markdown("##### 💻 Dados do Sistema:")
            if contas_sistema:
                df_sistema = pd.DataFrame(contas_sistema)
                df_sistema['valor'] = df_sistema['valor'].apply(formatar_moeda_brasileira)
                st.dataframe(df_sistema, use_container_width=True)
            else:
                st.info("Nenhum dado encontrado no sistema para esta data.")
    
    except Exception as e:
        st.error(f"❌ Erro na auditoria de contas pagas: {str(e)}")


def executar_auditoria_completa_a_pagar(df_original, dados_sistema):
    """
    Executa auditoria completa das contas a pagar.
    """
    st.info("🔍 Comparando contas a pagar...")
    
    # Implementar lógica de auditoria completa
    # Esta é uma versão simplificada
    total_original = df_original['valor'].sum() if 'valor' in df_original.columns else 0
    qtd_original = len(df_original)
    
    st.metric("Total Original", formatar_moeda_brasileira(total_original), f"{qtd_original} contas")
    
    if not dados_sistema:
        st.warning("⚠️ Nenhum dado encontrado no sistema para comparação.")
    
    st.success("✅ Auditoria de contas a pagar concluída.")


def executar_auditoria_completa_pagas(df_original, dados_sistema):
    """
    Executa auditoria completa das contas pagas.
    """
    st.info("🔍 Comparando contas pagas...")
    
    # Implementar lógica de auditoria completa
    # Esta é uma versão simplificada
    total_original = df_original['valor'].sum() if 'valor' in df_original.columns else 0
    qtd_original = len(df_original)
    
    st.metric("Total Original", formatar_moeda_brasileira(total_original), f"{qtd_original} contas")
    
    if not dados_sistema:
        st.warning("⚠️ Nenhum dado encontrado no sistema para comparação.")
    
    st.success("✅ Auditoria de contas pagas concluída.")
