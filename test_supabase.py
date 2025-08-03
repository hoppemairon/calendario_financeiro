"""
Teste de Conexão com Supabase
"""

import sys
sys.path.append('src')

from database.supabase_client import SupabaseClient

def testar_conexao():
    """Testa a conexão com o Supabase."""
    
    try:
        print("🔄 Testando conexão com Supabase...")
        
        # Criar cliente
        client = SupabaseClient()
        
        print("✅ Cliente Supabase criado com sucesso!")
        print(f"📡 URL: {client.url}")
        print(f"🔑 Key: {client.key[:20]}...")
        
        # Testar uma consulta simples
        print("\n🔄 Testando consulta de teste...")
        
        # Tentar buscar tabelas
        response = client.supabase.table("usuarios").select("count", count="exact").execute()
        
        print(f"✅ Conexão funcionando! Tabela 'usuarios' existe.")
        print(f"📊 Total de usuários: {response.count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão: {str(e)}")
        print("\n💡 Possíveis soluções:")
        print("1. Verifique se o SQL foi executado no Supabase")
        print("2. Confirme as credenciais no arquivo .env")
        print("3. Verifique se o projeto Supabase está ativo")
        return False

if __name__ == "__main__":
    testar_conexao()
