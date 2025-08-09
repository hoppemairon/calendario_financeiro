"""
Módulo para validação e processamento de modelos de contas pagas.
"""

import pandas as pd
import streamlit as st
from typing import Dict
import uuid


class ContasPagasValidator:
    """Validador para diferentes formatos de contas pagas."""
    
    def __init__(self):
        self.colunas_padrao = {
            'data_pagamento': 'data_pagamento',
            'empresa': 'empresa', 
            'fornecedor': 'fornecedor',
            'valor': 'valor',
            'descricao': 'descricao',
            'categoria': 'categoria',
            'historico': 'historico'
        }
        
        # Mapeamentos para o novo modelo
        self.mapeamento_novo_modelo = {
            'IdBanco': 'empresa',
            'Datapagamento': 'data_pagamento',
            'DescriçãoConta': 'descricao',
            'Saída': 'valor',
            'Histórico': 'historico',
            'Campo54': 'id_movimento'
        }
    
    def detectar_formato(self, df: pd.DataFrame) -> str:
        """
        Detecta o formato do arquivo de contas pagas.
        """
        colunas = set(df.columns)
        
        # Verificar se é o novo modelo com IdBanco, Datapagamento, etc
        if 'IdBanco' in colunas and 'Datapagamento' in colunas and 'Saída' in colunas:
            return 'novo_modelo'
        
        # Verificar se é formato padrão com data_pagamento, valor, etc
        if 'data_pagamento' in colunas and 'valor' in colunas:
            return 'padrao'
        
        # Verificar se tem colunas similares ao a pagar (que podem ser adaptadas)
        if 'DataVencimento' in colunas and 'ValorDoc' in colunas:
            return 'formato_a_pagar'
        
        return 'desconhecido'
    
    def validar_colunas_obrigatorias(self, df: pd.DataFrame, formato: str) -> Dict:
        """
        Valida se as colunas obrigatórias estão presentes.
        """
        resultado = {
            'valido': False,
            'colunas_faltando': [],
            'colunas_encontradas': [],
            'warnings': []
        }
        
        if formato == 'novo_modelo':
            colunas_obrigatorias = ['IdBanco', 'Datapagamento', 'Saída']
            colunas_opcionais = ['DescriçãoConta', 'Histórico', 'Entrada']
            
        elif formato == 'padrao':
            colunas_obrigatorias = ['data_pagamento', 'valor']
            colunas_opcionais = ['empresa', 'fornecedor', 'descricao']
            
        else:
            resultado['warnings'].append(f'Formato {formato} não suportado')
            return resultado
        
        # Verificar colunas obrigatórias
        for coluna in colunas_obrigatorias:
            if coluna in df.columns:
                resultado['colunas_encontradas'].append(coluna)
            else:
                resultado['colunas_faltando'].append(coluna)
        
        # Verificar colunas opcionais
        for coluna in colunas_opcionais:
            if coluna in df.columns:
                resultado['colunas_encontradas'].append(f'{coluna} (opcional)')
        
        resultado['valido'] = len(resultado['colunas_faltando']) == 0
        
        return resultado
    
    def converter_novo_modelo(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Converte o novo modelo para o formato padrão.
        """
        try:
            df_convertido = pd.DataFrame()
            
            # Mapeamento direto das colunas
            if 'IdBanco' in df.columns:
                df_convertido['empresa'] = df['IdBanco'].astype(str)
            
            if 'Datapagamento' in df.columns:
                df_convertido['data_pagamento'] = pd.to_datetime(df['Datapagamento'], errors='coerce')
            
            if 'DescriçãoConta' in df.columns:
                df_convertido['descricao'] = df['DescriçãoConta'].astype(str)
            
            # Para fornecedor, vamos tentar extrair do histórico ou usar empresa
            if 'Histórico' in df.columns:
                df_convertido['historico'] = df['Histórico'].astype(str)
                # Tentar extrair fornecedor do histórico
                df_convertido['fornecedor'] = df['Histórico'].astype(str)
            else:
                df_convertido['fornecedor'] = df_convertido['empresa'] if 'empresa' in df_convertido.columns else 'N/I'
            
            # Valor - usar Saída (que são os pagamentos)
            if 'Saída' in df.columns:
                df_convertido['valor'] = pd.to_numeric(df['Saída'], errors='coerce')
                # Filtrar apenas valores positivos (saídas reais)
                df_convertido = df_convertido[df_convertido['valor'] > 0]
            
            # Categoria baseada na descrição
            if 'DescriçãoConta' in df.columns:
                df_convertido['categoria'] = self._categorizar_automaticamente(df['DescriçãoConta'])
            
            # Campos adicionais
            if 'Campo54' in df.columns:
                df_convertido['id_movimento'] = df['Campo54']
            
            if 'NúmeroCheque' in df.columns:
                df_convertido['numero_cheque'] = df['NúmeroCheque']
            
            # Adicionar campos de controle
            df_convertido['arquivo_origem'] = 'novo_modelo_contas_pagas'
            df_convertido['processamento_id'] = str(uuid.uuid4())
            
            return df_convertido
            
        except (ValueError, KeyError, pd.errors.ParserError) as e:
            st.error(f"Erro ao converter novo modelo: {str(e)}")
            return pd.DataFrame()
    
    def _categorizar_automaticamente(self, descricoes: pd.Series) -> pd.Series:
        """
        Categoriza automaticamente baseado na descrição.
        """
        def categorizar(descricao):
            if pd.isna(descricao):
                return 'OUTROS'
            
            descricao = str(descricao).upper()
            
            # Mapeamento de palavras-chave para categorias
            if any(palavra in descricao for palavra in ['TARIFA', 'TAXA', 'ANUIDADE']):
                return 'TARIFAS BANCÁRIAS'
            elif any(palavra in descricao for palavra in ['COMPRAS', 'FORNECEDOR', 'MATERIAL']):
                return 'COMPRAS/FORNECEDORES'
            elif any(palavra in descricao for palavra in ['FOLHA', 'SALÁRIO', 'FUNCIONÁRIO']):
                return 'PESSOAL'
            elif any(palavra in descricao for palavra in ['LUZ', 'ÁGUA', 'TELEFONE', 'INTERNET']):
                return 'UTILIDADES'
            elif any(palavra in descricao for palavra in ['ALUGUEL', 'IMÓVEL']):
                return 'IMÓVEIS'
            elif any(palavra in descricao for palavra in ['EMPRÉSTIMO', 'FINANCIAMENTO']):
                return 'FINANCIAMENTOS'
            else:
                return 'OUTROS'
        
        return descricoes.apply(categorizar)
    
    def validar_dados_convertidos(self, df: pd.DataFrame) -> Dict:
        """
        Valida os dados após conversão.
        """
        resultado = {
            'valido': True,
            'total_registros': len(df),
            'registros_validos': 0,
            'problemas': [],
            'warnings': [],
            'estatisticas': {}
        }
        
        if df.empty:
            resultado['valido'] = False
            resultado['problemas'].append('Nenhum registro encontrado após conversão')
            return resultado
        
        # Validar datas
        datas_invalidas = df['data_pagamento'].isna().sum()
        if datas_invalidas > 0:
            resultado['warnings'].append(f'{datas_invalidas} datas inválidas encontradas')
        
        # Validar valores
        valores_invalidos = df['valor'].isna().sum()
        valores_zerados = (df['valor'] <= 0).sum()
        
        if valores_invalidos > 0:
            resultado['warnings'].append(f'{valores_invalidos} valores inválidos encontradas')
        
        if valores_zerados > 0:
            resultado['warnings'].append(f'{valores_zerados} valores zerados ou negativos encontrados')
        
        # Estatísticas gerais
        resultado['registros_validos'] = len(df) - datas_invalidas - valores_invalidos - valores_zerados
        resultado['estatisticas'] = {
            'valor_total': df['valor'].sum(),
            'valor_medio': df['valor'].mean(),
            'periodo': {
                'inicio': df['data_pagamento'].min(),
                'fim': df['data_pagamento'].max()
            },
            'empresas_unicas': df['empresa'].nunique() if 'empresa' in df.columns else 0,
            'categorias': df['categoria'].value_counts().to_dict() if 'categoria' in df.columns else {}
        }
        
        if resultado['registros_validos'] < resultado['total_registros'] * 0.5:
            resultado['valido'] = False
            resultado['problemas'].append('Mais de 50% dos registros têm problemas')
        
        return resultado


class ComparadorContasAPagarVsPagas:
    """
    Compara contas a pagar com contas pagas para identificar inconsistências.
    """
    
    def __init__(self):
        self.tolerancia_valor = 0.01  # R$ 0,01 de tolerância
        self.tolerancia_dias = 30     # 30 dias de tolerância na data
    
    def comparar_datasets(self, df_a_pagar: pd.DataFrame, df_pagas: pd.DataFrame) -> Dict:
        """
        Compara os dois datasets e identifica diferenças.
        """
        resultado = {
            'resumo': {},
            'correspondencias_exatas': pd.DataFrame(),
            'correspondencias_aproximadas': pd.DataFrame(),
            'contas_nao_pagas': pd.DataFrame(),
            'pagamentos_sem_conta': pd.DataFrame(),
            'diferencas_valor': pd.DataFrame(),
            'diferencas_prazo': pd.DataFrame()
        }
        
        # Estatísticas básicas
        resultado['resumo'] = {
            'total_a_pagar': len(df_a_pagar),
            'total_pagas': len(df_pagas),
            'valor_total_a_pagar': df_a_pagar['valor'].sum() if not df_a_pagar.empty and 'valor' in df_a_pagar.columns else 0,
            'valor_total_pago': df_pagas['valor'].sum() if not df_pagas.empty and 'valor' in df_pagas.columns else 0
        }
        
        if df_a_pagar.empty or df_pagas.empty:
            resultado['resumo']['status'] = 'Um dos datasets está vazio'
            return resultado
        
        # Preparar dados para comparação
        try:
            df_a_pagar_prep = self._preparar_dataset_comparacao(df_a_pagar, 'a_pagar')
            df_pagas_prep = self._preparar_dataset_comparacao(df_pagas, 'pagas')
        except (ValueError, KeyError) as e:
            print(f"❌ Erro ao preparar datasets: {str(e)}")
            resultado['resumo']['status'] = f'Erro na preparação: {str(e)}'
            return resultado
        
        # Verificar se as chaves foram criadas
        if 'chave_comparacao' not in df_a_pagar_prep.columns:
            print("⚠️ Chave de comparação não foi criada para contas a pagar. Usando comparação simples.")
            
        if 'chave_comparacao' not in df_pagas_prep.columns:
            print("⚠️ Chave de comparação não foi criada para contas pagas. Usando comparação simples.")
        
        # Encontrar correspondências exatas
        resultado['correspondencias_exatas'] = self._encontrar_correspondencias_exatas(
            df_a_pagar_prep, df_pagas_prep
        )
        
        # Encontrar correspondências aproximadas
        resultado['correspondencias_aproximadas'] = self._encontrar_correspondencias_aproximadas(
            df_a_pagar_prep, df_pagas_prep, resultado['correspondencias_exatas']
        )
        
        # Identificar contas não pagas
        resultado['contas_nao_pagas'] = self._identificar_contas_nao_pagas(
            df_a_pagar_prep, resultado['correspondencias_exatas'], resultado['correspondencias_aproximadas']
        )
        
        # Identificar pagamentos sem conta correspondente
        resultado['pagamentos_sem_conta'] = self._identificar_pagamentos_sem_conta(
            df_pagas_prep, resultado['correspondencias_exatas'], resultado['correspondencias_aproximadas']
        )
        
        # Analisar diferenças de valor
        resultado['diferencas_valor'] = self._analisar_diferencas_valor(
            resultado['correspondencias_exatas'], resultado['correspondencias_aproximadas']
        )
        
        # Analisar diferenças de prazo
        resultado['diferencas_prazo'] = self._analisar_diferencas_prazo(
            resultado['correspondencias_exatas'], resultado['correspondencias_aproximadas']
        )
        
        # Atualizar resumo
        resultado['resumo'].update({
            'correspondencias_exatas': len(resultado['correspondencias_exatas']),
            'correspondencias_aproximadas': len(resultado['correspondencias_aproximadas']),
            'contas_nao_pagas': len(resultado['contas_nao_pagas']),
            'pagamentos_sem_conta': len(resultado['pagamentos_sem_conta']),
            'diferencas_valor': len(resultado['diferencas_valor']),
            'diferencas_prazo': len(resultado['diferencas_prazo'])
        })
        
        return resultado
    
    def _preparar_dataset_comparacao(self, df: pd.DataFrame, tipo: str) -> pd.DataFrame:
        """
        Prepara dataset para comparação adicionando chaves normalizadas.
        """
        print(f"🔍 Processando DataFrame tipo '{tipo}' com {len(df)} registros")
        print(f"📋 Colunas disponíveis: {list(df.columns)}")
        
        df_prep = df.copy()
        
        # Normalizar nomes das colunas primeiro
        df_prep.columns = [col.lower().replace(' ', '_') for col in df_prep.columns]
        
        # Mapear colunas específicas do modelo de contas a pagar
        if tipo == 'a_pagar':
            column_mapping = {
                'empresa': 'empresa',
                'fornecedor': 'fornecedor',
                'valordoc': 'valor',
                'descriçãoconta': 'descricao',
                'datavencimento': 'data_vencimento',
                'histórico': 'historico'
            }
            
            # Renomear colunas se existirem
            for old_name, new_name in column_mapping.items():
                if old_name in df_prep.columns:
                    df_prep = df_prep.rename(columns={old_name: new_name})
        
        # Verificar se as colunas necessárias existem
        if 'empresa' not in df_prep.columns:
            print("⚠️ Coluna 'empresa' não encontrada")
            return df_prep
            
        if 'valor' not in df_prep.columns:
            print("⚠️ Coluna 'valor' não encontrada")
            return df_prep
        
        # Normalizar strings para comparação
        df_prep['empresa_norm'] = df_prep['empresa'].astype(str).str.upper().str.strip()
        
        if 'fornecedor' in df_prep.columns:
            df_prep['fornecedor_norm'] = df_prep['fornecedor'].astype(str).str.upper().str.strip()
        else:
            df_prep['fornecedor_norm'] = ''
            
        if 'descricao' in df_prep.columns:
            df_prep['descricao_norm'] = df_prep['descricao'].astype(str).str.upper().str.strip()
        else:
            df_prep['descricao_norm'] = ''
        
        # Criar chave de comparação
        try:
            df_prep['chave_comparacao'] = (
                df_prep['empresa_norm'] + '_' + 
                df_prep['fornecedor_norm'] + '_' + 
                df_prep['valor'].round(2).astype(str)
            )
            print(f"✅ Chave de comparação criada para {len(df_prep)} registros")
        except (ValueError, KeyError) as e:
            print(f"⚠️ Erro ao criar chave de comparação: {str(e)}")
            return df_prep
        
        df_prep['tipo'] = tipo
        
        print(f"📋 Colunas finais: {list(df_prep.columns)}")
        return df_prep
    
    def _encontrar_correspondencias_exatas(self, df_a_pagar: pd.DataFrame, df_pagas: pd.DataFrame) -> pd.DataFrame:
        """
        Encontra correspondências exatas entre os datasets.
        """
        # Merge baseado na chave de comparação
        correspondencias = pd.merge(
            df_a_pagar, df_pagas, 
            on='chave_comparacao', 
            suffixes=('_a_pagar', '_pagas'),
            how='inner'
        )
        
        return correspondencias
    
    def _encontrar_correspondencias_aproximadas(self, df_a_pagar: pd.DataFrame, df_pagas: pd.DataFrame, 
                                              correspondencias_exatas: pd.DataFrame) -> pd.DataFrame:
        """
        Encontra correspondências aproximadas (valores similares, empresas iguais).
        """
        # Remover itens já encontrados nas correspondências exatas
        chaves_exatas = set(correspondencias_exatas['chave_comparacao'].unique()) if not correspondencias_exatas.empty else set()
        
        df_a_pagar_restante = df_a_pagar[~df_a_pagar['chave_comparacao'].isin(chaves_exatas)]
        df_pagas_restante = df_pagas[~df_pagas['chave_comparacao'].isin(chaves_exatas)]
        
        correspondencias_aprox = []
        
        for _, conta_pagar in df_a_pagar_restante.iterrows():
            # Buscar pagamentos da mesma empresa com valor similar
            candidatos = df_pagas_restante[
                (df_pagas_restante['empresa_norm'] == conta_pagar['empresa_norm']) &
                (abs(df_pagas_restante['valor'] - conta_pagar['valor']) <= self.tolerancia_valor)
            ]
            
            if not candidatos.empty:
                # Pegar o candidato mais próximo por valor
                melhor_candidato = candidatos.iloc[
                    (candidatos['valor'] - conta_pagar['valor']).abs().argmin()
                ]
                
                correspondencias_aprox.append({
                    'id_a_pagar': conta_pagar.get('id', ''),
                    'id_pagas': melhor_candidato.get('id', ''),
                    'empresa_a_pagar': conta_pagar['empresa'],
                    'empresa_pagas': melhor_candidato['empresa'],
                    'valor_a_pagar': conta_pagar['valor'],
                    'valor_pagas': melhor_candidato['valor'],
                    'diferenca_valor': melhor_candidato['valor'] - conta_pagar['valor'],
                    'data_vencimento': conta_pagar.get('data_vencimento'),
                    'data_pagamento': melhor_candidato.get('data_pagamento'),
                    'fornecedor_a_pagar': conta_pagar.get('fornecedor', ''),
                    'fornecedor_pagas': melhor_candidato.get('fornecedor', ''),
                    'descricao_a_pagar': conta_pagar['descricao'],
                    'descricao_pagas': melhor_candidato['descricao']
                })
        
        return pd.DataFrame(correspondencias_aprox)
    
    def _identificar_contas_nao_pagas(self, df_a_pagar: pd.DataFrame, 
                                    correspondencias_exatas: pd.DataFrame,
                                    correspondencias_aproximadas: pd.DataFrame) -> pd.DataFrame:
        """
        Identifica contas a pagar que não têm correspondência nas contas pagas.
        """
        # IDs das contas que já têm correspondência
        ids_correspondidos = set()
        
        if not correspondencias_exatas.empty:
            ids_correspondidos.update(correspondencias_exatas['id_a_pagar'].dropna())
        
        if not correspondencias_aproximadas.empty:
            ids_correspondidos.update(correspondencias_aproximadas['id_a_pagar'].dropna())
        
        # Filtrar contas sem correspondência
        contas_nao_pagas = df_a_pagar[
            ~df_a_pagar.get('id', pd.Series(range(len(df_a_pagar)))).isin(ids_correspondidos)
        ].copy()
        
        return contas_nao_pagas
    
    def _identificar_pagamentos_sem_conta(self, df_pagas: pd.DataFrame,
                                        correspondencias_exatas: pd.DataFrame,
                                        correspondencias_aproximadas: pd.DataFrame) -> pd.DataFrame:
        """
        Identifica pagamentos que não têm correspondência nas contas a pagar.
        """
        # IDs dos pagamentos que já têm correspondência
        ids_correspondidos = set()
        
        if not correspondencias_exatas.empty:
            ids_correspondidos.update(correspondencias_exatas['id_pagas'].dropna())
        
        if not correspondencias_aproximadas.empty:
            ids_correspondidos.update(correspondencias_aproximadas['id_pagas'].dropna())
        
        # Filtrar pagamentos sem correspondência
        pagamentos_sem_conta = df_pagas[
            ~df_pagas.get('id', pd.Series(range(len(df_pagas)))).isin(ids_correspondidos)
        ].copy()
        
        return pagamentos_sem_conta
    
    def _analisar_diferencas_valor(self, correspondencias_exatas: pd.DataFrame,
                                 correspondencias_aproximadas: pd.DataFrame) -> pd.DataFrame:
        """
        Analisa diferenças significativas de valor.
        """
        diferencas = []
        
        # Verificar correspondências exatas com diferenças de valor significativas
        if not correspondencias_exatas.empty:
            for _, row in correspondencias_exatas.iterrows():
                if 'diferenca_valor' in row and abs(row.get('diferenca_valor', 0)) > self.tolerancia_valor:
                    diferencas.append(row)
        
        # Verificar correspondências aproximadas com diferenças de valor
        if not correspondencias_aproximadas.empty:
            for _, row in correspondencias_aproximadas.iterrows():
                if abs(row.get('diferenca_valor', 0)) > self.tolerancia_valor:
                    diferencas.append(row)
        
        return pd.DataFrame(diferencas)
    
    def _analisar_diferencas_prazo(self, correspondencias_exatas: pd.DataFrame,
                                 correspondencias_aproximadas: pd.DataFrame) -> pd.DataFrame:
        """
        Analisa diferenças de prazo entre vencimento e pagamento.
        """
        diferencas_prazo = []
        
        def analisar_correspondencias(df, tipo):
            for _, row in df.iterrows():
                if pd.notna(row.get('data_vencimento')) and pd.notna(row.get('data_pagamento')):
                    data_venc = pd.to_datetime(row['data_vencimento'])
                    data_pag = pd.to_datetime(row['data_pagamento'])
                    
                    diferenca_dias = (data_pag - data_venc).days
                    
                    if abs(diferenca_dias) > self.tolerancia_dias:
                        diferencas_prazo.append({
                            'tipo_correspondencia': tipo,
                            'empresa': row.get('empresa_a_pagar', row.get('empresa')),
                            'valor': row.get('valor_a_pagar', row.get('valor')),
                            'data_vencimento': data_venc,
                            'data_pagamento': data_pag,
                            'diferenca_dias': diferenca_dias,
                            'status_prazo': 'Antecipado' if diferenca_dias < 0 else 'Atrasado',
                            'descricao': row.get('descricao_a_pagar', row.get('descricao', ''))
                        })
        
        if not correspondencias_exatas.empty:
            analisar_correspondencias(correspondencias_exatas, 'Exata')
        
        if not correspondencias_aproximadas.empty:
            analisar_correspondencias(correspondencias_aproximadas, 'Aproximada')
        
        return pd.DataFrame(diferencas_prazo)
