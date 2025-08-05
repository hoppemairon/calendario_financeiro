#!/usr/bin/env python3
"""
Script para debugar diferenças entre valores do banco e interface
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.supabase_client import SupabaseClient
import pandas as pd
from datetime import datetime

def main():
    print("🔍 DEBUGANDO DIFERENÇAS ENTRE BANCO E INTERFACE")
    print("=" * 60)
    
    # Inicializar cliente
    supabase = SupabaseClient()
    user_id = "bde0a328-7d9f-4c91-a005-a1ee285c16fb"
    data_especifica = "2025-08-05"
    
    print(f"📅 Analisando data: {data_especifica}")
    print(f"👤 User ID: {user_id}")
    print()
    
    # Definir user_id no cliente
    supabase.set_user_id(user_id)
    
    # 1. Buscar dados direto do banco (mesma função usada pelo Streamlit)
    print("1️⃣ DADOS DIRETO DO BANCO (função do Streamlit):")
    try:
        contas_a_pagar_df = supabase.buscar_contas_a_pagar()
        print(f"Total de registros retornados: {len(contas_a_pagar_df)}")
        
        # O DataFrame já vem pronto da função
        df = contas_a_pagar_df
        
        if not df.empty:
            # Garantir que data_vencimento é datetime
            df['data_vencimento'] = pd.to_datetime(df['data_vencimento'])
            
            # Filtrar para a data específica
            df_dia = df[df['data_vencimento'].dt.strftime('%Y-%m-%d') == data_especifica]
            
            print(f"Registros para {data_especifica}: {len(df_dia)}")
            
            if not df_dia.empty:
                # Mostrar primeiros registros
                print("\n📋 PRIMEIROS 5 REGISTROS:")
                for idx, row in df_dia.head().iterrows():
                    print(f"  • {row['empresa']}: R$ {row['valor']:.2f} - {row['descricao']}")
                
                # Calcular total
                total_interface = df_dia['valor'].sum()
                print(f"\n💰 TOTAL CALCULADO (interface): R$ {total_interface:,.2f}")
                
                # Verificar tipos de dados
                print(f"\n🔍 ANÁLISE DOS VALORES:")
                print(f"Tipo da coluna 'valor': {df_dia['valor'].dtype}")
                print(f"Valores únicos (primeiros 10): {df_dia['valor'].head(10).tolist()}")
                
                # Verificar se há valores duplicados
                duplicados = df_dia.duplicated().sum()
                print(f"Registros duplicados: {duplicados}")
                
                # Análise estatística
                print(f"\n📊 ESTATÍSTICAS DOS VALORES:")
                print(f"Valor mínimo: R$ {df_dia['valor'].min():.2f}")
                print(f"Valor máximo: R$ {df_dia['valor'].max():.2f}")
                print(f"Valor médio: R$ {df_dia['valor'].mean():.2f}")
                print(f"Soma total: R$ {df_dia['valor'].sum():.2f}")
                
            else:
                print("❌ Nenhum registro encontrado para essa data")
        else:
            print("❌ DataFrame vazio")
            
    except Exception as e:
        print(f"❌ Erro ao buscar dados: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 Debug concluído!")

if __name__ == "__main__":
    main()
