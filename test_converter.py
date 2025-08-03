import sys
sys.path.append('src')

from client_file_converter import ClientFileConverter
import pandas as pd

# Criar instância do conversor
conversor = ClientFileConverter()

# Processar o arquivo modelo
arquivo_modelo = "ArquivosModeloCliente/Mov_Financeiro_Data_Vencimento_02082025.xls"

print("=== TESTE DO CONVERSOR ===\n")

# Detectar formato
print("1. Detectando formato...")
is_client_format = conversor.detectar_formato_cliente(arquivo_modelo)
print(f"   Formato do cliente detectado: {is_client_format}")

if is_client_format:
    print("\n2. Processando arquivo completo...")
    resultado = conversor.processar_arquivo_completo(arquivo_modelo, salvar_convertido=True)
    
    if resultado['sucesso']:
        print("   ✅ Conversão realizada com sucesso!")
        
        # Mostrar relatório
        relatorio = resultado['relatorio']
        print(f"\n3. Relatório da conversão:")
        print(f"   - Registros convertidos: {relatorio['registros_convertidos']}")
        print(f"   - Registros válidos: {relatorio['registros_validos']}")
        print(f"   - Valor total: R$ {relatorio['valor_total']:,.2f}")
        print(f"   - Empresas únicas: {relatorio['empresas_unicas']}")
        print(f"   - Período: {relatorio['periodo_vencimentos']['inicio'].strftime('%d/%m/%Y')} a {relatorio['periodo_vencimentos']['fim'].strftime('%d/%m/%Y')}")
        
        # Mostrar amostra dos dados
        df = resultado['dados_convertidos']
        print(f"\n4. Amostra dos dados convertidos (primeiras 5 linhas):")
        print(df[['empresa', 'valor', 'data_vencimento', 'categoria', 'descricao']].head())
        
        print(f"\n5. Arquivo convertido salvo em: {resultado['arquivo_convertido']}")
        
    else:
        print(f"   ❌ Erro na conversão: {resultado['erro']}")
else:
    print("   ❌ Arquivo não está no formato esperado")
