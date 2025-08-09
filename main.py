"""
Aplicação Principal do Calendário Financeiro.
"""

import streamlit as st

# Configurar página
st.set_page_config(
    page_title="Calendário Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Informar que deve usar a versão com autenticação
st.title("🔒 Calendário Financeiro - Sistema Seguro")
st.info("⚠️ Este sistema agora requer autenticação para maior segurança dos dados.")
st.write("Para acessar o sistema completo, execute:")
st.code("streamlit run main_with_auth.py")
st.write("Ou use a task 'Executar Calendário Financeiro' no VS Code.")

st.subheader("📋 Funcionalidades Implementadas:")
st.write("✅ Sistema de autenticação com Supabase")
st.write("✅ Upload e conversão de arquivos Excel")
st.write("✅ Prevenção automática de duplicatas")
st.write("✅ Validação de dados com fornecedor")
st.write("✅ Calendário interativo de pagamentos")
st.write("✅ Relatórios e análises financeiras")
