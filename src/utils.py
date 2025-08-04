"""
Utilitários para formatação de dados no padrão brasileiro.
"""

import locale
from datetime import datetime
from typing import Union
import pandas as pd

# Configurar locale para português brasileiro
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except locale.Error:
        # Fallback se não conseguir configurar o locale
        pass

def formatar_moeda_brasileira(valor: Union[float, int], com_simbolo: bool = True) -> str:
    """
    Formata um valor numérico como moeda brasileira.
    
    Args:
        valor: Valor a ser formatado
        com_simbolo: Se deve incluir o símbolo R$
        
    Returns:
        String formatada (ex: "R$ 1.234,56" ou "1.234,56")
    """
    if pd.isna(valor) or valor is None:
        return "R$ 0,00" if com_simbolo else "0,00"
    
    try:
        # Formatar com separador de milhares e decimais brasileiros
        valor_formatado = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        if com_simbolo:
            return f"R$ {valor_formatado}"
        else:
            return valor_formatado
    except (ValueError, TypeError):
        return "R$ 0,00" if com_simbolo else "0,00"

def formatar_data_brasileira(data: Union[datetime, pd.Timestamp, str], formato: str = "%d/%m/%Y") -> str:
    """
    Formata uma data no padrão brasileiro.
    
    Args:
        data: Data a ser formatada
        formato: Formato desejado (padrão: dd/mm/yyyy)
        
    Returns:
        String formatada (ex: "03/08/2025")
    """
    if pd.isna(data) or data is None:
        return ""
    
    try:
        if isinstance(data, str):
            # Tentar converter string para datetime
            if "/" in data:
                # Já está no formato brasileiro
                return data
            elif "-" in data:
                # Formato ISO (yyyy-mm-dd)
                data_obj = datetime.strptime(data, "%Y-%m-%d")
                return data_obj.strftime(formato)
        
        # Se já é datetime ou Timestamp
        if hasattr(data, 'strftime'):
            return data.strftime(formato)
        
        return str(data)
    except (ValueError, TypeError, AttributeError):
        return str(data) if data else ""

def formatar_numero_brasileiro(numero: Union[float, int], decimais: int = 0) -> str:
    """
    Formata um número no padrão brasileiro (separador de milhares).
    
    Args:
        numero: Número a ser formatado
        decimais: Quantidade de casas decimais
        
    Returns:
        String formatada (ex: "1.234" ou "1.234,56")
    """
    if pd.isna(numero) or numero is None:
        return "0"
    
    try:
        if decimais == 0:
            return f"{numero:,.0f}".replace(",", ".")
        else:
            return f"{numero:,.{decimais}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0"

def formatar_percentual_brasileiro(valor: Union[float, int], decimais: int = 1) -> str:
    """
    Formata um percentual no padrão brasileiro.
    
    Args:
        valor: Valor percentual (ex: 0.75 para 75%)
        decimais: Casas decimais
        
    Returns:
        String formatada (ex: "75,0%")
    """
    if pd.isna(valor) or valor is None:
        return "0,0%"
    
    try:
        # Se o valor já está em formato percentual (>1), usar direto
        if valor > 1:
            percentual = valor
        else:
            percentual = valor * 100
            
        if decimais == 0:
            return f"{percentual:,.0f}%".replace(",", ".")
        else:
            return f"{percentual:,.{decimais}f}%".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,0%"

def converter_dataframe_formato_brasileiro(df: pd.DataFrame, colunas_moeda: list = None, colunas_data: list = None) -> pd.DataFrame:
    """
    Converte um DataFrame para formato brasileiro.
    
    Args:
        df: DataFrame a ser convertido
        colunas_moeda: Lista de colunas que contêm valores monetários
        colunas_data: Lista de colunas que contêm datas
        
    Returns:
        DataFrame com formatação brasileira
    """
    if df.empty:
        return df
    
    df_formatado = df.copy()
    
    # Formatar colunas de moeda
    if colunas_moeda:
        for coluna in colunas_moeda:
            if coluna in df_formatado.columns:
                df_formatado[coluna] = df_formatado[coluna].apply(formatar_moeda_brasileira)
    
    # Formatar colunas de data
    if colunas_data:
        for coluna in colunas_data:
            if coluna in df_formatado.columns:
                df_formatado[coluna] = df_formatado[coluna].apply(formatar_data_brasileira)
    
    return df_formatado

def obter_mes_nome_brasileiro(mes: int) -> str:
    """
    Retorna o nome do mês em português.
    
    Args:
        mes: Número do mês (1-12)
        
    Returns:
        Nome do mês em português
    """
    meses = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    return meses.get(mes, f"Mês {mes}")

def obter_dia_semana_brasileiro(data: Union[datetime, pd.Timestamp]) -> str:
    """
    Retorna o nome do dia da semana em português.
    
    Args:
        data: Data para obter o dia da semana
        
    Returns:
        Nome do dia da semana em português
    """
    if pd.isna(data) or data is None:
        return ""
    
    dias = {
        0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira", 3: "Quinta-feira",
        4: "Sexta-feira", 5: "Sábado", 6: "Domingo"
    }
    
    try:
        if hasattr(data, 'weekday'):
            return dias.get(data.weekday(), "")
        return ""
    except (AttributeError, TypeError):
        return ""
