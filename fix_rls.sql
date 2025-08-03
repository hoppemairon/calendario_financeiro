-- FIX PARA ROW LEVEL SECURITY
-- Execute este SQL no Supabase SQL Editor

-- Remover política atual da tabela usuarios
DROP POLICY IF EXISTS "Usuários podem ver apenas seus próprios dados" ON usuarios;

-- Criar nova política que permite inserção durante cadastro
CREATE POLICY "Usuários podem gerenciar seus próprios dados" ON usuarios
    FOR ALL USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Política específica para permitir inserção inicial (quando o usuário se cadastra)
CREATE POLICY "Permitir inserção durante cadastro" ON usuarios
    FOR INSERT WITH CHECK (true);

-- Política para atualização apenas dos próprios dados
CREATE POLICY "Usuários podem atualizar apenas seus dados" ON usuarios
    FOR UPDATE USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Política para visualização apenas dos próprios dados
CREATE POLICY "Usuários podem ver apenas seus dados" ON usuarios
    FOR SELECT USING (auth.uid() = id);
