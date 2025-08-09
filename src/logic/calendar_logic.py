"""
Lógica do calendário financeiro para o Calendário Financeiro.

Contém funções para criação do calendário, cálculos de datas e visualizações.
"""

import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
from src.utils import obter_mes_nome_brasileiro
from .ui_helpers import aplicar_css_calendario
from .calendar_helpers import (
    mostrar_dia_semana,
    mostrar_dia_mensal,
    mostrar_resumo_semana,
    mostrar_resumo_mes,
    mostrar_detalhes_dia,
    ajustar_para_dia_util
)

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
    # Aplicar CSS específico para o calendário
    aplicar_css_calendario()
    
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

# Continuarei no próximo arquivo devido ao limite de caracteres...
