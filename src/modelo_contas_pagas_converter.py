"""
Conversor específico para o arquivo Modelo_Contas_Pagas.xlsx
Mapeia os campos conforme a nova estrutura definida.
"""

import pandas as pd
import os
import uuid
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModeloContasPagasConverter:
    """Conversor para arquivos no formato Modelo_Contas_Pagas.xlsx"""
    
    def __init__(self):
        # Mapeamento dos campos do Excel para o banco - IGUAL ao contas_pagas_validator
        self.mapeamento_campos = {
            'IdBanco': 'conta_corrente',
            'Datapagamento': 'data_pagamento', 
            'DescriçãoConta': 'categoria',
            'Saída': 'valor',
            'Histórico': 'descricao'
        }
        
        # Possíveis variações dos nomes das colunas
        self.variacoes_nomes = {
            'IdBanco': ['IdBanco', 'Id Banco', 'ID_BANCO', 'IDBANCO'],
            'Datapagamento': ['Datapagamento', 'Data pagamento', 'Data Pagamento', 'DATA_PAGAMENTO'],
            'DescriçãoConta': ['DescriçãoConta', 'Descrição Conta', 'Descricao Conta', 'DESCRICAO_CONTA'],
            'Saída': ['Saída', 'Saida', 'SAIDA', 'Valor Saída', 'Valor Saida'],
            'Histórico': ['Histórico', 'Historico', 'HISTORICO', 'História']
        }
    
    def detectar_formato_modelo_contas_pagas(self, arquivo_path: str) -> bool:
        """
        Detecta se o arquivo é do formato Modelo_Contas_Pagas.
        
        Args:
            arquivo_path: Caminho para o arquivo
            
        Returns:
            bool: True se for formato Modelo_Contas_Pagas
        """
        try:
            # Verificar pelo nome do arquivo primeiro
            nome_arquivo = os.path.basename(arquivo_path).lower()
            if 'modelo_contas_pagas' in nome_arquivo or 'contas_pagas' in nome_arquivo:
                return True
            
            # Verificar pelas colunas
            df = pd.read_excel(arquivo_path, nrows=5)  # Ler apenas as primeiras linhas
            colunas = [col.strip() for col in df.columns]
            
            # Verificar se tem pelo menos 3 das 5 colunas esperadas
            colunas_encontradas = 0
            for campo_esperado, variacoes in self.variacoes_nomes.items():
                for variacao in variacoes:
                    if variacao in colunas:
                        colunas_encontradas += 1
                        break
            
            return colunas_encontradas >= 3
            
        except Exception as e:
            logger.error(f"Erro ao detectar formato Modelo_Contas_Pagas: {e}")
            return False
    
    def normalizar_nome_coluna(self, nome_coluna: str) -> str:
        """
        Normaliza o nome da coluna para o padrão esperado.
        
        Args:
            nome_coluna: Nome da coluna original
            
        Returns:
            str: Nome da coluna normalizado ou None se não encontrado
        """
        nome_limpo = nome_coluna.strip()
        
        for campo_padrao, variacoes in self.variacoes_nomes.items():
            if nome_limpo in variacoes:
                return campo_padrao
        
        return None
    
    def converter_modelo_contas_pagas(self, arquivo_path: str) -> pd.DataFrame:
        """
        Converte arquivo Modelo_Contas_Pagas.xlsx para o formato do banco.
        
        Args:
            arquivo_path: Caminho para o arquivo Excel
            
        Returns:
            DataFrame convertido
        """
        try:
            logger.info(f"Convertendo arquivo Modelo_Contas_Pagas: {arquivo_path}")
            
            # Ler o arquivo Excel
            df = pd.read_excel(arquivo_path)
            
            if df.empty:
                logger.warning("Arquivo vazio")
                return pd.DataFrame()
            
            logger.info(f"Arquivo carregado com {len(df)} linhas e colunas: {list(df.columns)}")
            
            # Normalizar nomes das colunas
            mapeamento_encontrado = {}
            for col in df.columns:
                nome_normalizado = self.normalizar_nome_coluna(str(col))
                if nome_normalizado:
                    mapeamento_encontrado[col] = nome_normalizado
            
            logger.info(f"Mapeamento de colunas encontrado: {mapeamento_encontrado}")
            
            # Criar DataFrame resultado
            df_resultado = pd.DataFrame()
            
            # Mapear cada campo
            for col_original, campo_normalizado in mapeamento_encontrado.items():
                campo_banco = self.mapeamento_campos[campo_normalizado]
                df_resultado[campo_banco] = df[col_original]
            
            # Tratamentos específicos dos dados
            df_resultado = self._processar_dados(df_resultado)
            
            logger.info(f"Conversão concluída: {len(df_resultado)} registros convertidos")
            logger.info(f"Colunas finais: {list(df_resultado.columns)}")
            
            return df_resultado
            
        except Exception as e:
            logger.error(f"Erro ao converter arquivo Modelo_Contas_Pagas: {e}")
            return pd.DataFrame()
    
    def _processar_dados(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processa e limpa os dados convertidos.
        
        Args:
            df: DataFrame com dados convertidos
            
        Returns:
            DataFrame processado
        """
        df_processed = df.copy()
        
        # Processar data_pagamento
        if 'data_pagamento' in df_processed.columns:
            df_processed['data_pagamento'] = pd.to_datetime(df_processed['data_pagamento'], errors='coerce')
            # Remover registros sem data válida
            df_processed = df_processed.dropna(subset=['data_pagamento'])
        
        # Processar valor (Saída)
        if 'valor' in df_processed.columns:
            df_processed['valor'] = pd.to_numeric(df_processed['valor'], errors='coerce')
            # Remover registros com valor zero ou inválido
            df_processed = df_processed.dropna(subset=['valor'])
            df_processed = df_processed[df_processed['valor'] > 0]
        
        # Processar campos de texto
        campos_texto = ['conta_corrente', 'categoria', 'descricao']
        for campo in campos_texto:
            if campo in df_processed.columns:
                df_processed[campo] = df_processed[campo].astype(str).str.strip()
                # Remover registros vazios
                df_processed = df_processed[df_processed[campo] != '']
                df_processed = df_processed[~df_processed[campo].isin(['nan', 'NaN', 'None'])]
        
        # Adicionar campos de controle
        df_processed['arquivo_origem'] = 'modelo_contas_pagas'
        df_processed['processamento_id'] = df_processed.apply(lambda x: str(uuid.uuid4()), axis=1)
        
        # Resetar índice
        df_processed = df_processed.reset_index(drop=True)
        
        logger.info(f"Dados processados: {len(df_processed)} registros válidos")
        
        return df_processed


# Função standalone para uso direto
def converter_modelo_contas_pagas_standalone(arquivo_path: str) -> pd.DataFrame:
    """
    Função standalone para converter arquivo Modelo_Contas_Pagas.
    
    Args:
        arquivo_path: Caminho para o arquivo
        
    Returns:
        DataFrame convertido
    """
    converter = ModeloContasPagasConverter()
    return converter.converter_modelo_contas_pagas(arquivo_path)


if __name__ == "__main__":
    # Teste do conversor
    arquivo_teste = "ArquivosModeloCliente/Modelo_Contas_Pagar.xlsx"  # Adapte o caminho
    
    converter = ModeloContasPagasConverter()
    
    if converter.detectar_formato_modelo_contas_pagas(arquivo_teste):
        print("✅ Formato detectado como Modelo_Contas_Pagas")
        df_convertido = converter.converter_modelo_contas_pagas(arquivo_teste)
        print(f"📊 Dados convertidos: {len(df_convertido)} registros")
        if not df_convertido.empty:
            print("🔍 Primeiras 5 linhas:")
            print(df_convertido.head())
    else:
        print("❌ Formato não detectado como Modelo_Contas_Pagas")
