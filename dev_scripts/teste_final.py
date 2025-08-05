#!/usr/bin/env python3
"""
Teste final - simular exatamente o que o Streamlit faz
"""
import sys
import os

# Adicionar o diretório pai ao path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from src.database.supabase_client import SupabaseClient
import pandas as pd

def main():
    print("🎯 TESTE FINAL - SIMULANDO O STREAMLIT")
    print("=" * 50)
    
    # Simular exatamente o que o Streamlit faz
    supabase = SupabaseClient()
    user_id = "bde0a328-7d9f-4c91-a005-a1ee285c16fb"
    
    # 1. Definir user_id (como o Streamlit faz)
    supabase.set_user_id(user_id)
    
    # 2. Buscar contas a pagar (como o Streamlit faz)
    print("📊 Buscando contas a pagar...")
    df_contas = supabase.buscar_contas_a_pagar()
    print(f"Total de registros: {len(df_contas)}")
    
    if not df_contas.empty:
        # 3. Processar data (como o Streamlit faz)
        df_contas['data_vencimento'] = pd.to_datetime(df_contas['data_vencimento'])
        
        # 4. Filtrar para 05/08/2025 (como o Streamlit faz)
        data_filtro = "2025-08-05"
        df_dia = df_contas[df_contas['data_vencimento'].dt.strftime('%Y-%m-%d') == data_filtro]
        
        print(f"📅 Registros para {data_filtro}: {len(df_dia)}")
        
        if not df_dia.empty:
            # 5. Calcular total (como o Streamlit faz)
            total_a_pagar = df_dia['valor'].sum()
            
            print(f"💰 A PAGAR: R$ {total_a_pagar:,.2f}")
            
            # Mostrar detalhes
            print(f"\n📋 DETALHES DOS REGISTROS:")
            for idx, row in df_dia.iterrows():
                print(f"  • R$ {row['valor']:8.2f} - {row['empresa']} - {row['descricao'][:50]}...")
            
            # 6. Verificar se há contas pagas (como o Streamlit faz)
            df_pagas = supabase.buscar_contas_pagas()
            
            if not df_pagas.empty:
                df_pagas['data_vencimento'] = pd.to_datetime(df_pagas['data_vencimento'], errors='coerce')
                df_pagas_dia = df_pagas[df_pagas['data_vencimento'].dt.strftime('%Y-%m-%d') == data_filtro]
                total_pago = df_pagas_dia['valor'].sum() if not df_pagas_dia.empty else 0.0
            else:
                total_pago = 0.0
            
            print(f"💳 PAGO: R$ {total_pago:,.2f}")
            print(f"📊 DIFERENÇA: R$ {total_pago - total_a_pagar:,.2f}")
            
            print("\n" + "=" * 50)
            print("🎯 RESULTADO FINAL PARA O DASHBOARD:")
            print(f"A Pagar: {total_a_pagar:,.2f}")
            print(f"Pago: {total_pago:,.2f}")
            print(f"Dif: {total_pago - total_a_pagar:,.2f}")
            
        else:
            print("❌ Nenhum registro encontrado para essa data")
    else:
        print("❌ Nenhuma conta a pagar encontrada")

if __name__ == "__main__":
    main()
