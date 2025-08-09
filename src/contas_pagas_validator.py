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
                df_convertido['conta_corrente'] = df['IdBanco'].astype(str)
            
            if 'Datapagamento' in df.columns:
                df_convertido['data_pagamento'] = pd.to_datetime(df['Datapagamento'], errors='coerce')
            
            if 'Histórico' in df.columns:
                df_convertido['descricao'] = df['Histórico'].astype(str)
            
            if 'DescriçãoConta' in df.columns:
                df_convertido['categoria'] = df['DescriçãoConta'].astype(str)

            # Valor - usar Saída (que são os pagamentos)
            if 'Saída' in df.columns:
                df_convertido['valor'] = pd.to_numeric(df['Saída'], errors='coerce')
                # Filtrar apenas valores positivos (saídas reais)
                df_convertido = df_convertido[df_convertido['valor'] > 0]
            
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
            elif any(palavra in descricao for palavra in ['LUZ', 'ÁGUA', 'TELEFONE', 'INTERNET', 'ALUGUEL']):
                return 'ADMINISTRATIVO'
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
            'contas_correntes_unicas': df['conta_corrente'].nunique() if 'conta_corrente' in df.columns else 0,
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
        
        # Adicionar estatísticas específicas de correspondência por histórico
        resultado['resumo']['correspondencias_por_historico'] = len(
            resultado.get('correspondencias_por_historico', pd.DataFrame())
        )
        
        # Separar correspondências por tipo para relatório detalhado
        resultado['correspondencias_por_id'] = self._extrair_correspondencias_por_tipo(
            resultado['correspondencias_exatas'], 'id_movimento'
        )
        resultado['correspondencias_por_chave'] = self._extrair_correspondencias_por_tipo(
            resultado['correspondencias_exatas'], 'chave_comparacao'
        )
        resultado['correspondencias_por_historico'] = self._extrair_correspondencias_por_tipo(
            resultado['correspondencias_exatas'], 'historico_norm'
        )
        
        return resultado
    
    def _extrair_correspondencias_por_tipo(self, correspondencias: pd.DataFrame, tipo: str) -> pd.DataFrame:
        """
        Extrai correspondências de um tipo específico do DataFrame de correspondências.
        """
        if correspondencias.empty:
            return pd.DataFrame()
        
        if tipo == 'id_movimento':
            # Correspondências que têm ID válido em ambos os lados
            mask = (correspondencias.get('id_movimento_a_pagar', pd.Series()).notna() & 
                   correspondencias.get('id_movimento_pagas', pd.Series()).notna())
            return correspondencias[mask] if mask.any() else pd.DataFrame()
            
        elif tipo == 'chave_comparacao':
            # Correspondências que têm chave válida mas não vieram por ID nem por histórico
            mask = correspondencias.get('chave_comparacao', pd.Series()).notna()
            
            # Excluir as que já foram por ID
            if 'id_movimento_a_pagar' in correspondencias.columns and 'id_movimento_pagas' in correspondencias.columns:
                mask_tem_id = (correspondencias['id_movimento_a_pagar'].notna() & 
                              correspondencias['id_movimento_pagas'].notna())
                mask = mask & ~mask_tem_id
            
            # Excluir as que foram por histórico (verificando se existe a coluna historico_norm da correspondência)
            if 'historico_norm' in correspondencias.columns:
                mask_tem_historico = correspondencias['historico_norm'].notna()
                mask = mask & ~mask_tem_historico
            
            return correspondencias[mask] if mask.any() else pd.DataFrame()
            
        elif tipo == 'historico_norm':
            # Correspondências que têm histórico válido
            # A coluna 'historico_norm' existe quando a correspondência foi feita por histórico
            mask = correspondencias.get('historico_norm', pd.Series()).notna()
            return correspondencias[mask] if mask.any() else pd.DataFrame()
        
        return pd.DataFrame()
    
    def _preparar_dataset_comparacao(self, df: pd.DataFrame, tipo: str) -> pd.DataFrame:
        """
        Prepara dataset para comparação adicionando chaves normalizadas.
        """
        print(f"🔍 Processando DataFrame tipo '{tipo}' com {len(df)} registros")
        print(f"📋 Colunas disponíveis: {list(df.columns)}")
        
        df_prep = df.copy()
        
        # Normalizar nomes das colunas primeiro
        df_prep.columns = [col.lower().replace(' ', '_') for col in df_prep.columns]
        
        # Mapear colunas específicas dos modelos
        if tipo == 'a_pagar':
            column_mapping = {
                'empresa': 'empresa',
                'fornecedor': 'fornecedor',
                'valordoc': 'valor',
                'descriçãoconta': 'descricao',
                'datavencimento': 'data_vencimento',
                'histórico': 'historico',
                'idmovimento': 'id_movimento'
            }
        else:  # tipo == 'pagas'
            column_mapping = {
                'idbanco': 'empresa',
                'saída': 'valor',
                'descriçãoconta': 'descricao',
                'datapagamento': 'data_pagamento',
                'histórico': 'historico',
                'campo54': 'id_movimento'
            }
        
        # Renomear colunas se existirem
        for old_name, new_name in column_mapping.items():
            if old_name in df_prep.columns:
                df_prep = df_prep.rename(columns={old_name: new_name})
        
        # Verificar se as colunas necessárias existem
        if 'valor' not in df_prep.columns:
            print(f"⚠️ Coluna 'valor' não encontrada para tipo '{tipo}'. Colunas disponíveis: {list(df_prep.columns)}")
            return df_prep
            
        if 'descricao' not in df_prep.columns:
            print(f"⚠️ Coluna 'descricao' não encontrada para tipo '{tipo}'. Colunas disponíveis: {list(df_prep.columns)}")
            return df_prep
        
        # Normalizar strings para comparação
        df_prep['descricao_norm'] = df_prep['descricao'].astype(str).str.upper().str.strip()
        
        # Para comparação, usar apenas descricao e valor (mais data quando disponível)
        # Não usar empresa/conta_corrente/fornecedor na chave de comparação
        df_prep['valor_norm'] = df_prep['valor'].round(2)
        
        if 'descricao' in df_prep.columns:
            df_prep['descricao_norm'] = df_prep['descricao'].astype(str).str.upper().str.strip()
        else:
            df_prep['descricao_norm'] = ''
        
        # Criar chave de comparação baseada em descrição e valor
        try:
            df_prep['chave_comparacao'] = (
                df_prep['descricao_norm'] + '_' + 
                df_prep['valor_norm'].astype(str)
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
        Encontra correspondências exatas entre os datasets usando múltiplas estratégias.
        """
        correspondencias_totais = pd.DataFrame()
        
        # Estratégia 1: Correspondência por ID (mais confiável)
        if 'id_movimento' in df_a_pagar.columns and 'id_movimento' in df_pagas.columns:
            print("🔍 Buscando correspondências por ID...")
            correspondencias_id = pd.merge(
                df_a_pagar, df_pagas,
                on='id_movimento',
                suffixes=('_a_pagar', '_pagas'),
                how='inner'
            )
            if not correspondencias_id.empty:
                print(f"✅ Encontradas {len(correspondencias_id)} correspondências por ID")
                correspondencias_totais = pd.concat([correspondencias_totais, correspondencias_id], ignore_index=True)
        
        # Estratégia 2: Correspondência por chave (descrição + valor)
        if 'chave_comparacao' in df_a_pagar.columns and 'chave_comparacao' in df_pagas.columns:
            print("🔍 Buscando correspondências por chave de comparação...")
            
            # Remover IDs já correspondidos
            ids_ja_correspondidos = set()
            if not correspondencias_totais.empty and 'id_movimento_a_pagar' in correspondencias_totais.columns:
                ids_ja_correspondidos.update(correspondencias_totais['id_movimento_a_pagar'].dropna())
            
            df_a_pagar_restante = df_a_pagar[~df_a_pagar['id_movimento'].isin(ids_ja_correspondidos)] if ids_ja_correspondidos else df_a_pagar
            
            ids_pagas_correspondidos = set()
            if not correspondencias_totais.empty and 'id_movimento_pagas' in correspondencias_totais.columns:
                ids_pagas_correspondidos.update(correspondencias_totais['id_movimento_pagas'].dropna())
            
            df_pagas_restante = df_pagas[~df_pagas['id_movimento'].isin(ids_pagas_correspondidos)] if ids_pagas_correspondidos else df_pagas
            
            correspondencias_chave = pd.merge(
                df_a_pagar_restante, df_pagas_restante,
                on='chave_comparacao',
                suffixes=('_a_pagar', '_pagas'),
                how='inner'
            )
            
            if not correspondencias_chave.empty:
                print(f"✅ Encontradas {len(correspondencias_chave)} correspondências por chave")
                correspondencias_totais = pd.concat([correspondencias_totais, correspondencias_chave], ignore_index=True)
        
        # Estratégia 3: Correspondência por histórico 100% exato
        if 'historico' in df_a_pagar.columns and 'historico' in df_pagas.columns:
            print("🔍 Buscando correspondências por histórico exato...")
            
            # Remover registros já correspondidos
            ids_ja_correspondidos_a_pagar = set()
            ids_ja_correspondidos_pagas = set()
            
            if not correspondencias_totais.empty:
                if 'id_movimento_a_pagar' in correspondencias_totais.columns:
                    ids_ja_correspondidos_a_pagar.update(correspondencias_totais['id_movimento_a_pagar'].dropna())
                if 'id_movimento_pagas' in correspondencias_totais.columns:
                    ids_ja_correspondidos_pagas.update(correspondencias_totais['id_movimento_pagas'].dropna())
            
            df_a_pagar_historico = df_a_pagar.copy()
            df_pagas_historico = df_pagas.copy()
            
            if ids_ja_correspondidos_a_pagar:
                df_a_pagar_historico = df_a_pagar_historico[~df_a_pagar_historico['id_movimento'].isin(ids_ja_correspondidos_a_pagar)]
            if ids_ja_correspondidos_pagas:
                df_pagas_historico = df_pagas_historico[~df_pagas_historico['id_movimento'].isin(ids_ja_correspondidos_pagas)]
            
            # Normalizar históricos para comparação
            df_a_pagar_historico['historico_norm'] = df_a_pagar_historico['historico'].astype(str).str.upper().str.strip()
            df_pagas_historico['historico_norm'] = df_pagas_historico['historico'].astype(str).str.upper().str.strip()
            
            # Filtrar históricos válidos (não vazios, não "NAN")
            mask_a_pagar = (df_a_pagar_historico['historico_norm'] != '') & (df_a_pagar_historico['historico_norm'] != 'NAN') & (df_a_pagar_historico['historico_norm'].str.len() > 3)
            mask_pagas = (df_pagas_historico['historico_norm'] != '') & (df_pagas_historico['historico_norm'] != 'NAN') & (df_pagas_historico['historico_norm'].str.len() > 3)
            
            df_a_pagar_historico = df_a_pagar_historico[mask_a_pagar]
            df_pagas_historico = df_pagas_historico[mask_pagas]
            
            if not df_a_pagar_historico.empty and not df_pagas_historico.empty:
                correspondencias_historico = pd.merge(
                    df_a_pagar_historico, df_pagas_historico,
                    on='historico_norm',
                    suffixes=('_a_pagar', '_pagas'),
                    how='inner'
                )
                
                if not correspondencias_historico.empty:
                    print(f"✅ Encontradas {len(correspondencias_historico)} correspondências por histórico exato")
                    correspondencias_totais = pd.concat([correspondencias_totais, correspondencias_historico], ignore_index=True)
        
        return correspondencias_totais
    
    def _encontrar_correspondencias_aproximadas(self, df_a_pagar: pd.DataFrame, df_pagas: pd.DataFrame, 
                                              correspondencias_exatas: pd.DataFrame) -> pd.DataFrame:
        """
        Encontra correspondências aproximadas usando diferentes critérios.
        """
        correspondencias_aprox = []
        
        # Identificar registros já correspondidos exatamente
        ids_ja_correspondidos_a_pagar = set()
        ids_ja_correspondidos_pagas = set()
        
        if not correspondencias_exatas.empty:
            # Usar diferentes colunas dependendo de como foram feitas as correspondências
            if 'id_movimento_a_pagar' in correspondencias_exatas.columns:
                ids_ja_correspondidos_a_pagar.update(correspondencias_exatas['id_movimento_a_pagar'].dropna())
            if 'id_movimento_pagas' in correspondencias_exatas.columns:
                ids_ja_correspondidos_pagas.update(correspondencias_exatas['id_movimento_pagas'].dropna())
            
            # Fallback usando chave de comparação
            if 'chave_comparacao' in correspondencias_exatas.columns:
                chaves_exatas = set(correspondencias_exatas['chave_comparacao'].dropna())
                df_a_pagar_restante = df_a_pagar[~df_a_pagar['chave_comparacao'].isin(chaves_exatas)]
                df_pagas_restante = df_pagas[~df_pagas['chave_comparacao'].isin(chaves_exatas)]
            else:
                df_a_pagar_restante = df_a_pagar
                df_pagas_restante = df_pagas
        else:
            df_a_pagar_restante = df_a_pagar
            df_pagas_restante = df_pagas
        
        # Remover também por ID se disponível
        if ids_ja_correspondidos_a_pagar:
            df_a_pagar_restante = df_a_pagar_restante[~df_a_pagar_restante['id_movimento'].isin(ids_ja_correspondidos_a_pagar)]
        if ids_ja_correspondidos_pagas:
            df_pagas_restante = df_pagas_restante[~df_pagas_restante['id_movimento'].isin(ids_ja_correspondidos_pagas)]
        
        print(f"🔍 Buscando correspondências aproximadas em {len(df_a_pagar_restante)} contas a pagar restantes...")
        
        for idx, conta_pagar in df_a_pagar_restante.iterrows():
            if 'valor' not in conta_pagar or pd.isna(conta_pagar['valor']):
                continue
                
            # Critério 1: Valor exato + descrição similar (mais de 5 caracteres em comum)
            candidatos_valor_exato = df_pagas_restante[df_pagas_restante['valor'] == conta_pagar['valor']]
            if not candidatos_valor_exato.empty and 'descricao_norm' in conta_pagar:
                desc_conta = str(conta_pagar['descricao_norm'])
                for _, candidato in candidatos_valor_exato.iterrows():
                    desc_candidato = str(candidato['descricao_norm'])
                    if len(desc_conta) >= 5 and len(desc_candidato) >= 5:
                        # Verificar se pelo menos 5 caracteres consecutivos coincidem
                        if any(desc_conta[i:i+5] in desc_candidato for i in range(len(desc_conta)-4)):
                            correspondencias_aprox.append({
                                'tipo': 'valor_exato_desc_similar',
                                'conta_a_pagar_idx': idx,
                                'conta_paga_idx': candidato.name,
                                'diferenca_valor': 0,
                                'similaridade_desc': 'alta'
                            })
                            continue
            
            # Critério 2: Valor aproximado (tolerância de R$ 1,00) + mesma descrição
            candidatos_valor_aprox = df_pagas_restante[
                (abs(df_pagas_restante['valor'] - conta_pagar['valor']) <= self.tolerancia_valor)
            ]
            
            if not candidatos_valor_aprox.empty:
                for _, candidato in candidatos_valor_aprox.iterrows():
                    if 'descricao_norm' in conta_pagar and candidato['descricao_norm'] == conta_pagar['descricao_norm']:
                        diferenca = abs(candidato['valor'] - conta_pagar['valor'])
                        correspondencias_aprox.append({
                            'tipo': 'valor_aprox_desc_exata',
                            'conta_a_pagar_idx': idx,
                            'conta_paga_idx': candidato.name,
                            'diferenca_valor': diferenca,
                            'similaridade_desc': 'exata'
                        })
        
        # Converter para DataFrame
        if correspondencias_aprox:
            df_correspondencias_aprox = pd.DataFrame(correspondencias_aprox)
            
            # Adicionar dados das contas
            result_data = []
            for _, corresp in df_correspondencias_aprox.iterrows():
                conta_pagar = df_a_pagar_restante.loc[corresp['conta_a_pagar_idx']]
                conta_paga = df_pagas_restante.loc[corresp['conta_paga_idx']]
                
                row_data = {}
                # Adicionar dados da conta a pagar
                for col in conta_pagar.index:
                    row_data[f'{col}_a_pagar'] = conta_pagar[col]
                
                # Adicionar dados da conta paga
                for col in conta_paga.index:
                    row_data[f'{col}_pagas'] = conta_paga[col]
                
                # Adicionar metadados da correspondência
                row_data.update({
                    'tipo_correspondencia': corresp['tipo'],
                    'diferenca_valor': corresp['diferenca_valor'],
                    'similaridade_desc': corresp['similaridade_desc']
                })
                
                result_data.append(row_data)
            
            return pd.DataFrame(result_data)
        
        return pd.DataFrame()
    
    def _identificar_contas_nao_pagas(self, df_a_pagar: pd.DataFrame, 
                                    correspondencias_exatas: pd.DataFrame,
                                    correspondencias_aproximadas: pd.DataFrame) -> pd.DataFrame:
        """
        Identifica contas a pagar que não têm correspondência nas contas pagas.
        """
        # Chaves das contas que já têm correspondência
        chaves_correspondidas = set()
        
        if not correspondencias_exatas.empty and 'chave_comparacao' in correspondencias_exatas.columns:
            chaves_correspondidas.update(correspondencias_exatas['chave_comparacao'].dropna())
        
        if not correspondencias_aproximadas.empty and 'chave_comparacao' in correspondencias_aproximadas.columns:
            chaves_correspondidas.update(correspondencias_aproximadas['chave_comparacao'].dropna())
        
        # Filtrar contas sem correspondência usando chave de comparação
        if 'chave_comparacao' in df_a_pagar.columns:
            contas_nao_pagas = df_a_pagar[~df_a_pagar['chave_comparacao'].isin(chaves_correspondidas)].copy()
        else:
            # Fallback se não há chave de comparação
            contas_nao_pagas = df_a_pagar.copy()
        
        return contas_nao_pagas
    
    def _identificar_pagamentos_sem_conta(self, df_pagas: pd.DataFrame,
                                        correspondencias_exatas: pd.DataFrame,
                                        correspondencias_aproximadas: pd.DataFrame) -> pd.DataFrame:
        """
        Identifica pagamentos que não têm correspondência nas contas a pagar.
        """
        # Chaves dos pagamentos que já têm correspondência
        chaves_correspondidas = set()
        
        if not correspondencias_exatas.empty and 'chave_comparacao' in correspondencias_exatas.columns:
            chaves_correspondidas.update(correspondencias_exatas['chave_comparacao'].dropna())
        
        if not correspondencias_aproximadas.empty and 'chave_comparacao' in correspondencias_aproximadas.columns:
            chaves_correspondidas.update(correspondencias_aproximadas['chave_comparacao'].dropna())
        
        # Filtrar pagamentos sem correspondência usando chave de comparação
        if 'chave_comparacao' in df_pagas.columns:
            pagamentos_sem_conta = df_pagas[~df_pagas['chave_comparacao'].isin(chaves_correspondidas)].copy()
        else:
            # Fallback se não há chave de comparação
            pagamentos_sem_conta = df_pagas.copy()
        
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
