"""
Lógica de limpeza e utilitários para o Calendário Financeiro.

Contém funções para limpeza de arquivos temporários e outras operações de manutenção.
"""

import os
import time
import streamlit as st

def remover_arquivo_temporario(caminho_arquivo):
    """
    Remove arquivo temporário de forma segura, com tentativas múltiplas.
    
    Args:
        caminho_arquivo: Caminho para o arquivo temporário
    
    Returns:
        bool: True se removido com sucesso, False caso contrário
    """
    
    if not os.path.exists(caminho_arquivo):
        return True
    
    # Tentar remover até 5 vezes com intervalos
    for tentativa in range(5):
        try:
            os.remove(caminho_arquivo)
            return True
        except (PermissionError, OSError):
            if tentativa < 4:  # Não é a última tentativa
                time.sleep(0.5)  # Aguardar 500ms antes da próxima tentativa
                continue
            else:
                # Última tentativa - apenas avisar que não foi possível remover
                st.warning(f"⚠️ Não foi possível remover arquivo temporário: {os.path.basename(caminho_arquivo)}")
                return False
    
    return False
