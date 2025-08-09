"""
Helpers de interface do usuário para o Calendário Financeiro.

Contém CSS personalizado e funções auxiliares para a interface.
"""

import streamlit as st

def aplicar_css_global():
    """
    Aplica o CSS global para reduzir tamanho das métricas e estilizar componentes.
    """
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

def aplicar_css_calendario():
    """
    Aplica CSS específico para os botões do calendário.
    """
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
