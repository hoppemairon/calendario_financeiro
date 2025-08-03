import pandas as pd

# Ler o arquivo
df = pd.read_excel('ArquivosModeloCliente/Mov_Financeiro_Data_Vencimento_02082025.xls')

print("=== ANÁLISE DO ARQUIVO MODELO DO CLIENTE ===\n")
print(f"Tamanho: {df.shape}")
print(f"Colunas: {list(df.columns)}")

print("\n=== PRIMEIRAS 15 LINHAS ===")
for i in range(min(15, len(df))):
    print(f"Linha {i}: {df.iloc[i].tolist()}")

print("\n=== BUSCANDO CABEÇALHOS REAIS ===")
# Procurar por linhas que podem ser cabeçalhos
for i in range(min(20, len(df))):
    linha = df.iloc[i]
    if any('empresa' in str(val).lower() if pd.notna(val) else False for val in linha):
        print(f"Possível cabeçalho na linha {i}: {linha.tolist()}")
    elif any('data' in str(val).lower() if pd.notna(val) else False for val in linha):
        print(f"Possível cabeçalho na linha {i}: {linha.tolist()}")
    elif any('valor' in str(val).lower() if pd.notna(val) else False for val in linha):
        print(f"Possível cabeçalho na linha {i}: {linha.tolist()}")
