"""
Módulo para processamento de arquivos Excel de contas a pagar e contas pagas.
"""

import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExcelProcessor:
    """Classe para processar arquivos Excel de contas financeiras."""
    
    def __init__(self, data_path: str = "data"):
        self.data_path = data_path
        self.contas_a_pagar_path = os.path.join(data_path, "contas_a_pagar")
        self.contas_pagas_path = os.path.join(data_path, "contas_pagas")
        self.processed_path = os.path.join(data_path, "processed")
        
        # Colunas esperadas nos arquivos
        self.colunas_a_pagar = ["empresa", "valor", "data_vencimento", "descricao", "categoria"]
        self.colunas_pagas = ["empresa", "valor", "data_pagamento", "descricao", "categoria"]
    
    def validar_colunas(self, df: pd.DataFrame, colunas_esperadas: List[str], tipo_arquivo: str) -> bool:
        """
        Valida se o DataFrame possui as colunas necessárias.
        
        Args:
            df: DataFrame a ser validado
            colunas_esperadas: Lista de colunas que devem estar presentes
            tipo_arquivo: Tipo do arquivo para logging
            
        Returns:
            bool: True se todas as colunas estão presentes
        """
        colunas_presentes = [col.lower().replace(" ", "_") for col in df.columns]
        colunas_faltantes = [col for col in colunas_esperadas if col not in colunas_presentes]
        
        if colunas_faltantes:
            logger.error(f"Colunas faltantes no arquivo {tipo_arquivo}: {colunas_faltantes}")
            return False
        
        return True
    
    def normalizar_colunas(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza os nomes das colunas do DataFrame.
        
        Args:
            df: DataFrame com colunas a serem normalizadas
            
        Returns:
            DataFrame com colunas normalizadas
        """
        df.columns = [col.lower().replace(" ", "_") for col in df.columns]
        return df
    
    def processar_contas_a_pagar(self, arquivo_path: str) -> Optional[pd.DataFrame]:
        """
        Processa arquivo Excel de contas a pagar.
        
        Args:
            arquivo_path: Caminho para o arquivo Excel
            
        Returns:
            DataFrame processado ou None se houver erro
        """
        try:
            df = pd.read_excel(arquivo_path)
            df = self.normalizar_colunas(df)
            
            if not self.validar_colunas(df, self.colunas_a_pagar, "contas a pagar"):
                return None
            
            # Converter data de vencimento
            df['data_vencimento'] = pd.to_datetime(df['data_vencimento'], errors='coerce')
            
            # Converter valor para numérico
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
            
            # Remover linhas com dados inválidos
            df = df.dropna(subset=['data_vencimento', 'valor'])
            
            # Adicionar metadados
            df['arquivo_origem'] = os.path.basename(arquivo_path)
            df['data_processamento'] = datetime.now()
            
            logger.info(f"Processadas {len(df)} contas a pagar do arquivo {arquivo_path}")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo de contas a pagar {arquivo_path}: {str(e)}")
            return None
    
    def processar_contas_pagas(self, arquivo_path: str) -> Optional[pd.DataFrame]:
        """
        Processa arquivo Excel de contas pagas.
        
        Args:
            arquivo_path: Caminho para o arquivo Excel
            
        Returns:
            DataFrame processado ou None se houver erro
        """
        try:
            df = pd.read_excel(arquivo_path)
            df = self.normalizar_colunas(df)
            
            if not self.validar_colunas(df, self.colunas_pagas, "contas pagas"):
                return None
            
            # Converter data de pagamento
            df['data_pagamento'] = pd.to_datetime(df['data_pagamento'], errors='coerce')
            
            # Converter valor para numérico
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
            
            # Remover linhas com dados inválidos
            df = df.dropna(subset=['data_pagamento', 'valor'])
            
            # Adicionar metadados
            df['arquivo_origem'] = os.path.basename(arquivo_path)
            df['data_processamento'] = datetime.now()
            
            logger.info(f"Processadas {len(df)} contas pagas do arquivo {arquivo_path}")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo de contas pagas {arquivo_path}: {str(e)}")
            return None
    
    def carregar_todos_arquivos_a_pagar(self) -> pd.DataFrame:
        """
        Carrega e consolida todos os arquivos de contas a pagar.
        
        Returns:
            DataFrame consolidado com todas as contas a pagar
        """
        dfs = []
        
        if not os.path.exists(self.contas_a_pagar_path):
            logger.warning(f"Diretório {self.contas_a_pagar_path} não encontrado")
            return pd.DataFrame()
        
        for arquivo in os.listdir(self.contas_a_pagar_path):
            if arquivo.endswith(('.xlsx', '.xls')):
                arquivo_path = os.path.join(self.contas_a_pagar_path, arquivo)
                df = self.processar_contas_a_pagar(arquivo_path)
                if df is not None:
                    dfs.append(df)
        
        if dfs:
            df_consolidado = pd.concat(dfs, ignore_index=True)
            logger.info(f"Consolidadas {len(df_consolidado)} contas a pagar de {len(dfs)} arquivos")
            return df_consolidado
        else:
            return pd.DataFrame()
    
    def carregar_todos_arquivos_pagos(self) -> pd.DataFrame:
        """
        Carrega e consolida todos os arquivos de contas pagas.
        
        Returns:
            DataFrame consolidado com todas as contas pagas
        """
        dfs = []
        
        if not os.path.exists(self.contas_pagas_path):
            logger.warning(f"Diretório {self.contas_pagas_path} não encontrado")
            return pd.DataFrame()
        
        for arquivo in os.listdir(self.contas_pagas_path):
            if arquivo.endswith(('.xlsx', '.xls')):
                arquivo_path = os.path.join(self.contas_pagas_path, arquivo)
                df = self.processar_contas_pagas(arquivo_path)
                if df is not None:
                    dfs.append(df)
        
        if dfs:
            df_consolidado = pd.concat(dfs, ignore_index=True)
            logger.info(f"Consolidadas {len(df_consolidado)} contas pagas de {len(dfs)} arquivos")
            return df_consolidado
        else:
            return pd.DataFrame()
    
    def carregar_arquivo_excel(self, arquivo_path: str) -> Optional[pd.DataFrame]:
        """
        Carrega um arquivo Excel genérico.
        
        Args:
            arquivo_path: Caminho para o arquivo Excel
            
        Returns:
            DataFrame carregado ou None se houver erro
        """
        try:
            df = pd.read_excel(arquivo_path)
            logger.info(f"Arquivo Excel carregado com sucesso: {arquivo_path} ({len(df)} linhas)")
            return df
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo Excel {arquivo_path}: {str(e)}")
            return None
    
    def salvar_dados_processados(self, df: pd.DataFrame, nome_arquivo: str) -> bool:
        """
        Salva DataFrame processado em arquivo Excel.
        
        Args:
            df: DataFrame a ser salvo
            nome_arquivo: Nome do arquivo (sem extensão)
            
        Returns:
            bool: True se salvou com sucesso
        """
        try:
            os.makedirs(self.processed_path, exist_ok=True)
            arquivo_path = os.path.join(self.processed_path, f"{nome_arquivo}.xlsx")
            df.to_excel(arquivo_path, index=False)
            logger.info(f"Dados salvos em {arquivo_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar dados processados: {str(e)}")
            return False
