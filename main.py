"""
Aplicação principal do Calendário Financeiro.
"""

import streamlit as st
import sys
import os

# Configurar página ANTES de qualquer import
st.set_page_config(
    page_title="Calendário Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Adicionar src ao path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Importar e executar a aplicação Streamlit
if __name__ == "__main__":
    # Importar o módulo da aplicação
    import src.calendar_app
