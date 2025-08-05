from src.database.supabase_client import SupabaseClient
import os
from dotenv import load_dotenv
load_dotenv()

client = SupabaseClient()

print('=== INVESTIGANDO DIFERENÇA DE VALORES ===')

try:
    # Teste 1: Todos os registros do dia 05/08/2025 SEM filtro de user_id
    print('1. TODOS os registros para 05/08/2025 (sem filtro de user):')
    response_all = client.supabase.table('contas_a_pagar').select('usuario_id, valor, empresa').eq('data_vencimento', '2025-08-05').execute()
    
    if response_all.data:
        total_all = sum(float(r.get('valor', 0)) for r in response_all.data)
        print(f'   Total geral: {len(response_all.data)} registros = R$ {total_all:,.2f}')
        
        # Agrupar por user_id
        from collections import defaultdict
        por_user = defaultdict(list)
        
        for r in response_all.data:
            user_id = r.get('usuario_id', 'NULL')
            valor = float(r.get('valor', 0))
            por_user[user_id].append(valor)
        
        print('   Por user_id:')
        for user_id, valores in por_user.items():
            total_user = sum(valores)
            print(f'     {user_id}: {len(valores)} registros = R$ {total_user:,.2f}')
    
    # Teste 2: Apenas para o user_id específico
    print('\n2. Apenas para user_id bde0a328-7d9f-4c91-a005-a1ee285c16fb:')
    response_user = client.supabase.table('contas_a_pagar').select('valor, empresa').eq('data_vencimento', '2025-08-05').eq('usuario_id', 'bde0a328-7d9f-4c91-a005-a1ee285c16fb').execute()
    
    if response_user.data:
        total_user = sum(float(r.get('valor', 0)) for r in response_user.data)
        print(f'   Total específico: {len(response_user.data)} registros = R$ {total_user:,.2f}')
        
        # Mostrar primeiros valores
        print('   Primeiros 10 valores:')
        for i, r in enumerate(response_user.data[:10]):
            valor = float(r.get('valor', 0))
            empresa = r.get('empresa', 'N/A')[:30]
            print(f'     {i+1}: R$ {valor:,.2f} - {empresa}')

except Exception as e:
    print(f'Erro: {e}')
