"""
Conversor específico para arquivos do sistema do cliente.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, List, Dict
import logging
import os

# Importar o novo conversor de contas pagas
from .modelo_contas_pagas_converter import ModeloContasPagasConverter

logger = logging.getLogger(__name__)


class ClientFileConverter:
    """Conversor para arquivos no formato específico do cliente."""
    
    def __init__(self):
        # Inicializar o conversor de contas pagas
        self.conversor_contas_pagas = ModeloContasPagasConverter()
        
        self.colunas_mapeamento = {
            'EmpresaNome': 'empresa_origem',
            'Campo39': 'data_vencimento', 
            'NomeEmpresa': 'empresa',
            'IdConta': 'id_conta',
            'DescriçãoConta': 'categoria',
            'NúmeroDocumento': 'numero_documento',
            'ValorDoc': 'valor',
            'Histórico': 'descricao',
            'IdMovimento': 'id_movimento'
        }
        
        # Mapeamento para o novo formato "Modelo_Contas_Pagar"
        self.colunas_modelo_contas_pagar = {
            'Empresa': 'empresa',
            'DataVencimento': 'data_vencimento',
            'Fornecedor': 'fornecedor',
            'ValorDoc': 'valor',
            'Histórico': 'descricao',
            'DescriçãoConta': 'categoria',
            'NúmeroDocumento': 'numero_documento',
            'IdConta_Financeira': 'id_conta',
            'IdMovimento': 'id_movimento'
        }
    
    def detectar_formato_cliente(self, arquivo_path: str) -> bool:
        """
        Detecta se o arquivo está no formato do cliente.
        
        Args:
            arquivo_path: Caminho para o arquivo
            
        Returns:
            bool: True se for formato do cliente
        """
        try:
            df = pd.read_excel(arquivo_path)
            
            # Verificar se tem as colunas características do formato do cliente
            if len(df.columns) >= 10:
                primeira_linha = df.iloc[0] if len(df) > 0 else None
                if primeira_linha is not None:
                    valores_str = [str(val) for val in primeira_linha.tolist()]
                    return any('EmpresaNome' in val for val in valores_str)
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao detectar formato do cliente: {str(e)}")
            return False
    
    def detectar_formato_modelo_contas_pagar(self, arquivo_path: str) -> bool:
        """
        Detecta se o arquivo está no formato "Modelo_Contas_Pagar".
        
        Args:
            arquivo_path: Caminho para o arquivo
            
        Returns:
            bool: True se for formato Modelo_Contas_Pagar
        """
        try:
            # Verificar se tem a aba "Contas a Pagar"
            excel_file = pd.ExcelFile(arquivo_path)
            if 'Contas a Pagar' not in excel_file.sheet_names:
                return False
            
            # Ler a aba específica
            df = pd.read_excel(arquivo_path, sheet_name='Contas a Pagar')
            
            # Verificar se tem as colunas características
            colunas_necessarias = ['Empresa', 'DataVencimento', 'Fornecedor', 'ValorDoc', 'Histórico']
            colunas_arquivo = [col for col in df.columns]
            
            # Verificar se pelo menos 4 das 5 colunas principais estão presentes
            colunas_encontradas = sum(1 for col in colunas_necessarias if col in colunas_arquivo)
            
            return colunas_encontradas >= 4
            
        except Exception as e:
            logger.error(f"Erro ao detectar formato Modelo_Contas_Pagar: {str(e)}")
            return False
    
    def converter_arquivo_cliente(self, arquivo_path: str) -> Optional[pd.DataFrame]:
        """
        Converte arquivo do formato do cliente para o formato padrão.
        
        Args:
            arquivo_path: Caminho para o arquivo do cliente
            
        Returns:
            DataFrame convertido ou None se houver erro
        """
        try:
            # Ler arquivo
            df_original = pd.read_excel(arquivo_path)
            
            logger.info(f"Processando arquivo do cliente: {arquivo_path}")
            logger.info(f"Tamanho original: {df_original.shape}")
            
            # Identificar linha de cabeçalho (linha 0 contém os nomes das colunas)
            colunas_reais = df_original.iloc[0].tolist()
            
            # Renomear colunas baseado na primeira linha
            df = df_original.copy()
            df.columns = [str(col) if pd.notna(col) else f'col_{i}' for i, col in enumerate(colunas_reais)]
            
            # Remover a linha de cabeçalho
            df = df.iloc[1:].reset_index(drop=True)
            
            # Processar dados
            dados_convertidos = []
            data_vencimento_atual = None
            empresa_origem_atual = None
            
            for idx, row in df.iterrows():
                # Verificar se é uma linha de data
                if pd.notna(row.get('Campo39')) and isinstance(row['Campo39'], datetime):
                    data_vencimento_atual = row['Campo39']
                    continue
                
                # Verificar se é uma linha de empresa origem
                if pd.notna(row.get('EmpresaNome')) and pd.isna(row.get('NomeEmpresa')):
                    empresa_origem_atual = row['EmpresaNome']
                    continue
                
                # Verificar se é uma linha com dados válidos
                if (pd.notna(row.get('NomeEmpresa')) and 
                    pd.notna(row.get('ValorDoc')) and 
                    row['ValorDoc'] != 0):
                    
                    dados_convertidos.append({
                        'empresa_origem': empresa_origem_atual,
                        'empresa': row['NomeEmpresa'],
                        'valor': float(row['ValorDoc']) if pd.notna(row['ValorDoc']) else 0.0,
                        'data_vencimento': data_vencimento_atual,
                        'descricao': row.get('Histórico', ''),
                        'categoria': row.get('DescriçãoConta', ''),
                        'numero_documento': row.get('NúmeroDocumento', ''),
                        'id_conta': row.get('IdConta', ''),
                        'id_movimento': row.get('IdMovimento', ''),
                        'arquivo_origem': os.path.basename(arquivo_path)
                    })
            
            if not dados_convertidos:
                logger.warning("Nenhum dado válido encontrado no arquivo")
                return None
            
            # Criar DataFrame convertido
            df_convertido = pd.DataFrame(dados_convertidos)
            
            # Limpar e validar dados
            df_convertido = self._limpar_dados_convertidos(df_convertido, 'formato_erp_cliente')
            
            logger.info(f"Conversão concluída: {len(df_convertido)} registros convertidos")
            return df_convertido
            
        except Exception as e:
            logger.error(f"Erro ao converter arquivo do cliente: {str(e)}")
            return None
    
    def converter_modelo_contas_pagar(self, arquivo_path: str) -> Optional[pd.DataFrame]:
        """
        Converte arquivo do formato "Modelo_Contas_Pagar" para o formato padrão.
        
        Args:
            arquivo_path: Caminho para o arquivo Modelo_Contas_Pagar
            
        Returns:
            DataFrame convertido ou None se houver erro
        """
        try:
            # Ler a aba "Contas a Pagar"
            df_original = pd.read_excel(arquivo_path, sheet_name='Contas a Pagar')
            
            logger.info(f"Processando arquivo Modelo_Contas_Pagar: {arquivo_path}")
            logger.info(f"Tamanho original: {df_original.shape}")
            
            # Verificar se tem dados
            if df_original.empty:
                logger.warning("Arquivo está vazio")
                return None
            
            # Criar DataFrame convertido com mapeamento das colunas
            dados_convertidos = []
            
            for idx, row in df_original.iterrows():
                try:
                    # Verificar se tem dados válidos (empresa e valor)
                    if pd.isna(row.get('Empresa')) or pd.isna(row.get('ValorDoc')):
                        continue
                    
                    # Tratar valor
                    valor = row.get('ValorDoc', 0)
                    if pd.isna(valor) or valor == 0:
                        continue
                    
                    # Tratar data
                    data_vencimento = row.get('DataVencimento')
                    if pd.isna(data_vencimento):
                        continue
                    
                    # Montar registro convertido
                    registro = {
                        'empresa': str(row.get('Empresa', '')).strip(),
                        'data_vencimento': data_vencimento,
                        'valor': float(valor),
                        'descricao': str(row.get('Histórico', '')).strip(),
                        'categoria': str(row.get('DescriçãoConta', '')).strip(),
                        'fornecedor': str(row.get('Fornecedor', '')).strip(),
                        'numero_documento': str(row.get('NúmeroDocumento', '')).strip(),
                        'id_conta': row.get('IdConta_Financeira'),
                        'id_movimento': row.get('IdMovimento')
                    }
                    
                    dados_convertidos.append(registro)
                    
                except Exception as row_error:
                    logger.warning(f"Erro ao processar linha {idx}: {str(row_error)}")
                    continue
            
            if not dados_convertidos:
                logger.warning("Nenhum dado válido encontrado no arquivo")
                return None
            
            # Criar DataFrame
            df_convertido = pd.DataFrame(dados_convertidos)
            
            # Limpar e validar dados
            df_convertido = self._limpar_dados_convertidos(df_convertido, 'modelo_contas_pagar')
            
            logger.info(f"Conversão Modelo_Contas_Pagar concluída: {len(df_convertido)} registros convertidos")
            return df_convertido
            
        except Exception as e:
            logger.error(f"Erro ao converter arquivo Modelo_Contas_Pagar: {str(e)}")
            return None
    
    def _limpar_dados_convertidos(self, df: pd.DataFrame, tipo_conversao: str = 'formato_cliente') -> pd.DataFrame:
        """
        Limpa e valida os dados convertidos.
        
        Args:
            df: DataFrame com dados convertidos
            tipo_conversao: Tipo de conversão realizada
            
        Returns:
            DataFrame limpo
        """
        # Remover linhas com dados essenciais vazios
        df = df.dropna(subset=['empresa', 'valor', 'data_vencimento'])
        
        # Converter tipos de dados
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        df['data_vencimento'] = pd.to_datetime(df['data_vencimento'], errors='coerce')
        
        # Remover linhas com conversões inválidas
        df = df.dropna(subset=['valor', 'data_vencimento'])
        
        # Limpar strings
        colunas_string = ['empresa_origem', 'empresa', 'descricao', 'categoria', 'numero_documento', 'fornecedor']
        for col in colunas_string:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace('nan', '')
        
        # Adicionar metadados
        df['data_processamento'] = datetime.now()
        df['tipo_conversao'] = tipo_conversao
        
        return df
    
    def salvar_arquivo_convertido(self, df: pd.DataFrame, arquivo_original: str, 
                                diretorio_destino: str = "data/contas_a_pagar") -> str:
        """
        Salva o arquivo convertido.
        
        Args:
            df: DataFrame convertido
            arquivo_original: Nome do arquivo original
            diretorio_destino: Diretório de destino
            
        Returns:
            Caminho do arquivo salvo
        """
        try:
            os.makedirs(diretorio_destino, exist_ok=True)
            
            # Gerar nome do arquivo convertido
            nome_base = os.path.splitext(os.path.basename(arquivo_original))[0]
            nome_convertido = f"{nome_base}_convertido_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            arquivo_destino = os.path.join(diretorio_destino, nome_convertido)
            
            # Salvar arquivo
            df.to_excel(arquivo_destino, index=False)
            
            logger.info(f"Arquivo convertido salvo: {arquivo_destino}")
            return arquivo_destino
            
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo convertido: {str(e)}")
            return None
    
    def gerar_relatorio_conversao(self, df_original: pd.DataFrame, 
                                 df_convertido: pd.DataFrame) -> Dict:
        """
        Gera relatório da conversão.
        
        Args:
            df_original: DataFrame original
            df_convertido: DataFrame convertido
            
        Returns:
            Dicionário com estatísticas da conversão
        """
        relatorio = {
            'registros_originais': len(df_original),
            'registros_convertidos': len(df_convertido),
            'registros_validos': len(df_convertido[df_convertido['valor'] > 0]),
            'valor_total': df_convertido['valor'].sum(),
            'empresas_unicas': df_convertido['empresa'].nunique(),
            'periodo_vencimentos': {
                'inicio': df_convertido['data_vencimento'].min(),
                'fim': df_convertido['data_vencimento'].max()
            },
            'categorias_encontradas': df_convertido['categoria'].value_counts().to_dict(),
            'data_conversao': datetime.now()
        }
        
        return relatorio
    
    def processar_arquivo_completo(self, arquivo_path: str, 
                                 salvar_convertido: bool = True) -> Dict:
        """
        Processa um arquivo completo do cliente.
        
        Args:
            arquivo_path: Caminho para o arquivo
            salvar_convertido: Se deve salvar o arquivo convertido
            
        Returns:
            Dicionário com resultado do processamento
        """
        resultado = {
            'sucesso': False,
            'arquivo_original': arquivo_path,
            'arquivo_convertido': None,
            'dados_convertidos': None,
            'relatorio': None,
            'erro': None
        }
        
        try:
            # Verificar se é formato do cliente
            if not self.detectar_formato_cliente(arquivo_path):
                resultado['erro'] = "Arquivo não está no formato esperado do cliente"
                return resultado
            
            # Converter arquivo
            df_convertido = self.converter_arquivo_cliente(arquivo_path)
            if df_convertido is None:
                resultado['erro'] = "Falha na conversão do arquivo"
                return resultado
            
            resultado['dados_convertidos'] = df_convertido
            
            # Salvar arquivo convertido se solicitado
            if salvar_convertido:
                arquivo_convertido = self.salvar_arquivo_convertido(df_convertido, arquivo_path)
                resultado['arquivo_convertido'] = arquivo_convertido
            
            # Gerar relatório
            df_original = pd.read_excel(arquivo_path)
            resultado['relatorio'] = self.gerar_relatorio_conversao(df_original, df_convertido)
            
            resultado['sucesso'] = True
            logger.info(f"Processamento concluído com sucesso: {arquivo_path}")
            
        except Exception as e:
            resultado['erro'] = str(e)
            logger.error(f"Erro no processamento completo: {str(e)}")
        
        return resultado
    
    # === MÉTODOS PARA CONTAS PAGAS ===
    
    def detectar_formato_modelo_contas_pagas(self, arquivo_path: str) -> bool:
        """
        Detecta se o arquivo é do formato Modelo_Contas_Pagas.
        
        Args:
            arquivo_path: Caminho para o arquivo
            
        Returns:
            bool: True se for formato Modelo_Contas_Pagas
        """
        return self.conversor_contas_pagas.detectar_formato_modelo_contas_pagas(arquivo_path)
    
    def converter_modelo_contas_pagas(self, arquivo_path: str) -> Optional[pd.DataFrame]:
        """
        Converte arquivo Modelo_Contas_Pagas.xlsx para o formato do banco.
        
        Args:
            arquivo_path: Caminho para o arquivo
            
        Returns:
            DataFrame convertido ou None se houver erro
        """
        return self.conversor_contas_pagas.converter_modelo_contas_pagas(arquivo_path)
    
    def processar_contas_pagas_completo(self, arquivo_path: str, salvar_convertido: bool = True) -> Dict[str, any]:
        """
        Processa arquivo completo de contas pagas com detalhes.
        
        Args:
            arquivo_path: Caminho para o arquivo
            salvar_convertido: Se deve salvar arquivo convertido
            
        Returns:
            Dict com resultado do processamento
        """
        resultado = {
            'sucesso': False,
            'dados_convertidos': pd.DataFrame(),
            'arquivo_convertido': None,
            'relatorio': {},
            'erro': None
        }
        
        try:
            logger.info(f"Iniciando processamento de contas pagas: {arquivo_path}")
            
            # Detectar e converter
            if self.detectar_formato_modelo_contas_pagas(arquivo_path):
                df_convertido = self.converter_modelo_contas_pagas(arquivo_path)
                
                if df_convertido is not None and not df_convertido.empty:
                    resultado['dados_convertidos'] = df_convertido
                    
                    # Salvar arquivo convertido se solicitado
                    if salvar_convertido:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        nome_base = os.path.splitext(os.path.basename(arquivo_path))[0]
                        arquivo_convertido = f"data/contas_pagas/{nome_base}_convertido_{timestamp}.xlsx"
                        
                        # Criar diretório se não existir
                        os.makedirs(os.path.dirname(arquivo_convertido), exist_ok=True)
                        
                        df_convertido.to_excel(arquivo_convertido, index=False)
                        resultado['arquivo_convertido'] = arquivo_convertido
                        logger.info(f"Arquivo convertido salvo: {arquivo_convertido}")
                    
                    # Gerar relatório
                    df_original = pd.read_excel(arquivo_path)
                    resultado['relatorio'] = {
                        'registros_original': len(df_original),
                        'registros_convertidos': len(df_convertido),
                        'colunas_original': list(df_original.columns),
                        'colunas_convertidas': list(df_convertido.columns),
                        'tipo_conversao': 'Modelo_Contas_Pagas'
                    }
                    
                    resultado['sucesso'] = True
                    logger.info(f"Processamento de contas pagas concluído: {arquivo_path}")
                else:
                    resultado['erro'] = "Nenhum dado foi convertido"
            else:
                resultado['erro'] = "Formato não reconhecido como Modelo_Contas_Pagas"
                
        except Exception as e:
            resultado['erro'] = str(e)
            logger.error(f"Erro no processamento de contas pagas: {str(e)}")
        
        return resultado
