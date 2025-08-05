import pandas as pd
import sys
sys.path.append('src')
from client_file_converter import ClientFileConverter

# Testar a conversão do arquivo
arquivo = 'ArquivosModeloCliente/Modelo_Contas_Pagar.xlsx'
converter = ClientFileConverter()

print("=== TESTE DE CONVERSÃO ===")

# 1. Verificar detecção de formato
print("1. Testando detecção de formato...")
eh_modelo_contas_pagar = converter.detectar_formato_modelo_contas_pagar(arquivo)
print(f"É formato Modelo_Contas_Pagar: {eh_modelo_contas_pagar}")

# 2. Testar conversão
print("\n2. Testando conversão...")
df_convertido = converter.converter_modelo_contas_pagar(arquivo)

if df_convertido is not None:
    print(f"Conversão bem-sucedida! {len(df_convertido)} registros convertidos")
    print("\nColunas do DataFrame convertido:")
    print(list(df_convertido.columns))
    
    # Verificar fornecedores
    if 'fornecedor' in df_convertido.columns:
        print("\nFornecedores únicos no DataFrame convertido (primeiros 10):")
        fornecedores_convertidos = df_convertido['fornecedor'].dropna().unique()
        for i, fornecedor in enumerate(fornecedores_convertidos[:10]):
            print(f"{i+1}: {repr(fornecedor)}")
            
        print(f"\nTotal de fornecedores únicos no convertido: {len(fornecedores_convertidos)}")
        print(f"Valores vazios na coluna fornecedor: {df_convertido['fornecedor'].isna().sum()}")
        print(f"Valores vazios (string vazia): {(df_convertido['fornecedor'] == '').sum()}")
        
        # Mostrar algumas linhas de exemplo
        print("\nPrimeiras 3 linhas do DataFrame convertido:")
        colunas_exemplo = ['empresa', 'fornecedor', 'valor', 'descricao', 'data_vencimento']
        df_exemplo = df_convertido[colunas_exemplo].head(3)
        print(df_exemplo)
        
    else:
        print("ERRO: Coluna 'fornecedor' não foi criada no DataFrame convertido!")
        
else:
    print("ERRO: Conversão falhou!")
