"""
Módulo de lógicas de negócio do Calendário Financeiro.

Este módulo contém todas as lógicas separadas da interface do usuário,
organizadas por funcionalidade específica.
"""

from .dashboard_logic import mostrar_resumo_dashboard, mostrar_dados_banco
from .file_processing_logic import (
    processar_arquivos,
    detectar_e_processar_arquivo,
    processar_arquivo_padrao,
    simular_reimportacao
)
from .calendar_logic import (
    criar_calendario_financeiro,
    mostrar_calendario_semanal,
    mostrar_calendario_mensal,
    calcular_semanas_do_mes
)
from .calendar_helpers import (
    mostrar_dia_semana,
    mostrar_dia_mensal,
    mostrar_resumo_semana,
    mostrar_resumo_mes,
    mostrar_detalhes_dia,
    ajustar_para_dia_util
)
from .audit_logic import (
    executar_auditoria_dia,
    executar_auditoria_completa
)
from .cleanup_logic import remover_arquivo_temporario
from .ui_helpers import aplicar_css_global

__all__ = [
    # Dashboard
    'mostrar_resumo_dashboard',
    'mostrar_dados_banco',
    
    # File Processing
    'processar_arquivos',
    'detectar_e_processar_arquivo',
    'processar_arquivo_padrao',
    'simular_reimportacao',
    
    # Calendar
    'criar_calendario_financeiro',
    'mostrar_calendario_semanal',
    'mostrar_calendario_mensal',
    'calcular_semanas_do_mes',
    'ajustar_para_dia_util',
    'mostrar_dia_semana',
    'mostrar_dia_mensal',
    'mostrar_resumo_semana',
    'mostrar_resumo_mes',
    'mostrar_detalhes_dia',
    
    # Audit
    'executar_auditoria_dia',
    'executar_auditoria_completa',
    
    # Cleanup
    'remover_arquivo_temporario',
    
    # UI Helpers
    'aplicar_css_global'
]
