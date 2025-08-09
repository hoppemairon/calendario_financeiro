"""
Continuação das funções de calendário - parte 2.

Funções auxiliares para visualização de dias e resumos.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.utils import formatar_moeda_brasileira


def ajustar_para_dia_util(data_original):
    """
    Ajusta datas de fim de semana para a próxima segunda-feira.
    Sábado (5) e Domingo (6) -> Segunda-feira
    
    Args:
        data_original: Data original a ser ajustada
    
    Returns:
        datetime: Data ajustada para dia útil
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
                        'conta_corrente': row.get('conta_corrente', 'N/A'),
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
                'conta_corrente': 'Conta Corrente',
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
    
    # Relatório de Fornecedores/Contas Correntes
    st.markdown("### 🏢 Relatório por Fornecedor/Conta Corrente")
    
    # Consolidar dados por fornecedor/conta corrente
    relatorio_fornecedores = {}
    
    # Processar contas a pagar
    for conta in contas_a_pagar_dia:
        fornecedor = conta['fornecedor']
        if fornecedor not in relatorio_fornecedores:
            relatorio_fornecedores[fornecedor] = {
                'identificador': fornecedor,
                'tipo': 'Fornecedor',
                'total_a_pagar': 0,
                'total_pago': 0,
                'qtd_a_pagar': 0,
                'qtd_pagas': 0
            }
        relatorio_fornecedores[fornecedor]['total_a_pagar'] += conta['valor']
        relatorio_fornecedores[fornecedor]['qtd_a_pagar'] += 1
    
    # Processar contas pagas - usar conta_corrente como identificador
    for conta in contas_pagas_dia:
        conta_corrente = conta['conta_corrente']
        if conta_corrente not in relatorio_fornecedores:
            relatorio_fornecedores[conta_corrente] = {
                'identificador': conta_corrente,
                'tipo': 'Conta Corrente',
                'total_a_pagar': 0,
                'total_pago': 0,
                'qtd_a_pagar': 0,
                'qtd_pagas': 0
            }
        relatorio_fornecedores[conta_corrente]['total_pago'] += conta['valor']
        relatorio_fornecedores[conta_corrente]['qtd_pagas'] += 1
    
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
            df_export = df_fornecedores[['identificador', 'total_a_pagar', 'total_pago', 'qtd_a_pagar', 'qtd_pagas', 'diferenca']].copy()
            
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
            from .audit_logic import executar_auditoria_dia  # Import local para evitar circular
            executar_auditoria_dia(arquivo_auditoria, data_filtro, contas_a_pagar_dia, contas_pagas_dia)
