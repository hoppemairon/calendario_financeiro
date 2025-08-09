"""
Cliente Supabase para o Calendário Financeiro.
"""

import os
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import uuid
import streamlit as st

# Carregar variáveis de ambiente
load_dotenv()

try:
    from .compartilhamento import CompartilhamentoMixin
except ImportError:
    # Fallback se o módulo não existir
    class CompartilhamentoMixin:
        pass

class SupabaseClient(CompartilhamentoMixin):
    """Cliente para interação com o banco Supabase."""
    
    def __init__(self):
        """Inicializa o cliente Supabase."""
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL e SUPABASE_KEY devem estar configurados no arquivo .env")
        
        self.supabase: Client = create_client(self.url, self.key)
        self.user_id: Optional[str] = None
    
    def set_user_id(self, user_id: str):
        """Define o ID do usuário atual para as operações."""
        self.user_id = user_id
    
    def _garantir_usuario_existe(self):
        """Garante que o usuário existe na tabela usuarios."""
        if not self.user_id:
            return
        
        try:
            # Verificar se usuário existe
            response = self.supabase.table("usuarios").select("id").eq("id", self.user_id).execute()
            
            if not response.data:
                # Usuário não existe, vamos criá-lo
                print(f"Usuário {self.user_id} não encontrado na tabela, criando...")
                
                # Buscar dados do Auth
                try:
                    user = self.supabase.auth.get_user()
                    if user and user.user:
                        user_data = {
                            "id": self.user_id,
                            "email": user.user.email,
                            "nome": user.user.user_metadata.get("nome", user.user.email.split("@")[0]),
                            "empresa_padrao": user.user.user_metadata.get("empresa_padrao", "")
                        }
                        
                        # Inserir usuário na tabela
                        self.supabase.table("usuarios").insert(user_data).execute()
                        print(f"Usuário {self.user_id} criado na tabela usuarios")
                        
                except Exception as auth_error:
                    print(f"Erro ao buscar dados do Auth: {auth_error}")
                    # Criar com dados mínimos
                    user_data = {
                        "id": self.user_id,
                        "email": "usuario@exemplo.com",
                        "nome": "Usuário",
                        "empresa_padrao": ""
                    }
                    self.supabase.table("usuarios").insert(user_data).execute()
                    print(f"Usuário {self.user_id} criado com dados mínimos")
            
        except Exception as e:
            print(f"Erro ao garantir usuário existe: {e}")
            # Não falhar se não conseguir criar o usuário
    
    # ==================== AUTENTICAÇÃO ====================
    
    def sign_up(self, email: str, password: str, nome: str, empresa_padrao: str = None) -> Dict[str, Any]:
        """Cadastra um novo usuário."""
        try:
            # Cadastrar no Supabase Auth
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {  # Metadados do usuário
                        "nome": nome,
                        "empresa_padrao": empresa_padrao
                    },
                    "email_redirect_to": "http://localhost:8503"  # Redirect para nossa aplicação
                }
            })
            
            if auth_response.user:
                return {
                    "success": True,
                    "user": auth_response.user,
                    "message": "Usuário cadastrado com sucesso! Verifique seu email para confirmar a conta."
                }
            else:
                return {
                    "success": False,
                    "error": "Erro ao cadastrar usuário",
                    "message": "Verifique os dados e tente novamente."
                }
                
        except Exception as e:
            error_msg = str(e)
            
            # Tratar erros específicos
            if "Email not confirmed" in error_msg:
                return {
                    "success": False,
                    "error": error_msg,
                    "message": "Cadastro realizado! Verifique seu email e clique no link de confirmação antes de fazer login."
                }
            elif "User already registered" in error_msg:
                return {
                    "success": False,
                    "error": error_msg,
                    "message": "Este email já está cadastrado. Tente fazer login ou use outro email."
                }
            else:
                return {
                    "success": False,
                    "error": error_msg,
                    "message": f"Erro ao cadastrar: {error_msg}"
                }
    
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Faz login do usuário."""
        try:
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user:
                self.user_id = auth_response.user.id
                
                # Buscar dados complementares do usuário (se existir)
                user_data = None
                try:
                    user_query = self.supabase.table("usuarios").select("*").eq("id", self.user_id).execute()
                    if user_query.data:
                        user_data = user_query.data[0]
                except Exception as e:
                    # Se não conseguir buscar dados complementares, usar dados do Auth
                    print(f"Aviso: Não foi possível buscar dados complementares: {e}")
                    user_data = {
                        "id": auth_response.user.id,
                        "email": auth_response.user.email,
                        "nome": auth_response.user.user_metadata.get("nome", email.split("@")[0]),
                        "empresa_padrao": auth_response.user.user_metadata.get("empresa_padrao", "")
                    }
                
                # Se não encontrou dados complementares, criar com base no Auth
                if not user_data:
                    user_data = {
                        "id": auth_response.user.id,
                        "email": auth_response.user.email,
                        "nome": auth_response.user.user_metadata.get("nome", email.split("@")[0]),
                        "empresa_padrao": auth_response.user.user_metadata.get("empresa_padrao", "")
                    }
                
                return {
                    "success": True,
                    "user": auth_response.user,
                    "user_data": user_data,
                    "message": "Login realizado com sucesso!"
                }
            else:
                return {
                    "success": False,
                    "error": "Credenciais inválidas",
                    "message": "Email ou senha incorretos."
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),  
                "message": f"Erro ao fazer login: {str(e)}"
            }
    
    def sign_out(self) -> Dict[str, Any]:
        """Faz logout do usuário."""
        try:
            self.supabase.auth.sign_out()
            self.user_id = None
            return {
                "success": True,
                "message": "Logout realizado com sucesso!"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Erro ao fazer logout."
            }
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Retorna o usuário atual logado."""
        try:
            user = self.supabase.auth.get_user()
            if user and user.user:
                return {
                    "id": user.user.id,
                    "email": user.user.email,
                    "created_at": user.user.created_at
                }
            return None
        except (AttributeError, ValueError):
            return None
    
    # ==================== CONTAS A PAGAR ====================
    
    def inserir_contas_a_pagar(self, df: pd.DataFrame, arquivo_origem: str = None, processamento_id: str = None, verificar_duplicatas: bool = True) -> Dict[str, Any]:
        """Insere contas a pagar no banco."""
        if not self.user_id:
            return {"success": False, "error": "Usuário não autenticado"}
        
        try:
            # Verificar se o usuário existe na tabela usuarios
            self._garantir_usuario_existe()
            
            # Gerar UUID válido para processamento_id se não for fornecido ou for inválido
            if processamento_id:
                try:
                    uuid.UUID(processamento_id)
                except ValueError:
                    processamento_id = str(uuid.uuid4())
            else:
                processamento_id = str(uuid.uuid4())
            
            # Verificar duplicatas se solicitado
            duplicatas_info = {"duplicatas": 0, "novos": len(df), "df_novos": df}
            if verificar_duplicatas:
                duplicatas_info = self.verificar_duplicatas_contas_a_pagar(df)
                df = duplicatas_info["df_novos"]
                
                # Se não há registros novos, retornar
                if len(df) == 0:
                    return {
                        "success": True,
                        "registros_inseridos": 0,
                        "duplicatas_ignoradas": duplicatas_info["duplicatas"],
                        "message": f"Nenhum registro novo encontrado. {duplicatas_info['duplicatas']} duplicatas ignoradas."
                    }
            
            # Preparar dados para inserção
            registros = []
            for _, row in df.iterrows():
                try:
                    # Tratar valor
                    valor = row.get('valor', 0)
                    if pd.isna(valor):
                        valor = 0
                    valor = float(valor)
                    
                    # Tratar data
                    data_vencimento = row.get('data_vencimento', '')
                    if pd.isna(data_vencimento):
                        data_vencimento = '2025-01-01'
                    else:
                        # Converter para string se for datetime
                        if hasattr(data_vencimento, 'strftime'):
                            data_vencimento = data_vencimento.strftime('%Y-%m-%d')
                        else:
                            data_vencimento = str(data_vencimento)
                    
                    # Tratar strings
                    empresa = str(row.get('empresa', '')).strip() if not pd.isna(row.get('empresa', '')) else ''
                    descricao = str(row.get('descricao', '')).strip() if not pd.isna(row.get('descricao', '')) else ''
                    categoria = str(row.get('categoria', '')).strip() if not pd.isna(row.get('categoria', '')) else ''
                    fornecedor = str(row.get('fornecedor', '')).strip() if not pd.isna(row.get('fornecedor', '')) else ''
                    
                    registro = {
                        "usuario_id": self.user_id,
                        "empresa": empresa,
                        "valor": valor,
                        "data_vencimento": data_vencimento,
                        "descricao": descricao,
                        "categoria": categoria,
                        "fornecedor": fornecedor,
                        "arquivo_origem": arquivo_origem,
                        "processamento_id": processamento_id
                    }
                    registros.append(registro)
                    
                except Exception as row_error:
                    print(f"Erro ao processar linha: {row_error}")
                    continue
            
            # Inserir no banco em lotes menores para evitar timeout
            batch_size = 100
            total_inseridos = 0
            
            for i in range(0, len(registros), batch_size):
                batch = registros[i:i + batch_size]
                
                try:
                    response = self.supabase.table("contas_a_pagar").insert(batch).execute()
                    total_inseridos += len(batch)
                    print(f"Lote {i//batch_size + 1}: {len(batch)} registros inseridos")
                    
                except Exception as batch_error:
                    print(f"Erro no lote {i//batch_size + 1}: {batch_error}")
                    # Tentar inserir um por um se der erro no lote
                    for registro in batch:
                        try:
                            self.supabase.table("contas_a_pagar").insert(registro).execute()
                            total_inseridos += 1
                        except Exception as single_error:
                            print(f"Erro ao inserir registro individual: {single_error}")
                            continue
            
            # Preparar mensagem final
            mensagem = f"{total_inseridos} contas a pagar inseridas com sucesso!"
            if verificar_duplicatas and duplicatas_info["duplicatas"] > 0:
                mensagem += f" {duplicatas_info['duplicatas']} duplicatas ignoradas."
            
            return {
                "success": True,
                "registros_inseridos": total_inseridos,
                "duplicatas_ignoradas": duplicatas_info["duplicatas"] if verificar_duplicatas else 0,
                "message": mensagem
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao inserir contas a pagar: {str(e)}"
            }
    
    def buscar_contas_a_pagar(self, empresa: str = None, data_inicio: str = None, data_fim: str = None) -> pd.DataFrame:
        """Busca contas a pagar do usuário."""
        if not self.user_id:
            return pd.DataFrame()
        
        try:
            query = self.supabase.table("contas_a_pagar").select("*").eq("usuario_id", self.user_id).order("data_vencimento", desc=False).order("id", desc=False).limit(10000)
            
            # Filtros opcionais
            if empresa:
                query = query.eq("empresa", empresa)
            if data_inicio:
                query = query.gte("data_vencimento", data_inicio)
            if data_fim:
                query = query.lte("data_vencimento", data_fim)
            
            response = query.execute()
            
            if response.data:
                return pd.DataFrame(response.data)
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Erro ao buscar contas a pagar: {e}")
            return pd.DataFrame()
    
    # ==================== CONTAS PAGAS ====================
    
    def inserir_contas_pagas(self, df: pd.DataFrame, arquivo_origem: str = None, processamento_id: str = None, verificar_duplicatas: bool = True) -> Dict[str, Any]:
        """Insere contas pagas no banco."""
        if not self.user_id:
            return {"success": False, "error": "Usuário não autenticado"}
        
        try:
            # Verificar se o usuário existe na tabela usuarios
            self._garantir_usuario_existe()
            
            # Gerar UUID válido para processamento_id se não for fornecido ou for inválido
            if processamento_id:
                try:
                    uuid.UUID(processamento_id)
                except ValueError:
                    processamento_id = str(uuid.uuid4())
            else:
                processamento_id = str(uuid.uuid4())
            
            # Verificar duplicatas se solicitado
            duplicatas_info = {"duplicatas": 0, "novos": len(df), "df_novos": df}
            if verificar_duplicatas:
                duplicatas_info = self.verificar_duplicatas_contas_pagas(df)
                df = duplicatas_info["df_novos"]
                
                # Se não há registros novos, retornar
                if len(df) == 0:
                    return {
                        "success": True,
                        "registros_inseridos": 0,
                        "duplicatas_ignoradas": duplicatas_info["duplicatas"],
                        "message": f"Nenhum registro novo encontrado. {duplicatas_info['duplicatas']} duplicatas ignoradas."
                    }
            
            # Preparar dados para inserção
            registros = []
            for _, row in df.iterrows():
                try:
                    # Tratar valor
                    valor = row.get('valor', 0)
                    if pd.isna(valor):
                        valor = 0
                    valor = float(valor)
                    
                    # Tratar data de pagamento
                    data_pagamento = row.get('data_pagamento', row.get('data_vencimento', ''))
                    if pd.isna(data_pagamento):
                        data_pagamento = '2025-01-01'
                    else:
                        # Converter para string se for datetime
                        if hasattr(data_pagamento, 'strftime'):
                            data_pagamento = data_pagamento.strftime('%Y-%m-%d')
                        else:
                            data_pagamento = str(data_pagamento)
                    
                    # Tratar strings
                    conta_corrente = str(row.get('conta_corrente', '')).strip() if not pd.isna(row.get('conta_corrente', '')) else ''
                    descricao = str(row.get('descricao', '')).strip() if not pd.isna(row.get('descricao', '')) else ''
                    categoria = str(row.get('categoria', '')).strip() if not pd.isna(row.get('categoria', '')) else ''
                    
                    registro = {
                        "usuario_id": self.user_id,
                        "conta_corrente": conta_corrente,
                        "valor": valor,
                        "data_pagamento": data_pagamento,
                        "descricao": descricao,
                        "categoria": categoria,
                        "arquivo_origem": arquivo_origem,
                        "processamento_id": processamento_id
                    }
                    registros.append(registro)
                    
                except Exception as row_error:
                    print(f"Erro ao processar linha de conta paga: {row_error}")
                    continue
            
            # Inserir no banco em lotes menores para evitar timeout
            batch_size = 100
            total_inseridos = 0
            
            for i in range(0, len(registros), batch_size):
                batch = registros[i:i + batch_size]
                
                try:
                    response = self.supabase.table("contas_pagas").insert(batch).execute()
                    total_inseridos += len(batch)
                    print(f"Lote contas pagas {i//batch_size + 1}: {len(batch)} registros inseridos")
                    
                except Exception as batch_error:
                    print(f"Erro no lote contas pagas {i//batch_size + 1}: {batch_error}")
                    # Tentar inserir um por um se der erro no lote
                    for registro in batch:
                        try:
                            self.supabase.table("contas_pagas").insert(registro).execute()
                            total_inseridos += 1
                        except Exception as single_error:
                            print(f"Erro ao inserir conta paga individual: {single_error}")
                            continue
            
            # Preparar mensagem final
            mensagem = f"{total_inseridos} contas pagas inseridas com sucesso!"
            if verificar_duplicatas and duplicatas_info["duplicatas"] > 0:
                mensagem += f" {duplicatas_info['duplicatas']} duplicatas ignoradas."
            
            return {
                "success": True,
                "registros_inseridos": total_inseridos,
                "duplicatas_ignoradas": duplicatas_info["duplicatas"] if verificar_duplicatas else 0,
                "message": mensagem
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao inserir contas pagas: {str(e)}"
            }
    
    def buscar_contas_pagas(self, data_inicio: str = None, data_fim: str = None) -> pd.DataFrame:
        """Busca contas pagas do usuário."""
        if not self.user_id:
            return pd.DataFrame()
        
        try:
            query = self.supabase.table("contas_pagas").select("*").eq("usuario_id", self.user_id).limit(10000)
            
            # Filtros opcionais
            if data_inicio:
                query = query.gte("data_pagamento", data_inicio)
            if data_fim:
                query = query.lte("data_pagamento", data_fim)
            
            response = query.execute()
            
            if response.data:
                return pd.DataFrame(response.data)
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Erro ao buscar contas pagas: {e}")
            return pd.DataFrame()
    
    def inserir_conta_paga(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insere uma nova conta paga no banco.
        
        Args:
            dados: Dicionário com os dados da conta paga
            
        Returns:
            Dict com success (bool) e message/data
        """
        if not self.user_id:
            return {"success": False, "message": "Usuário não autenticado"}

        try:
            # Garantir que o usuário existe
            self._garantir_usuario_existe()
            
            # Preparar dados para inserção - incluindo a coluna conta_corrente
            # Gerar UUID válido para processamento_id se não for fornecido ou for inválido
            processamento_id = dados.get("processamento_id", "")
            if processamento_id:
                # Verificar se é um UUID válido
                try:
                    uuid.UUID(processamento_id)
                    # É um UUID válido, manter
                except ValueError:
                    # Não é um UUID válido, gerar um novo
                    processamento_id = str(uuid.uuid4())
            else:
                # Está vazio, gerar um novo
                processamento_id = str(uuid.uuid4())
            
            dados_conta = {
                "usuario_id": self.user_id,
                "conta_corrente": str(dados.get("conta_corrente", "")),
                "valor": float(dados.get("valor", 0)),
                "data_pagamento": dados.get("data_pagamento"),
                "descricao": str(dados.get("descricao", "")),
                "categoria": str(dados.get("categoria", "OUTROS")),
                "arquivo_origem": str(dados.get("arquivo_origem", "")),
                "processamento_id": processamento_id
            }
            
            # Inserir no banco
            response = self.supabase.table("contas_pagas").insert(dados_conta).execute()
            
            if response.data:
                return {
                    "success": True,
                    "message": "Conta paga inserida com sucesso",
                    "data": response.data[0]
                }
            else:
                return {"success": False, "message": "Erro ao inserir conta paga"}
                
        except Exception as e:
            return {"success": False, "message": f"Erro ao inserir conta paga: {str(e)}"}
    
    # ==================== EMPRESAS ====================
    
    def listar_empresas(self) -> List[str]:
        """Lista todas as empresas do usuário."""
        if not self.user_id:
            return []
        
        try:
            # Buscar empresas únicas das contas a pagar
            response_a_pagar = self.supabase.table("contas_a_pagar")\
                .select("empresa")\
                .eq("usuario_id", self.user_id)\
                .limit(10000)\
                .execute()
            
            # Buscar empresas únicas das contas pagas
            response_pagas = self.supabase.table("contas_pagas")\
                .select("empresa")\
                .eq("usuario_id", self.user_id)\
                .limit(10000)\
                .execute()
            
            empresas = set()
            
            if response_a_pagar.data:
                empresas.update([item['empresa'] for item in response_a_pagar.data])
            
            if response_pagas.data:
                empresas.update([item['empresa'] for item in response_pagas.data])
            
            return sorted(list(empresas))
            
        except Exception as e:
            print(f"Erro ao listar empresas: {e}")
            return []
    
    # ==================== PROCESSAMENTOS ====================
    
    def registrar_processamento(self, tipo: str, status: str, detalhes: Dict[str, Any], arquivos: List[str] = None) -> str:
        """Registra um processamento no log."""
        if not self.user_id:
            return None
        
        try:
            # Garantir que usuário existe
            self._garantir_usuario_existe()
            
            processamento_id = str(uuid.uuid4())
            
            registro = {
                "id": processamento_id,
                "usuario_id": self.user_id,
                "tipo": tipo,
                "status": status,
                "detalhes": detalhes,
                "arquivos_processados": arquivos or []
            }
            
            self.supabase.table("processamentos").insert(registro).execute()
            
            return processamento_id
            
        except Exception as e:
            print(f"Erro ao registrar processamento: {e}")
            # Retornar um ID mesmo se falhar para não quebrar o fluxo
            return str(uuid.uuid4())
    
    # ==================== DASHBOARD ====================
    
    def get_resumo_financeiro(self) -> Dict[str, Any]:
        """Retorna resumo financeiro do usuário."""
        if not self.user_id:
            return {}
        
        try:
            # Buscar dados das contas a pagar
            contas_a_pagar = self.buscar_contas_a_pagar()
            contas_pagas = self.buscar_contas_pagas()
            
            # Calcular métricas
            total_a_pagar = contas_a_pagar['valor'].sum() if not contas_a_pagar.empty else 0
            total_pago = contas_pagas['valor'].sum() if not contas_pagas.empty else 0
            quantidade_a_pagar = len(contas_a_pagar) if not contas_a_pagar.empty else 0
            quantidade_pagas = len(contas_pagas) if not contas_pagas.empty else 0
            
            return {
                "total_a_pagar": float(total_a_pagar),
                "total_pago": float(total_pago),
                "quantidade_a_pagar": quantidade_a_pagar,
                "quantidade_pagas": quantidade_pagas,
                "empresas_total": len(self.listar_empresas())
            }
            
        except Exception as e:
            print(f"Erro ao calcular resumo financeiro: {e}")
            return {}
    
    # ==================== LIMPEZA DE DADOS ====================
    
    def limpar_contas_a_pagar(self) -> Dict[str, Any]:
        """Limpa apenas as contas a pagar do usuário."""
        if not self.user_id:
            return {"success": False, "error": "Usuário não autenticado"}
        
        try:
            # Contar registros antes da limpeza
            response = self.supabase.table("contas_a_pagar").select("id", count="exact").eq("usuario_id", self.user_id).execute()
            total_antes = response.count if response.count else 0
            
            # Limpar contas a pagar
            self.supabase.table("contas_a_pagar").delete().eq("usuario_id", self.user_id).execute()
            
            return {
                "success": True,
                "registros_removidos": total_antes,
                "message": f"Removidos {total_antes} registros de contas a pagar."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Erro ao limpar contas a pagar."
            }
    
    def limpar_contas_pagas(self) -> Dict[str, Any]:
        """Limpa apenas as contas pagas do usuário."""
        if not self.user_id:
            return {"success": False, "error": "Usuário não autenticado"}
        
        try:
            # Contar registros antes da limpeza
            response = self.supabase.table("contas_pagas").select("id", count="exact").eq("usuario_id", self.user_id).execute()
            total_antes = response.count if response.count else 0
            
            # Limpar contas pagas
            self.supabase.table("contas_pagas").delete().eq("usuario_id", self.user_id).execute()
            
            return {
                "success": True,
                "registros_removidos": total_antes,
                "message": f"Removidos {total_antes} registros de contas pagas."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Erro ao limpar contas pagas."
            }
    
    def limpar_dados_usuario(self) -> Dict[str, Any]:
        """Limpa todos os dados do usuário (use com cuidado!)."""
        if not self.user_id:
            return {"success": False, "error": "Usuário não autenticado"}
        
        try:
            # Contar total de registros antes da limpeza
            contas_a_pagar = self.supabase.table("contas_a_pagar").select("id", count="exact").eq("usuario_id", self.user_id).execute()
            contas_pagas = self.supabase.table("contas_pagas").select("id", count="exact").eq("usuario_id", self.user_id).execute()
            
            total_a_pagar = contas_a_pagar.count if contas_a_pagar.count else 0
            total_pagas = contas_pagas.count if contas_pagas.count else 0
            
            # Limpar tabelas na ordem correta (devido às foreign keys)
            self.supabase.table("correspondencias").delete().eq("usuario_id", self.user_id).execute()
            self.supabase.table("processamentos").delete().eq("usuario_id", self.user_id).execute()
            self.supabase.table("contas_pagas").delete().eq("usuario_id", self.user_id).execute()
            self.supabase.table("contas_a_pagar").delete().eq("usuario_id", self.user_id).execute()
            self.supabase.table("empresas").delete().eq("usuario_id", self.user_id).execute()
            
            return {
                "success": True,
                "contas_a_pagar_removidas": total_a_pagar,
                "contas_pagas_removidas": total_pagas,
                "message": f"Removidos {total_a_pagar} contas a pagar e {total_pagas} contas pagas."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Erro ao limpar dados do usuário."
            }
    
    # ==================== VERIFICAÇÃO DE DUPLICATAS ====================
    
    def verificar_duplicatas_contas_a_pagar(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Verifica se existem duplicatas nas contas a pagar antes de inserir.
        
        Critérios de duplicata:
        1. Mesmo usuário, empresa, fornecedor, valor, data_vencimento E descrição
        2. OU mesmo usuário, empresa, valor, data_vencimento com descrições muito similares
        """
        if not self.user_id:
            return {"duplicatas": 0, "novos": len(df), "df_novos": df}
        
        try:
            duplicatas = 0
            novos_registros = []
            registros_duplicados = []
            
            print(f"🔍 Verificando duplicatas para {len(df)} registros de contas a pagar...")
            
            for _, row in df.iterrows():
                # Extrair e normalizar campos principais
                empresa = str(row.get('empresa', '')).strip().upper()
                fornecedor = str(row.get('fornecedor', '')).strip().upper()
                valor = float(row.get('valor', 0)) if not pd.isna(row.get('valor', 0)) else 0
                descricao = str(row.get('descricao', '')).strip().upper()
                
                # Tratar data de vencimento
                data_vencimento = row.get('data_vencimento', '')
                if pd.isna(data_vencimento):
                    data_vencimento = '2025-01-01'
                else:
                    if hasattr(data_vencimento, 'strftime'):
                        data_vencimento = data_vencimento.strftime('%Y-%m-%d')
                    else:
                        data_vencimento = str(data_vencimento)[:10]  # Garantir formato YYYY-MM-DD
                
                # Verificar duplicatas no banco
                response = self.supabase.table("contas_a_pagar")\
                    .select("id,empresa,fornecedor,valor,data_vencimento,descricao")\
                    .eq("usuario_id", self.user_id)\
                    .eq("empresa", empresa)\
                    .eq("valor", valor)\
                    .eq("data_vencimento", data_vencimento)\
                    .limit(10)\
                    .execute()
                
                eh_duplicata = False
                
                if response.data and len(response.data) > 0:
                    # Verificar se algum registro existente é muito similar
                    for registro_existente in response.data:
                        fornecedor_existente = str(registro_existente.get('fornecedor', '')).strip().upper()
                        descricao_existente = str(registro_existente.get('descricao', '')).strip().upper()
                        
                        # Critério 1: Fornecedor e descrição exatos
                        if (fornecedor == fornecedor_existente and 
                            descricao == descricao_existente):
                            eh_duplicata = True
                            break
                        
                        # Critério 2: Mesmo fornecedor e descrições muito similares
                        if fornecedor == fornecedor_existente:
                            similaridade = self._calcular_similaridade_texto(descricao, descricao_existente)
                            if similaridade > 0.8:
                                eh_duplicata = True
                                break
                        
                        # Critério 3: Descrições idênticas (mesmo sem fornecedor)
                        if descricao and len(descricao) > 10 and descricao == descricao_existente:
                            eh_duplicata = True
                            break
                
                if eh_duplicata:
                    duplicatas += 1
                    registros_duplicados.append({
                        'empresa': row.get('empresa', ''),
                        'fornecedor': row.get('fornecedor', ''),
                        'valor': valor,
                        'data_vencimento': data_vencimento,
                        'descricao': row.get('descricao', ''),
                        'motivo': 'Registro similar já existe no banco'
                    })
                    print(f"📋 Duplicata encontrada: {empresa} - {fornecedor} - R${valor}")
                else:
                    novos_registros.append(row)
            
            resultado = {
                "duplicatas": duplicatas,
                "novos": len(novos_registros),
                "df_novos": pd.DataFrame(novos_registros) if novos_registros else pd.DataFrame(),
                "registros_duplicados": registros_duplicados
            }
            
            if duplicatas > 0:
                print(f"⚠️ {duplicatas} duplicatas encontradas e serão ignoradas")
            if len(novos_registros) > 0:
                print(f"✅ {len(novos_registros)} registros novos serão inseridos")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Erro ao verificar duplicatas contas a pagar: {e}")
            # Em caso de erro, considerar todos como novos para não bloquear
            return {"duplicatas": 0, "novos": len(df), "df_novos": df}
    
    def verificar_duplicatas_contas_pagas(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Verifica se existem duplicatas nas contas pagas antes de inserir.
        
        Critérios de duplicata:
        1. Mesmo usuário, empresa, fornecedor, valor, data_pagamento E descrição
        2. OU mesmo usuário, empresa, valor, data_pagamento com diferença mínima na descrição
        """
        if not self.user_id:
            return {"duplicatas": 0, "novos": len(df), "df_novos": df}
        
        try:
            duplicatas = 0
            novos_registros = []
            registros_duplicados = []
            
            print(f"🔍 Verificando duplicatas para {len(df)} registros de contas pagas...")
            
            for _, row in df.iterrows():
                # Extrair e normalizar campos principais
                empresa = str(row.get('empresa', '')).strip().upper()
                fornecedor = str(row.get('fornecedor', '')).strip().upper()
                valor = float(row.get('valor', 0)) if not pd.isna(row.get('valor', 0)) else 0
                descricao = str(row.get('descricao', '')).strip().upper()
                
                # Tratar data de pagamento
                data_pagamento = row.get('data_pagamento', '')
                if pd.isna(data_pagamento):
                    data_pagamento = '2025-01-01'
                else:
                    if hasattr(data_pagamento, 'strftime'):
                        data_pagamento = data_pagamento.strftime('%Y-%m-%d')
                    else:
                        data_pagamento = str(data_pagamento)[:10]  # Garantir formato YYYY-MM-DD
                
                # Primeiro: verificação exata (incluindo fornecedor)
                response = self.supabase.table("contas_pagas")\
                    .select("id,empresa,fornecedor,valor,data_pagamento,descricao")\
                    .eq("usuario_id", self.user_id)\
                    .eq("empresa", empresa)\
                    .eq("valor", valor)\
                    .eq("data_pagamento", data_pagamento)\
                    .limit(10)\
                    .execute()
                
                eh_duplicata = False
                
                if response.data and len(response.data) > 0:
                    # Verificar se algum registro existente é muito similar
                    for registro_existente in response.data:
                        fornecedor_existente = str(registro_existente.get('fornecedor', '')).strip().upper()
                        descricao_existente = str(registro_existente.get('descricao', '')).strip().upper()
                        
                        # Critério 1: Fornecedor e descrição exatos
                        if (fornecedor == fornecedor_existente and 
                            descricao == descricao_existente):
                            eh_duplicata = True
                            break
                        
                        # Critério 2: Mesmo fornecedor e descrições muito similares (>80% similaridade)
                        if fornecedor == fornecedor_existente:
                            similaridade = self._calcular_similaridade_texto(descricao, descricao_existente)
                            if similaridade > 0.8:
                                eh_duplicata = True
                                break
                        
                        # Critério 3: Descrições idênticas (mesmo sem fornecedor)
                        if descricao and len(descricao) > 10 and descricao == descricao_existente:
                            eh_duplicata = True
                            break
                
                if eh_duplicata:
                    duplicatas += 1
                    registros_duplicados.append({
                        'empresa': row.get('empresa', ''),
                        'fornecedor': row.get('fornecedor', ''),
                        'valor': valor,
                        'data_pagamento': data_pagamento,
                        'descricao': row.get('descricao', ''),
                        'motivo': 'Registro similar já existe no banco'
                    })
                    print(f"📋 Duplicata encontrada: {empresa} - {fornecedor} - R${valor}")
                else:
                    novos_registros.append(row)
            
            resultado = {
                "duplicatas": duplicatas,
                "novos": len(novos_registros),
                "df_novos": pd.DataFrame(novos_registros) if novos_registros else pd.DataFrame(),
                "registros_duplicados": registros_duplicados
            }
            
            if duplicatas > 0:
                print(f"⚠️ {duplicatas} duplicatas encontradas e serão ignoradas")
            if len(novos_registros) > 0:
                print(f"✅ {len(novos_registros)} registros novos serão inseridos")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Erro ao verificar duplicatas: {e}")
            # Em caso de erro, considerar todos como novos para não bloquear
            return {"duplicatas": 0, "novos": len(df), "df_novos": df}
    
    def _calcular_similaridade_texto(self, texto1: str, texto2: str) -> float:
        """
        Calcula similaridade entre dois textos usando algoritmo simples.
        Retorna valor entre 0 (totalmente diferente) e 1 (idêntico).
        """
        if not texto1 or not texto2:
            return 0.0
        
        # Normalizar textos
        t1 = texto1.upper().strip()
        t2 = texto2.upper().strip()
        
        if t1 == t2:
            return 1.0
        
        # Calcular similaridade por palavras comuns
        palavras1 = set(t1.split())
        palavras2 = set(t2.split())
        
        if not palavras1 or not palavras2:
            return 0.0
        
        intersecao = palavras1.intersection(palavras2)
        uniao = palavras1.union(palavras2)
        
        return len(intersecao) / len(uniao) if uniao else 0.0
