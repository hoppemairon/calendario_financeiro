"""
Funcionalidades de compartilhamento de dados entre usuários.
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any
import streamlit as st


class CompartilhamentoMixin:
    """Mixin para adicionar funcionalidades de compartilhamento ao SupabaseClient."""
    
    def conceder_acesso_usuario(self, email_usuario: str, nivel_acesso: str = 'viewer') -> Dict[str, Any]:
        """Concede acesso aos dados do usuário atual para outro usuário."""
        if not self.user_id:
            return {"success": False, "error": "Usuário não autenticado"}
            
        try:
            # 1. Buscar ID do usuário pelo email
            user_response = self.supabase.table("usuarios").select("id, nome").eq("email", email_usuario).execute()
            
            if not user_response.data:
                return {"success": False, "error": "Usuário não encontrado"}
            
            target_user_id = user_response.data[0]['id']
            target_user_name = user_response.data[0]['nome']
            
            # 2. Verificar se não está tentando dar acesso para si mesmo
            if target_user_id == self.user_id:
                return {"success": False, "error": "Você não pode conceder acesso para si mesmo"}
            
            # 3. Criar/atualizar permissão
            permissao_data = {
                "usuario_proprietario": self.user_id,
                "usuario_convidado": target_user_id,
                "nivel_acesso": nivel_acesso,
                "ativo": True,
                "data_concessao": datetime.now().isoformat()
            }
            
            # Usar upsert para atualizar se já existir
            response = self.supabase.table("permissoes_usuario").upsert(permissao_data).execute()
            
            return {"success": True, "message": f"Acesso '{nivel_acesso}' concedido para {target_user_name} ({email_usuario})"}
        
        except Exception as e:
            return {"success": False, "error": f"Erro ao conceder acesso: {str(e)}"}

    def revogar_acesso_usuario(self, email_usuario: str) -> Dict[str, Any]:
        """Revoga acesso de um usuário aos meus dados."""
        if not self.user_id:
            return {"success": False, "error": "Usuário não autenticado"}
            
        try:
            # 1. Buscar ID do usuário pelo email
            user_response = self.supabase.table("usuarios").select("id, nome").eq("email", email_usuario).execute()
            
            if not user_response.data:
                return {"success": False, "error": "Usuário não encontrado"}
            
            target_user_id = user_response.data[0]['id']
            target_user_name = user_response.data[0]['nome']
            
            # 2. Desativar permissão
            response = self.supabase.table("permissoes_usuario").update({
                "ativo": False
            }).eq("usuario_proprietario", self.user_id).eq("usuario_convidado", target_user_id).execute()
            
            return {"success": True, "message": f"Acesso revogado para {target_user_name} ({email_usuario})"}
        
        except Exception as e:
            return {"success": False, "error": f"Erro ao revogar acesso: {str(e)}"}

    def listar_usuarios_com_acesso(self) -> pd.DataFrame:
        """Lista usuários que têm acesso aos meus dados."""
        if not self.user_id:
            return pd.DataFrame()
            
        try:
            response = self.supabase.table("permissoes_usuario").select(
                "usuario_convidado, nivel_acesso, data_concessao, usuarios!usuario_convidado(nome, email)"
            ).eq("usuario_proprietario", self.user_id).eq("ativo", True).execute()
            
            if response.data:
                dados = []
                for item in response.data:
                    if item.get('usuarios'):  # Verificar se existe a relação
                        dados.append({
                            'nome': item['usuarios']['nome'],
                            'email': item['usuarios']['email'], 
                            'nivel_acesso': item['nivel_acesso'],
                            'data_concessao': item['data_concessao']
                        })
                
                return pd.DataFrame(dados)
            
            return pd.DataFrame()
        
        except Exception as e:
            print(f"Erro ao listar usuários: {e}")
            return pd.DataFrame()

    def listar_meus_acessos(self) -> pd.DataFrame:
        """Lista usuários cujos dados eu tenho acesso."""
        if not self.user_id:
            return pd.DataFrame()
            
        try:
            response = self.supabase.table("permissoes_usuario").select(
                "usuario_proprietario, nivel_acesso, data_concessao, usuarios!usuario_proprietario(nome, email)"
            ).eq("usuario_convidado", self.user_id).eq("ativo", True).execute()
            
            if response.data:
                dados = []
                for item in response.data:
                    if item.get('usuarios'):  # Verificar se existe a relação
                        dados.append({
                            'nome': item['usuarios']['nome'],
                            'email': item['usuarios']['email'], 
                            'nivel_acesso': item['nivel_acesso'],
                            'data_concessao': item['data_concessao'],
                            'usuario_id': item['usuario_proprietario']
                        })
                
                return pd.DataFrame(dados)
            
            return pd.DataFrame()
        
        except Exception as e:
            print(f"Erro ao listar meus acessos: {e}")
            return pd.DataFrame()

    def alternar_visualizacao_usuario(self, email_usuario: str) -> Dict[str, Any]:
        """Alterna para visualizar dados de outro usuário (se tiver permissão)."""
        if not self.user_id:
            return {"success": False, "error": "Usuário não autenticado"}
            
        try:
            # 1. Buscar ID do usuário
            user_response = self.supabase.table("usuarios").select("id, nome").eq("email", email_usuario).execute()
            
            if not user_response.data:
                return {"success": False, "error": "Usuário não encontrado"}
            
            target_user_id = user_response.data[0]['id']
            target_user_name = user_response.data[0]['nome']
            
            # 2. Verificar permissão
            permissao = self.supabase.table("permissoes_usuario").select("*").eq(
                "usuario_proprietario", target_user_id
            ).eq("usuario_convidado", self.user_id).eq("ativo", True).execute()
            
            if not permissao.data:
                return {"success": False, "error": "Você não tem permissão para acessar os dados deste usuário"}
            
            # 3. Salvar estado atual e alternar
            if 'visualizacao_original' not in st.session_state:
                st.session_state['visualizacao_original'] = self.user_id
            
            # Alternar user_id temporariamente
            self.set_user_id(target_user_id)
            st.session_state['visualizando_usuario'] = target_user_name
            st.session_state['visualizando_email'] = email_usuario
            
            return {"success": True, "message": f"Agora visualizando dados de {target_user_name}"}
        
        except Exception as e:
            return {"success": False, "error": f"Erro ao alternar visualização: {str(e)}"}

    def voltar_visualizacao_original(self) -> Dict[str, Any]:
        """Volta para o usuário original."""
        try:
            if 'visualizacao_original' in st.session_state:
                self.set_user_id(st.session_state['visualizacao_original'])
                
                # Limpar estado
                del st.session_state['visualizacao_original']
                if 'visualizando_usuario' in st.session_state:
                    del st.session_state['visualizando_usuario']
                if 'visualizando_email' in st.session_state:
                    del st.session_state['visualizando_email']
                
                return {"success": True, "message": "Voltou para seus próprios dados"}
            
            return {"success": False, "error": "Não estava visualizando outro usuário"}
        
        except Exception as e:
            return {"success": False, "error": f"Erro ao voltar visualização: {str(e)}"}
