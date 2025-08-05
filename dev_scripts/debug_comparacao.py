#!/usr/bin/env python3
"""
Script para comparar consultas SQL diretas vs função Streamlit
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.supabase_client import SupabaseClient
import pandas as pd

def main():
    print("🔍 COMPARANDO CONSULTAS: SQL DIRETO vs STREAMLIT")
    print("=" * 60)
    
    # Inicializar cliente
    supabase = SupabaseClient()
    user_id = "bde0a328-7d9f-4c91-a005-a1ee285c16fb"
    data_especifica = "2025-08-05"
    
    print(f"📅 Data analisada: {data_especifica}")
    print(f"👤 User ID: {user_id}")
    print()
    
    # 1. CONSULTA DIRETA (mesma do debug_valores.py)
    print("1️⃣ CONSULTA SQL DIRETA:")
    try:
        # Query direta com filtro de data
        response = supabase.supabase.table("contas_a_pagar").select("*").eq("usuario_id", user_id).eq("data_vencimento", data_especifica).limit(10000).execute()
        
        df_direto = pd.DataFrame(response.data)
        print(f"Registros retornados: {len(df_direto)}")
        
        if not df_direto.empty:
            total_direto = df_direto['valor'].sum()
            print(f"Total: R$ {total_direto:,.2f}")
            
            # Mostrar alguns valores
            print("\n📋 VALORES (primeiros 10):")
            for idx, row in df_direto.head(10).iterrows():
                print(f"  • R$ {row['valor']:,.2f} - {row['empresa']} - {row['descricao']}")
        
    except Exception as e:
        print(f"❌ Erro na consulta direta: {e}")
    
    print("\n" + "-" * 60)
    
    # 2. CONSULTA VIA FUNÇÃO STREAMLIT
    print("2️⃣ CONSULTA VIA FUNÇÃO STREAMLIT:")
    try:
        supabase.set_user_id(user_id)
        df_streamlit = supabase.buscar_contas_a_pagar()
        
        print(f"Total de registros: {len(df_streamlit)}")
        
        if not df_streamlit.empty:
            # Filtrar para a data específica
            df_streamlit['data_vencimento'] = pd.to_datetime(df_streamlit['data_vencimento'])
            df_dia = df_streamlit[df_streamlit['data_vencimento'].dt.strftime('%Y-%m-%d') == data_especifica]
            
            print(f"Registros para {data_especifica}: {len(df_dia)}")
            
            if not df_dia.empty:
                total_streamlit = df_dia['valor'].sum()
                print(f"Total: R$ {total_streamlit:,.2f}")
                
                # Mostrar alguns valores
                print("\n📋 VALORES (primeiros 10):")
                for idx, row in df_dia.head(10).iterrows():
                    print(f"  • R$ {row['valor']:,.2f} - {row['empresa']} - {row['descricao']}")
        
    except Exception as e:
        print(f"❌ Erro na consulta Streamlit: {e}")
    
    print("\n" + "=" * 60)
    
    # 3. ANÁLISE COMPARATIVA
    print("3️⃣ ANÁLISE COMPARATIVA:")
    
    if 'df_direto' in locals() and 'df_dia' in locals() and not df_direto.empty and not df_dia.empty:
        print(f"Consulta direta: {len(df_direto)} registros")
        print(f"Consulta Streamlit: {len(df_dia)} registros")
        print(f"Diferença: {len(df_direto) - len(df_dia)} registros")
        
        # Comparar IDs se possível
        if 'id' in df_direto.columns and 'id' in df_dia.columns:
            ids_direto = set(df_direto['id'].astype(str))
            ids_streamlit = set(df_dia['id'].astype(str))
            
            apenas_direto = ids_direto - ids_streamlit
            apenas_streamlit = ids_streamlit - ids_direto
            
            print(f"\nIDs apenas na consulta direta: {len(apenas_direto)}")
            print(f"IDs apenas na consulta Streamlit: {len(apenas_streamlit)}")
            
            if apenas_direto:
                print("Primeiros IDs só na consulta direta:", list(apenas_direto)[:5])
    
    print("\n🔍 Comparação concluída!")

if __name__ == "__main__":
    main()
