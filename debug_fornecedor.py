import pandas as pd
import sys
sys.path.append('src')

# Ler o arquivo para verificar a estrutura
arquivo = 'ArquivosModeloCliente/Modelo_Contas_Pagar.xlsx'
try:
    # Verificar as abas
    excel_file = pd.ExcelFile(arquivo)
    print('Abas disponíveis:', excel_file.sheet_names)
    
    # Ler a aba 'Contas a Pagar'
    df = pd.read_excel(arquivo, sheet_name='Contas a Pagar')
    print('\nColunas do arquivo:', list(df.columns))
    print('\nTamanho do DataFrame:', df.shape)
    
    # Verificar dados da coluna Fornecedor especificamente
    if 'Fornecedor' in df.columns:
        print('\nPrimeiros 10 fornecedores únicos:')
        fornecedores = df['Fornecedor'].dropna().unique()
        for i, fornecedor in enumerate(fornecedores[:10]):
            print(f"{i+1}: {repr(fornecedor)}")
            
        print(f'\nTotal de fornecedores únicos: {len(fornecedores)}')
        print(f'Valores vazios na coluna Fornecedor: {df["Fornecedor"].isna().sum()}')
        print(f'Valores não vazios: {df["Fornecedor"].notna().sum()}')
        
        # Mostrar algumas linhas completas para debug
        print('\nPrimeiras 3 linhas com dados completos:')
        colunas_importantes = ['Empresa', 'Fornecedor', 'ValorDoc', 'Histórico', 'DataVencimento']
        for col in colunas_importantes:
            if col in df.columns:
                print(f"Coluna {col} existe")
            else:
                print(f"ATENÇÃO: Coluna {col} NÃO existe")
        
        print('\nDados das primeiras 3 linhas:')
        df_sample = df[colunas_importantes].head(3) if all(col in df.columns for col in colunas_importantes) else df.head(3)
        print(df_sample)
    else:
        print('\nATENÇÃO: Coluna Fornecedor não encontrada!')
        print('Colunas similares encontradas:')
        for col in df.columns:
            if 'fornec' in col.lower() or 'vendor' in col.lower() or 'supplier' in col.lower():
                print(f"- {col}")
        
except Exception as e:
    print(f'Erro: {e}')
    import traceback
    traceback.print_exc()
