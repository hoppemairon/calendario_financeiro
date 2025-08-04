"""
Módulo para análise e comparação de pagamentos.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class PaymentAnalyzer:
    """Classe para análise e comparação de contas a pagar vs contas pagas."""
    
    def __init__(self):
        self.tolerancia_valor = 0.01  # Tolerância para diferenças de valor (R$ 0,01)
        self.tolerancia_dias = 7      # Tolerância em dias para considerar o mesmo pagamento
    
    def criar_chave_comparacao(self, df: pd.DataFrame, tipo: str) -> pd.DataFrame:
        """
        Cria uma chave única para comparação entre contas a pagar e pagas.
        
        Args:
            df: DataFrame com os dados
            tipo: 'a_pagar' ou 'pagas'
            
        Returns:
            DataFrame com chave de comparação
        """
        if df.empty:
            return df
        
        print(f"🔍 Processando DataFrame tipo '{tipo}' com {len(df)} registros")
        print(f"📋 Colunas disponíveis: {list(df.columns)}")
        
        df = df.copy()
        
        # Verificar e garantir que as colunas necessárias existam
        colunas_obrigatorias = ['empresa', 'descricao', 'valor']
        colunas_faltando = [col for col in colunas_obrigatorias if col not in df.columns]
        
        if colunas_faltando:
            print(f"⚠️ Colunas faltando no DataFrame: {colunas_faltando}")
            print(f"📋 Colunas disponíveis: {list(df.columns)}")
            
            # Tentar mapear colunas similares
            for col in colunas_faltando:
                if col == 'empresa':
                    # Procurar colunas similares
                    colunas_similares = [c for c in df.columns if 'empresa' in c.lower()]
                    if not colunas_similares:
                        df['empresa'] = 'Não informado'
                    else:
                        df['empresa'] = df[colunas_similares[0]]
                        
                elif col == 'descricao':
                    colunas_similares = [c for c in df.columns if 'descri' in c.lower()]
                    if not colunas_similares:
                        df['descricao'] = 'Não informado'
                    else:
                        df['descricao'] = df[colunas_similares[0]]
                        
                elif col == 'valor':
                    colunas_similares = [c for c in df.columns if 'valor' in c.lower()]
                    if not colunas_similares:
                        df['valor'] = 0.0
                    else:
                        df['valor'] = df[colunas_similares[0]]
        
        # Normalizar empresa e descrição para comparação
        df['empresa_norm'] = df['empresa'].astype(str).str.upper().str.strip()
        df['descricao_norm'] = df['descricao'].astype(str).str.upper().str.strip()
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0.0)
        
        # Criar chave de comparação
        try:
            df['chave_comparacao'] = (
                df['empresa_norm'].astype(str) + "_" + 
                df['descricao_norm'].astype(str) + "_" + 
                df['valor'].round(2).astype(str)
            )
            
            print(f"✅ Chave de comparação criada para {len(df)} registros")
            print(f"📋 Colunas finais: {list(df.columns)}")
            
            # Verificar se a chave foi criada corretamente
            if 'chave_comparacao' not in df.columns:
                raise ValueError("Falha ao criar coluna chave_comparacao")
                
            # Verificar se há valores nulos na chave
            chaves_nulas = df['chave_comparacao'].isna().sum()
            if chaves_nulas > 0:
                print(f"⚠️ {chaves_nulas} chaves de comparação são nulas")
            
            return df
            
        except Exception as e:
            print(f"❌ Erro ao criar chave de comparação: {str(e)}")
            # Retornar DataFrame original se falhar
            return df
    
    def encontrar_correspondencias(self, df_a_pagar: pd.DataFrame, df_pagas: pd.DataFrame) -> Dict:
        """
        Encontra correspondências entre contas a pagar e contas pagas.
        
        Args:
            df_a_pagar: DataFrame com contas a pagar
            df_pagas: DataFrame with contas pagas
            
        Returns:
            Dicionário com correspondências encontradas
        """
        # Verificar se os DataFrames estão vazios
        if df_a_pagar.empty and df_pagas.empty:
            return {
                'exatas': [],
                'aproximadas': [],
                'nao_encontradas': [],
                'pagas_nao_encontradas': []
            }
        
        # Preparar dados para comparação
        try:
            df_a_pagar_processado = self.criar_chave_comparacao(df_a_pagar, 'a_pagar')
            df_pagas_processado = self.criar_chave_comparacao(df_pagas, 'pagas')
            
            # Verificar se as chaves foram criadas com sucesso
            if 'chave_comparacao' not in df_a_pagar_processado.columns:
                print(f"⚠️ Chave de comparação não foi criada para contas a pagar. Usando comparação simples.")
                # Retornar resultado vazio mas válido
                return {
                    'exatas': [],
                    'aproximadas': [],
                    'nao_encontradas': [],
                    'pagas_nao_encontradas': []
                }
            
            if 'chave_comparacao' not in df_pagas_processado.columns:
                print(f"⚠️ Chave de comparação não foi criada para contas pagas. Usando comparação simples.")
                # Se não há contas pagas, todas as contas a pagar são não encontradas
                return {
                    'exatas': [],
                    'aproximadas': [],
                    'nao_encontradas': df_a_pagar_processado.to_dict('records'),
                    'pagas_nao_encontradas': []
                }
                
            df_a_pagar = df_a_pagar_processado
            df_pagas = df_pagas_processado
            
        except Exception as e:
            print(f"❌ Erro ao criar chaves de comparação: {e}")
            # Retornar dados básicos sem comparação
            return {
                'exatas': [],
                'aproximadas': [],
                'nao_encontradas': df_a_pagar.to_dict('records') if not df_a_pagar.empty else [],
                'pagas_nao_encontradas': df_pagas.to_dict('records') if not df_pagas.empty else []
            }
        
        correspondencias = {
            'exatas': [],
            'aproximadas': [],
            'nao_encontradas': [],
            'pagamentos_extras': []
        }
        
        df_pagas_restantes = df_pagas.copy()
        
        # Buscar correspondências exatas
        for idx_pagar, conta_pagar in df_a_pagar.iterrows():
            correspondencia_exata = df_pagas_restantes[
                df_pagas_restantes['chave_comparacao'] == conta_pagar['chave_comparacao']
            ]
            
            if not correspondencia_exata.empty:
                # Pegar a primeira correspondência
                conta_paga = correspondencia_exata.iloc[0]
                
                correspondencias['exatas'].append({
                    'conta_a_pagar': conta_pagar.to_dict(),
                    'conta_paga': conta_paga.to_dict(),
                    'diferenca_dias': (conta_paga['data_pagamento'] - conta_pagar['data_vencimento']).days,
                    'diferenca_valor': conta_paga['valor'] - conta_pagar['valor']
                })
                
                # Remover da lista de contas pagas restantes
                df_pagas_restantes = df_pagas_restantes.drop(conta_paga.name)
                continue
            
            # Buscar correspondências aproximadas (mesma empresa e valor similar)
            correspondencia_aproximada = df_pagas_restantes[
                (df_pagas_restantes['empresa_norm'] == conta_pagar['empresa_norm']) &
                (abs(df_pagas_restantes['valor'] - conta_pagar['valor']) <= self.tolerancia_valor)
            ]
            
            if not correspondencia_aproximada.empty:
                # Pegar a correspondência mais próxima em data
                if 'data_vencimento' in conta_pagar and pd.notna(conta_pagar['data_vencimento']):
                    correspondencia_aproximada['diff_dias'] = abs(
                        (correspondencia_aproximada['data_pagamento'] - conta_pagar['data_vencimento']).dt.days
                    )
                    conta_paga = correspondencia_aproximada.loc[correspondencia_aproximada['diff_dias'].idxmin()]
                else:
                    conta_paga = correspondencia_aproximada.iloc[0]
                
                correspondencias['aproximadas'].append({
                    'conta_a_pagar': conta_pagar.to_dict(),
                    'conta_paga': conta_paga.to_dict(),
                    'diferenca_dias': (conta_paga['data_pagamento'] - conta_pagar['data_vencimento']).days if pd.notna(conta_pagar['data_vencimento']) else None,
                    'diferenca_valor': conta_paga['valor'] - conta_pagar['valor'],
                    'motivo_aproximacao': 'empresa_valor_similar'
                })
                
                # Remover da lista de contas pagas restantes
                df_pagas_restantes = df_pagas_restantes.drop(conta_paga.name)
                continue
            
            # Não encontrou correspondência
            correspondencias['nao_encontradas'].append(conta_pagar.to_dict())
        
        # Pagamentos extras (não encontrados nas contas a pagar)
        correspondencias['pagamentos_extras'] = df_pagas_restantes.to_dict('records')
        
        return correspondencias
    
    def calcular_resumo_financeiro(self, correspondencias: Dict) -> Dict:
        """
        Calcula resumo financeiro das correspondências.
        
        Args:
            correspondencias: Resultado do método encontrar_correspondencias
            
        Returns:
            Dicionário com resumo financeiro
        """
        resumo = {
            'total_a_pagar': 0,
            'total_pago': 0,
            'total_pendente': 0,
            'total_extra': 0,
            'quantidade_exatas': len(correspondencias['exatas']),
            'quantidade_aproximadas': len(correspondencias['aproximadas']),
            'quantidade_pendentes': len(correspondencias['nao_encontradas']),
            'quantidade_extras': len(correspondencias['pagamentos_extras'])
        }
        
        # Calcular totais de correspondências exatas
        for corresp in correspondencias['exatas']:
            resumo['total_a_pagar'] += corresp['conta_a_pagar']['valor']
            resumo['total_pago'] += corresp['conta_paga']['valor']
        
        # Calcular totais de correspondências aproximadas
        for corresp in correspondencias['aproximadas']:
            resumo['total_a_pagar'] += corresp['conta_a_pagar']['valor']
            resumo['total_pago'] += corresp['conta_paga']['valor']
        
        # Calcular total pendente
        for conta in correspondencias['nao_encontradas']:
            resumo['total_pendente'] += conta['valor']
        
        # Calcular total extra
        for conta in correspondencias['pagamentos_extras']:
            resumo['total_extra'] += conta['valor']
        
        # Calcular diferenças
        resumo['diferenca_valor'] = resumo['total_pago'] - resumo['total_a_pagar']
        resumo['percentual_pago'] = (resumo['total_pago'] / (resumo['total_a_pagar'] + resumo['total_pendente']) * 100) if (resumo['total_a_pagar'] + resumo['total_pendente']) > 0 else 0
        
        return resumo
    
    def gerar_relatorio_por_empresa(self, correspondencias: Dict) -> pd.DataFrame:
        """
        Gera relatório resumido por empresa.
        
        Args:
            correspondencias: Resultado do método encontrar_correspondencias
            
        Returns:
            DataFrame com resumo por empresa
        """
        dados_empresa = {}
        
        # Processar correspondências exatas e aproximadas
        for tipo in ['exatas', 'aproximadas']:
            for corresp in correspondencias[tipo]:
                empresa = corresp['conta_a_pagar']['empresa']
                
                if empresa not in dados_empresa:
                    dados_empresa[empresa] = {
                        'empresa': empresa,
                        'valor_a_pagar': 0,
                        'valor_pago': 0,
                        'quantidade_a_pagar': 0,
                        'quantidade_pago': 0,
                        'valor_pendente': 0,
                        'quantidade_pendente': 0
                    }
                
                dados_empresa[empresa]['valor_a_pagar'] += corresp['conta_a_pagar']['valor']
                dados_empresa[empresa]['valor_pago'] += corresp['conta_paga']['valor']
                dados_empresa[empresa]['quantidade_a_pagar'] += 1
                dados_empresa[empresa]['quantidade_pago'] += 1
        
        # Processar contas não encontradas (pendentes)
        for conta in correspondencias['nao_encontradas']:
            empresa = conta['empresa']
            
            if empresa not in dados_empresa:
                dados_empresa[empresa] = {
                    'empresa': empresa,
                    'valor_a_pagar': 0,
                    'valor_pago': 0,
                    'quantidade_a_pagar': 0,
                    'quantidade_pago': 0,
                    'valor_pendente': 0,
                    'quantidade_pendente': 0
                }
            
            dados_empresa[empresa]['valor_a_pagar'] += conta['valor']
            dados_empresa[empresa]['valor_pendente'] += conta['valor']
            dados_empresa[empresa]['quantidade_a_pagar'] += 1
            dados_empresa[empresa]['quantidade_pendente'] += 1
        
        # Converter para DataFrame
        df_resumo = pd.DataFrame(list(dados_empresa.values()))
        
        if not df_resumo.empty:
            # Calcular percentuais e diferenças
            df_resumo['diferenca_valor'] = df_resumo['valor_pago'] - (df_resumo['valor_a_pagar'] - df_resumo['valor_pendente'])
            df_resumo['percentual_pago'] = (df_resumo['valor_pago'] / df_resumo['valor_a_pagar'] * 100).round(2)
            df_resumo['percentual_pendente'] = (df_resumo['valor_pendente'] / df_resumo['valor_a_pagar'] * 100).round(2)
            
            # Ordenar por valor a pagar (decrescente)
            df_resumo = df_resumo.sort_values('valor_a_pagar', ascending=False)
        
        return df_resumo
    
    def identificar_atrasos(self, correspondencias: Dict, data_referencia: datetime = None) -> List[Dict]:
        """
        Identifica pagamentos em atraso ou contas vencidas não pagas.
        
        Args:
            correspondencias: Resultado do método encontrar_correspondencias
            data_referencia: Data de referência para calcular atrasos (padrão: hoje)
            
        Returns:
            Lista com informações de atrasos
        """
        if data_referencia is None:
            data_referencia = datetime.now()
        
        atrasos = []
        
        # Verificar correspondências exatas e aproximadas com atraso
        for tipo in ['exatas', 'aproximadas']:
            for corresp in correspondencias[tipo]:
                conta_pagar = corresp['conta_a_pagar']
                conta_paga = corresp['conta_paga']
                
                if pd.notna(conta_pagar['data_vencimento']):
                    dias_atraso = (conta_paga['data_pagamento'] - conta_pagar['data_vencimento']).days
                    
                    if dias_atraso > 0:  # Pagamento em atraso
                        atrasos.append({
                            'tipo': 'pagamento_atrasado',
                            'empresa': conta_pagar['empresa'],
                            'descricao': conta_pagar['descricao'],
                            'valor': conta_pagar['valor'],
                            'data_vencimento': conta_pagar['data_vencimento'],
                            'data_pagamento': conta_paga['data_pagamento'],
                            'dias_atraso': dias_atraso,
                            'correspondencia_tipo': tipo
                        })
        
        # Verificar contas vencidas não pagas
        for conta in correspondencias['nao_encontradas']:
            if pd.notna(conta['data_vencimento']):
                dias_vencido = (data_referencia - conta['data_vencimento']).days
                
                if dias_vencido > 0:  # Conta vencida
                    atrasos.append({
                        'tipo': 'conta_vencida_nao_paga',
                        'empresa': conta['empresa'],
                        'descricao': conta['descricao'],
                        'valor': conta['valor'],
                        'data_vencimento': conta['data_vencimento'],
                        'data_pagamento': None,
                        'dias_vencido': dias_vencido,
                        'correspondencia_tipo': 'nao_encontrada'
                    })
        
        return atrasos
