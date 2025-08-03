"""
Gerenciador de Autenticação para o Calendário Financeiro.
"""

import streamlit as st
import streamlit_authenticator as stauth
from typing import Optional, Dict, Any
import hashlib
import re
from src.database.supabase_client import SupabaseClient

class AuthManager:
    """Gerenciador de autenticação usando Supabase."""
    
    def __init__(self):
        """Inicializa o gerenciador de autenticação."""
        self.supabase_client = SupabaseClient()
        
        # Inicializar session state
        if 'authenticated' not in st.session_state:
            st.session_state['authenticated'] = False
        if 'user_data' not in st.session_state:
            st.session_state['user_data'] = None
        if 'user_id' not in st.session_state:
            st.session_state['user_id'] = None
    
    def is_authenticated(self) -> bool:
        """Verifica se o usuário está autenticado."""
        return st.session_state.get('authenticated', False)
    
    def get_user_data(self) -> Optional[Dict[str, Any]]:
        """Retorna os dados do usuário atual."""
        return st.session_state.get('user_data')
    
    def get_user_id(self) -> Optional[str]:
        """Retorna o ID do usuário atual."""
        return st.session_state.get('user_id')
    
    def validate_email(self, email: str) -> bool:
        """Valida formato do email."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password: str) -> Dict[str, Any]:
        """Valida a senha."""
        errors = []
        
        if len(password) < 6:
            errors.append("Senha deve ter pelo menos 6 caracteres")
        
        if not re.search(r'[A-Za-z]', password):
            errors.append("Senha deve conter pelo menos uma letra")
        
        if not re.search(r'[0-9]', password):
            errors.append("Senha deve conter pelo menos um número")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def login_form(self) -> bool:
        """Exibe formulário de login."""
        with st.form("login_form"):
            st.subheader("🔐 Login")
            
            email = st.text_input("Email", placeholder="seu.email@exemplo.com")
            password = st.text_input("Senha", type="password", placeholder="Sua senha")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                login_button = st.form_submit_button("Entrar", type="primary", use_container_width=True)
            
            with col2:
                register_button = st.form_submit_button("Cadastrar", use_container_width=True)
            
            # Botão para confirmar email manualmente
            st.markdown("---")
            col3, col4 = st.columns([1, 1])
            
            with col3:
                confirm_email_button = st.form_submit_button("📧 Confirmar Email", use_container_width=True)
            
            with col4:
                resend_button = st.form_submit_button("🔄 Reenviar Email", use_container_width=True)
            
            if login_button:
                if not email or not password:
                    st.error("Por favor, preencha todos os campos.")
                    return False
                
                if not self.validate_email(email):
                    st.error("Email inválido.")
                    return False
                
                with st.spinner("Fazendo login..."):
                    result = self.supabase_client.sign_in(email, password)
                    
                    if result["success"]:
                        # Configurar session state
                        st.session_state['authenticated'] = True
                        st.session_state['user_data'] = result["user_data"]
                        st.session_state['user_id'] = result["user"].id
                        
                        # Configurar cliente Supabase
                        self.supabase_client.set_user_id(result["user"].id)
                        
                        st.success(result["message"])
                        st.rerun()
                        return True
                    else:
                        error_msg = result.get("error", "")
                        if "Email not confirmed" in error_msg:
                            st.error("❌ Email não confirmado!")
                            st.info("📧 Verifique seu email e clique no link de confirmação.")
                            st.info("💡 Ou use o botão 'Confirmar Email' abaixo com o token do email.")
                        else:
                            st.error(result["message"])
                        return False
            
            if register_button:
                if not email or not password:
                    st.error("Por favor, preencha todos os campos.")
                    return False
                
                if not self.validate_email(email):
                    st.error("Email inválido.")
                    return False
                
                password_validation = self.validate_password(password)
                if not password_validation["valid"]:
                    for error in password_validation["errors"]:
                        st.error(error)
                    return False
                
                # Mostrar formulário de cadastro adicional
                st.session_state['register_data'] = {
                    'email': email,
                    'password': password
                }
                st.session_state['show_register_form'] = True
                st.rerun()
            
            if confirm_email_button:
                if not email:
                    st.error("Digite seu email para confirmar.")
                    return False
                
                # Mostrar campo para token
                st.session_state['show_confirm_email'] = True
                st.session_state['confirm_email'] = email
                st.rerun()
            
            if resend_button:
                if not email:
                    st.error("Digite seu email para reenviar confirmação.")
                    return False
                
                with st.spinner("Reenviando email..."):
                    try:
                        # Tentar reenviar email de confirmação
                        result = self.supabase_client.supabase.auth.resend({
                            "type": "signup",
                            "email": email,
                            "options": {
                                "email_redirect_to": "http://localhost:8503"
                            }
                        })
                        st.success("📧 Email de confirmação reenviado!")
                        st.info("Verifique sua caixa de entrada e spam.")
                    except Exception as e:
                        st.error(f"❌ Erro ao reenviar: {str(e)}")
        
        return False
    
    def confirm_email_form(self):
        """Exibe formulário para confirmação manual de email."""
        email = st.session_state.get('confirm_email', '')
        
        with st.form("confirm_email_form"):
            st.subheader("📧 Confirmar Email")
            
            st.text_input("Email", value=email, disabled=True)
            
            st.info("""
            💡 **Como obter o token:**
            1. Abra o email de confirmação que você recebeu
            2. No link, copie apenas a parte do **token** (após `token=` e antes do `&`)
            3. Cole o token no campo abaixo
            
            Exemplo: se o link for:
            `...token=abc123def456&type=signup...`
            
            Cole apenas: `abc123def456`
            """)
            
            token = st.text_input("Token de Confirmação", placeholder="Cole aqui o token do email")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                confirm_button = st.form_submit_button("✅ Confirmar", type="primary", use_container_width=True)
            
            with col2:
                cancel_button = st.form_submit_button("❌ Cancelar", use_container_width=True)
            
            if confirm_button:
                if not token:
                    st.error("Por favor, cole o token do email.")
                    return
                
                with st.spinner("Confirmando email..."):
                    try:
                        # Confirmar usando o token
                        result = self.supabase_client.supabase.auth.verify_otp({
                            "token": token.strip(),
                            "type": "signup"
                        })
                        
                        if result.user:
                            st.success("🎉 Email confirmado com sucesso!")
                            st.success("✅ Agora você pode fazer login normalmente.")
                            st.balloons()
                            
                            # Limpar dados
                            del st.session_state['show_confirm_email']
                            del st.session_state['confirm_email']
                            st.rerun()
                        else:
                            st.error("❌ Token inválido ou expirado.")
                            st.info("💡 Verifique se copiou o token correto ou solicite um novo email.")
                            
                    except Exception as e:
                        error_msg = str(e)
                        if "expired" in error_msg.lower():
                            st.error("⏰ Token expirado!")
                            st.info("💡 Solicite um novo email de confirmação.")
                        elif "invalid" in error_msg.lower():
                            st.error("❌ Token inválido!")
                            st.info("💡 Verifique se copiou corretamente.")
                        else:
                            st.error(f"❌ Erro: {error_msg}")
            
            if cancel_button:
                del st.session_state['show_confirm_email']
                del st.session_state['confirm_email']
                st.rerun()

    def register_form(self):
        """Exibe formulário completo de cadastro."""
        register_data = st.session_state.get('register_data', {})
        
        with st.form("register_complete_form"):
            st.subheader("📝 Completar Cadastro")
            
            st.text_input("Email", value=register_data.get('email', ''), disabled=True)
            
            nome = st.text_input("Nome Completo", placeholder="Seu nome completo")
            empresa_padrao = st.text_input("Empresa Principal (opcional)", placeholder="Nome da sua empresa principal")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                complete_register = st.form_submit_button("Completar Cadastro", type="primary", use_container_width=True)
            
            with col2:
                cancel_register = st.form_submit_button("Cancelar", use_container_width=True)
            
            if complete_register:
                if not nome:
                    st.error("Nome é obrigatório.")
                    return
                
                with st.spinner("Criando conta..."):
                    result = self.supabase_client.sign_up(
                        email=register_data['email'],
                        password=register_data['password'],
                        nome=nome,
                        empresa_padrao=empresa_padrao
                    )
                    
                    if result["success"]:
                        st.success("🎉 " + result["message"])
                        st.info("📧 Verifique seu email para confirmar a conta antes de fazer login.")
                        st.balloons()
                        
                        # Limpar dados de registro
                        del st.session_state['register_data']
                        del st.session_state['show_register_form']
                        st.rerun()
                    else:
                        # Verificar tipo de erro
                        error_msg = result.get("error", "")
                        
                        if "Email not confirmed" in error_msg:
                            st.success("✅ Conta criada com sucesso!")
                            st.info("📧 Verifique seu email e clique no link de confirmação antes de fazer login.")
                            
                            # Limpar dados de registro
                            del st.session_state['register_data']
                            del st.session_state['show_register_form']
                            st.rerun()
                        elif "User already registered" in error_msg:
                            st.warning("⚠️ Este email já está cadastrado.")
                            st.info("💡 Tente fazer login ou use outro email.")
                        elif "security purposes" in error_msg:
                            st.warning("⏰ Aguarde alguns segundos antes de tentar novamente.")
                            st.info("🔒 Medida de segurança do sistema.")
                        else:
                            st.error("❌ " + result["message"])
            
            if cancel_register:
                # Limpar dados de registro
                del st.session_state['register_data']
                del st.session_state['show_register_form']
                st.rerun()
    
    def logout(self):
        """Faz logout do usuário."""
        result = self.supabase_client.sign_out()
        
        # Limpar session state
        st.session_state['authenticated'] = False
        st.session_state['user_data'] = None
        st.session_state['user_id'] = None
        
        # Limpar outros dados da sessão
        keys_to_clear = [
            'df_a_pagar', 'df_pagas', 'correspondencias', 
            'resumo', 'resumo_empresa', 'data_processamento'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        st.success(result["message"])
        st.rerun()
    
    def show_user_info(self):
        """Exibe informações do usuário logado."""
        user_data = self.get_user_data()
        
        if user_data:
            with st.sidebar:
                st.success(f"Logado como: **{user_data['nome']}**")
                st.caption(f"📧 {user_data['email']}")
                
                if user_data.get('empresa_padrao'):
                    st.caption(f"🏢 {user_data['empresa_padrao']}")
                
                if st.button("🚪 Sair", use_container_width=True):
                    self.logout()
    
    def require_auth(self, show_form: bool = True) -> bool:
        """
        Requer autenticação para acessar a página.
        
        Args:
            show_form: Se deve mostrar o formulário de login/cadastro
            
        Returns:
            bool: True se autenticado, False caso contrário
        """
        if self.is_authenticated():
            # Configurar cliente Supabase com o usuário atual
            user_id = self.get_user_id()
            if user_id:
                self.supabase_client.set_user_id(user_id)
            
            # Mostrar informações do usuário
            self.show_user_info()
            return True
        
        if show_form:
            # Verificar se deve mostrar formulário de confirmação de email
            if st.session_state.get('show_confirm_email', False):
                self.confirm_email_form()
            # Verificar se deve mostrar formulário de cadastro completo
            elif st.session_state.get('show_register_form', False):
                self.register_form()
            else:
                self.login_form()
        
        return False
    
    def get_supabase_client(self) -> SupabaseClient:
        """Retorna o cliente Supabase configurado."""
        return self.supabase_client
