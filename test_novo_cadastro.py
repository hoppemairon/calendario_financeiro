"""
Teste de Cadastro com Email Diferente
"""

import sys
sys.path.append('src')

from database.supabase_client import SupabaseClient
import time
import random

def testar_cadastro_novo():
    """Testa o cadastro com um email único."""
    
    try:
        print("🔄 Testando cadastro com email único...")
        
        # Criar cliente
        client = SupabaseClient()
        
        # Gerar email único
        timestamp = int(time.time())
        random_num = random.randint(100, 999)
        email_teste = f"teste{timestamp}{random_num}@exemplo.com"
        senha_teste = "teste123456"
        nome_teste = "Usuário Teste Novo"
        
        print(f"📧 Email: {email_teste}")
        print(f"🔑 Senha: {senha_teste}")
        print(f"👤 Nome: {nome_teste}")
        
        # Tentar cadastrar
        print("\n🔄 Tentando cadastrar...")
        resultado = client.sign_up(email_teste, senha_teste, nome_teste, "Empresa Teste")
        
        print(f"\n📊 Resultado:")
        print(f"✅ Sucesso: {resultado['success']}")
        print(f"💬 Mensagem: {resultado['message']}")
        
        if not resultado['success']:
            print(f"❌ Erro: {resultado.get('error', 'Erro desconhecido')}")
        
        return resultado['success']
        
    except Exception as e:
        print(f"❌ Erro na função de teste: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 TESTE DE CADASTRO COM EMAIL ÚNICO\n")
    testar_cadastro_novo()
