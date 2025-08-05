-- Execute estas queries no SQL Editor do Supabase para diagnosticar o problema

-- 1. Verificar se há dados na tabela
SELECT COUNT(*) as total_registros FROM contas_a_pagar;

-- 2. Verificar primeiros registros
SELECT * FROM contas_a_pagar LIMIT 5;

-- 3. Verificar user_ids únicos
SELECT usuario_id, COUNT(*) as quantidade 
FROM contas_a_pagar 
GROUP BY usuario_id;

-- 4. Verificar se RLS está ativo
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE tablename = 'contas_a_pagar';

-- 5. Verificar políticas RLS
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies 
WHERE tablename = 'contas_a_pagar';

-- 6. Verificar registros para o user_id específico
SELECT COUNT(*) as registros_user, SUM(valor) as total_valor
FROM contas_a_pagar 
WHERE usuario_id = 'bde0a328-7d9f-4c91-a005-a1ee285c16fb';

-- 7. Verificar registros para 05/08/2025
SELECT COUNT(*) as registros_dia, SUM(valor) as total_dia
FROM contas_a_pagar 
WHERE data_vencimento = '2025-08-05' 
AND usuario_id = 'bde0a328-7d9f-4c91-a005-a1ee285c16fb';

-- 8. Se RLS estiver ativo, temporariamente desabilitá-lo para teste
-- ALTER TABLE contas_a_pagar DISABLE ROW LEVEL SECURITY;

-- 9. QUERY ADICIONAL: Verificar TODOS os registros do dia 05/08/2025 (sem filtro de user_id)
SELECT COUNT(*) as total_registros_05_08, SUM(valor) as total_valor_05_08
FROM contas_a_pagar 
WHERE data_vencimento = '2025-08-05';

-- 10. Verificar se há RLS ativo na tabela
SELECT tablename, rowsecurity FROM pg_tables WHERE tablename = 'contas_a_pagar';
