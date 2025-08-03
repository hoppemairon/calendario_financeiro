"""
Módulo para geração de relatórios e exportação de dados.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Classe para geração de relatórios financeiros."""
    
    def __init__(self, reports_path: str = "reports"):
        self.reports_path = reports_path
        os.makedirs(reports_path, exist_ok=True)
    
    def gerar_relatorio_excel(self, correspondencias: Dict, resumo: Dict, 
                             resumo_empresa: pd.DataFrame, nome_arquivo: str = None) -> str:
        """
        Gera relatório completo em Excel.
        
        Args:
            correspondencias: Dados de correspondências
            resumo: Resumo financeiro
            resumo_empresa: Resumo por empresa
            nome_arquivo: Nome do arquivo (opcional)
            
        Returns:
            Caminho do arquivo gerado
        """
        if nome_arquivo is None:
            nome_arquivo = f"relatorio_financeiro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        arquivo_path = os.path.join(self.reports_path, nome_arquivo)
        
        try:
            with pd.ExcelWriter(arquivo_path, engine='xlsxwriter') as writer:
                # Aba 1: Resumo Geral
                df_resumo_geral = pd.DataFrame([resumo])
                df_resumo_geral.to_excel(writer, sheet_name='Resumo_Geral', index=False)
                
                # Aba 2: Resumo por Empresa
                if not resumo_empresa.empty:
                    resumo_empresa.to_excel(writer, sheet_name='Resumo_por_Empresa', index=False)
                
                # Aba 3: Correspondências Exatas
                if correspondencias['exatas']:
                    df_exatas = self._processar_correspondencias_para_excel(correspondencias['exatas'], 'exata')
                    df_exatas.to_excel(writer, sheet_name='Correspondencias_Exatas', index=False)
                
                # Aba 4: Correspondências Aproximadas
                if correspondencias['aproximadas']:
                    df_aproximadas = self._processar_correspondencias_para_excel(correspondencias['aproximadas'], 'aproximada')
                    df_aproximadas.to_excel(writer, sheet_name='Correspondencias_Aproximadas', index=False)
                
                # Aba 5: Contas Pendentes
                if correspondencias['nao_encontradas']:
                    df_pendentes = pd.DataFrame(correspondencias['nao_encontradas'])
                    df_pendentes.to_excel(writer, sheet_name='Contas_Pendentes', index=False)
                
                # Aba 6: Pagamentos Extras
                if correspondencias['pagamentos_extras']:
                    df_extras = pd.DataFrame(correspondencias['pagamentos_extras'])
                    df_extras.to_excel(writer, sheet_name='Pagamentos_Extras', index=False)
                
                # Aplicar formatação
                self._aplicar_formatacao_excel(writer)
            
            logger.info(f"Relatório Excel gerado: {arquivo_path}")
            return arquivo_path
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório Excel: {str(e)}")
            return None
    
    def _processar_correspondencias_para_excel(self, correspondencias: List[Dict], tipo: str) -> pd.DataFrame:
        """
        Processa correspondências para formato Excel.
        
        Args:
            correspondencias: Lista de correspondências
            tipo: Tipo da correspondência
            
        Returns:
            DataFrame formatado
        """
        dados = []
        
        for corresp in correspondencias:
            linha = {
                'tipo_correspondencia': tipo,
                'empresa': corresp['conta_a_pagar']['empresa'],
                'descricao': corresp['conta_a_pagar']['descricao'],
                'categoria': corresp['conta_a_pagar']['categoria'],
                'valor_a_pagar': corresp['conta_a_pagar']['valor'],
                'valor_pago': corresp['conta_paga']['valor'],
                'diferenca_valor': corresp['diferenca_valor'],
                'data_vencimento': corresp['conta_a_pagar'].get('data_vencimento'),
                'data_pagamento': corresp['conta_paga']['data_pagamento'],
                'diferenca_dias': corresp['diferenca_dias'],
                'arquivo_origem_a_pagar': corresp['conta_a_pagar'].get('arquivo_origem'),
                'arquivo_origem_pago': corresp['conta_paga'].get('arquivo_origem')
            }
            
            if tipo == 'aproximada' and 'motivo_aproximacao' in corresp:
                linha['motivo_aproximacao'] = corresp['motivo_aproximacao']
            
            dados.append(linha)
        
        return pd.DataFrame(dados)
    
    def _aplicar_formatacao_excel(self, writer):
        """
        Aplica formatação básica ao arquivo Excel.
        
        Args:
            writer: ExcelWriter object
        """
        workbook = writer.book
        
        # Formatos
        formato_moeda = workbook.add_format({'num_format': 'R$ #,##0.00'})
        formato_data = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        formato_header = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1
        })
        
        # Aplicar formatação nas planilhas
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            
            # Ajustar largura das colunas
            worksheet.set_column('A:Z', 15)
            
            # Formatar headers (primeira linha)
            worksheet.set_row(0, None, formato_header)
    
    def criar_grafico_resumo_por_empresa(self, resumo_empresa: pd.DataFrame) -> go.Figure:
        """
        Cria gráfico de barras com resumo por empresa.
        
        Args:
            resumo_empresa: DataFrame com resumo por empresa
            
        Returns:
            Figura do Plotly
        """
        if resumo_empresa.empty:
            return go.Figure()
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Valores por Empresa', 'Status de Pagamento'),
            specs=[[{"secondary_y": False}, {"type": "pie"}]]
        )
        
        # Gráfico de barras - Valores por empresa
        fig.add_trace(
            go.Bar(
                name='A Pagar',
                x=resumo_empresa['empresa'],
                y=resumo_empresa['valor_a_pagar'],
                marker_color='lightblue'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(
                name='Pago',
                x=resumo_empresa['empresa'],
                y=resumo_empresa['valor_pago'],
                marker_color='lightgreen'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(
                name='Pendente',
                x=resumo_empresa['empresa'],
                y=resumo_empresa['valor_pendente'],
                marker_color='lightcoral'
            ),
            row=1, col=1
        )
        
        # Gráfico de pizza - Status geral
        fig.add_trace(
            go.Pie(
                labels=['Pago', 'Pendente'],
                values=[resumo_empresa['valor_pago'].sum(), resumo_empresa['valor_pendente'].sum()],
                marker_colors=['lightgreen', 'lightcoral']
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title_text="Resumo Financeiro por Empresa",
            showlegend=True,
            height=500
        )
        
        fig.update_xaxes(title_text="Empresas", row=1, col=1)
        fig.update_yaxes(title_text="Valor (R$)", row=1, col=1)
        
        return fig
    
    def criar_calendario_vencimentos(self, df_a_pagar: pd.DataFrame, 
                                   df_correspondencias: Optional[pd.DataFrame] = None) -> go.Figure:
        """
        Cria calendário de vencimentos.
        
        Args:
            df_a_pagar: DataFrame com contas a pagar
            df_correspondencias: DataFrame com correspondências (opcional)
            
        Returns:
            Figura do Plotly
        """
        if df_a_pagar.empty:
            return go.Figure()
        
        # Preparar dados do calendário
        df_calendario = df_a_pagar.copy()
        df_calendario['status'] = 'Pendente'
        
        if df_correspondencias is not None and not df_correspondencias.empty:
            # Marcar como pago as contas que têm correspondência
            for idx, row in df_correspondencias.iterrows():
                mask = (
                    (df_calendario['empresa'] == row['empresa']) &
                    (df_calendario['valor'] == row['valor_a_pagar']) &
                    (df_calendario['data_vencimento'] == row['data_vencimento'])
                )
                df_calendario.loc[mask, 'status'] = 'Pago'
        
        # Agrupar por data e status
        df_agrupado = df_calendario.groupby(['data_vencimento', 'status']).agg({
            'valor': 'sum',
            'empresa': 'count'
        }).reset_index()
        df_agrupado.rename(columns={'empresa': 'quantidade'}, inplace=True)
        
        # Criar gráfico
        fig = go.Figure()
        
        for status in df_agrupado['status'].unique():
            df_status = df_agrupado[df_agrupado['status'] == status]
            
            color = 'green' if status == 'Pago' else 'red'
            
            fig.add_trace(go.Scatter(
                x=df_status['data_vencimento'],
                y=df_status['valor'],
                mode='markers',
                marker=dict(
                    size=df_status['quantidade'] * 5,  # Tamanho proporcional à quantidade
                    color=color,
                    opacity=0.7
                ),
                name=status,
                text=df_status.apply(lambda row: 
                    f"Data: {row['data_vencimento'].strftime('%d/%m/%Y')}<br>"
                    f"Valor: R$ {row['valor']:,.2f}<br>"
                    f"Quantidade: {row['quantidade']}", axis=1),
                hovertemplate='%{text}<extra></extra>'
            ))
        
        fig.update_layout(
            title="Calendário de Vencimentos",
            xaxis_title="Data de Vencimento",
            yaxis_title="Valor Total (R$)",
            hovermode='closest'
        )
        
        return fig
    
    def criar_grafico_fluxo_caixa(self, df_a_pagar: pd.DataFrame, 
                                 df_pagas: pd.DataFrame) -> go.Figure:
        """
        Cria gráfico de fluxo de caixa projetado vs realizado.
        
        Args:
            df_a_pagar: DataFrame com contas a pagar
            df_pagas: DataFrame com contas pagas
            
        Returns:
            Figura do Plotly
        """
        # Preparar dados de fluxo projetado (baseado em vencimentos)
        if not df_a_pagar.empty:
            fluxo_projetado = df_a_pagar.groupby('data_vencimento')['valor'].sum().reset_index()
            fluxo_projetado['tipo'] = 'Projetado'
            fluxo_projetado['data'] = fluxo_projetado['data_vencimento']
        else:
            fluxo_projetado = pd.DataFrame()
        
        # Preparar dados de fluxo realizado (baseado em pagamentos)
        if not df_pagas.empty:
            fluxo_realizado = df_pagas.groupby('data_pagamento')['valor'].sum().reset_index()
            fluxo_realizado['tipo'] = 'Realizado'
            fluxo_realizado['data'] = fluxo_realizado['data_pagamento']
        else:
            fluxo_realizado = pd.DataFrame()
        
        fig = go.Figure()
        
        if not fluxo_projetado.empty:
            fig.add_trace(go.Scatter(
                x=fluxo_projetado['data'],
                y=fluxo_projetado['valor'],
                mode='lines+markers',
                name='Fluxo Projetado',
                line=dict(color='blue', dash='dash'),
                marker=dict(size=8)
            ))
        
        if not fluxo_realizado.empty:
            fig.add_trace(go.Scatter(
                x=fluxo_realizado['data'],
                y=fluxo_realizado['valor'],
                mode='lines+markers',
                name='Fluxo Realizado',
                line=dict(color='green'),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            title="Fluxo de Caixa: Projetado vs Realizado",
            xaxis_title="Data",
            yaxis_title="Valor (R$)",
            hovermode='x unified'
        )
        
        return fig
    
    def salvar_grafico(self, fig: go.Figure, nome_arquivo: str, formato: str = 'html') -> str:
        """
        Salva gráfico em arquivo.
        
        Args:
            fig: Figura do Plotly
            nome_arquivo: Nome do arquivo (sem extensão)
            formato: Formato do arquivo ('html' ou 'png')
            
        Returns:
            Caminho do arquivo salvo
        """
        arquivo_path = os.path.join(self.reports_path, f"{nome_arquivo}.{formato}")
        
        try:
            if formato == 'html':
                fig.write_html(arquivo_path)
            elif formato == 'png':
                fig.write_image(arquivo_path)
            
            logger.info(f"Gráfico salvo: {arquivo_path}")
            return arquivo_path
            
        except Exception as e:
            logger.error(f"Erro ao salvar gráfico: {str(e)}")
            return None
