"""
Teste de Cadastro de Usuário
"""

import sys
sys.path.append('src')

from database.supabase_client import SupabaseClient

def testar_cadastro():
    """Testa o cadastro de usuário."""
    
    try:
        print("🔄 Testando cadastro de usuário...")
        
        # Criar cliente
        client = SupabaseClient()
        
        # Dados de teste
        email_teste = "teste@exemplo.com"
        senha_teste = "teste123"
        nome_teste = "Usuário Teste"
        
        print(f"📧 Email: {email_teste}")
        print(f"🔑 Senha: {senha_teste}")
        print(f"👤 Nome: {nome_teste}")
        
        # Tentar cadastrar
        print("\n🔄 Tentando cadastrar...")
        resultado = client.sign_up(email_teste, senha_teste, nome_teste)
        
        print(f"\n📊 Resultado:")
        print(f"✅ Sucesso: {resultado['success']}")
        
        if resultado['success']:
            print(f"💬 Mensagem: {resultado['message']}")
            print(f"👤 Usuário ID: {resultado['user'].id}")
        else:
            print(f"❌ Erro: {resultado.get('error', 'Erro desconhecido')}")
            print(f"💬 Mensagem: {resultado['message']}")
        
        return resultado['success']
        
    except Exception as e:
        print(f"❌ Erro na função de teste: {str(e)}")
        import traceback
        print("\n🔍 Traceback completo:")
        traceback.print_exc()
        return False

def testar_tabela_usuarios():
    """Testa se a tabela usuarios existe e está configurada corretamente."""
    
    try:
        print("\n🔄 Testando estrutura da tabela usuarios...")
        
        client = SupabaseClient()
        
        # Tentar fazer uma consulta simples
        response = client.supabase.table("usuarios").select("*").limit(1).execute()
        
        print("✅ Tabela 'usuarios' acessível")
        print(f"📊 Dados retornados: {len(response.data)} registros")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao acessar tabela usuarios: {str(e)}")
        
        # Verificar se o problema é RLS
        if "row-level security" in str(e).lower() or "rls" in str(e).lower():
            print("💡 Possível problema: Row Level Security (RLS)")
            print("   Verifique as políticas de segurança no Supabase")
        
        return False

if __name__ == "__main__":
    print("🧪 TESTE DE CADASTRO DE USUÁRIO\n")
    
    # Testar estrutura
    testar_tabela_usuarios()
    
    # Testar cadastro
    testar_cadastro()
