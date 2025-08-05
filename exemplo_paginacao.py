# Exemplo de como implementar paginação no Supabase

def buscar_contas_a_pagar_completo(self, empresa: str = None):
    """Busca TODAS as contas a pagar usando paginação."""
    todos_registros = []
    offset = 0
    batch_size = 1000
    
    while True:
        query = (self.supabase
                .table("contas_a_pagar")
                .select("*")
                .eq("usuario_id", self.user_id)
                .order("data_vencimento", desc=False)
                .order("id", desc=False)
                .range(offset, offset + batch_size - 1)  # Paginação
                )
        
        if empresa:
            query = query.eq("empresa", empresa)
        
        response = query.execute()
        
        if not response.data:
            break
            
        todos_registros.extend(response.data)
        
        # Se retornou menos que batch_size, chegamos ao fim
        if len(response.data) < batch_size:
            break
            
        offset += batch_size
    
    return pd.DataFrame(todos_registros)