"""
Lógica de processamento de arquivos para o Calendário Financeiro.

Contém funções para upload, detecção de formato, processamento e simulação.
"""

import streamlit as st
import pandas as pd
import uuid
from .cleanup_logic import remover_arquivo_temporario

def processar_arquivos(uploaded_a_pagar, uploaded_pagas, supabase_client, converter, processor):
    """
    Processa arquivos e salva no banco de dados.
    
    Args:
        uploaded_a_pagar: Lista de arquivos de contas a pagar
        uploaded_pagas: Lista de arquivos de contas pagas
        supabase_client: Cliente do Supabase
        converter: Conversor de arquivos
        processor: Processador de Excel
    """
    
    # Obter configuração de duplicatas
    verificar_duplicatas = st.session_state.get('verificar_duplicatas', True)
    
    with st.spinner("Processando arquivos e salvando no banco..."):
        try:
            processamento_id = supabase_client.registrar_processamento(
                tipo="upload_completo",
                status="em_andamento",
                detalhes={"inicio": str(st.session_state.get('user_data', {}).get('nome', 'Usuário'))},
                arquivos=[]
            )
            
            total_registros = 0
            total_duplicatas = 0
            arquivos_processados = []
            
            # Processar arquivos de contas a pagar
            if uploaded_a_pagar:
                st.info(f"📁 Processando {len(uploaded_a_pagar)} arquivo(s) de contas a pagar...")
                
                for uploaded_file in uploaded_a_pagar:
                    try:
                        # Detectar formato e processar
                        df_processado = detectar_e_processar_arquivo(uploaded_file, converter, processor)
                        
                        if not df_processado.empty:
                            # Salvar no banco com verificação de duplicatas
                            resultado = supabase_client.inserir_contas_a_pagar(
                                df_processado, 
                                arquivo_origem=uploaded_file.name,
                                processamento_id=processamento_id,
                                verificar_duplicatas=verificar_duplicatas
                            )
                            
                            if resultado["success"]:
                                total_registros += resultado["registros_inseridos"]
                                total_duplicatas += resultado.get("duplicatas_ignoradas", 0)
                                arquivos_processados.append(uploaded_file.name)
                                st.success(f"✅ {uploaded_file.name}: {resultado['registros_inseridos']} registros salvos")
                                if resultado.get("duplicatas_ignoradas", 0) > 0:
                                    st.info(f"ℹ️ {uploaded_file.name}: {resultado['duplicatas_ignoradas']} duplicatas ignoradas")
                            else:
                                st.error(f"❌ Erro ao salvar {uploaded_file.name}: {resultado['message']}")
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao processar {uploaded_file.name}: {str(e)}")
            
            # Processar arquivos de contas pagas
            if uploaded_pagas:
                st.info(f"📁 Processando {len(uploaded_pagas)} arquivo(s) de contas pagas...")
                
                for uploaded_file in uploaded_pagas:
                    try:
                        # Processar arquivo padrão
                        df_processado = processar_arquivo_padrao(uploaded_file, processor)
                        
                        if not df_processado.empty:
                            # Salvar no banco com verificação de duplicatas
                            resultado = supabase_client.inserir_contas_pagas(
                                df_processado,
                                arquivo_origem=uploaded_file.name,
                                processamento_id=processamento_id,
                                verificar_duplicatas=verificar_duplicatas
                            )
                            
                            if resultado["success"]:
                                total_registros += resultado["registros_inseridos"]
                                total_duplicatas += resultado.get("duplicatas_ignoradas", 0)
                                arquivos_processados.append(uploaded_file.name)
                                st.success(f"✅ {uploaded_file.name}: {resultado['registros_inseridos']} registros salvos")
                                if resultado.get("duplicatas_ignoradas", 0) > 0:
                                    st.info(f"ℹ️ {uploaded_file.name}: {resultado['duplicatas_ignoradas']} duplicatas ignoradas")
                            else:
                                st.error(f"❌ Erro ao salvar {uploaded_file.name}: {resultado['message']}")
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao processar {uploaded_file.name}: {str(e)}")
            
            # Finalizar processamento
            supabase_client.registrar_processamento(
                tipo="upload_completo",
                status="concluido",
                detalhes={
                    "total_registros": total_registros,
                    "total_duplicatas": total_duplicatas,
                    "arquivos_processados": len(arquivos_processados),
                    "verificar_duplicatas": verificar_duplicatas
                },
                arquivos=arquivos_processados
            )
            
            if total_registros > 0:
                mensagem = f"🎉 Processamento concluído! {total_registros} registros salvos no banco de dados."
                if total_duplicatas > 0:
                    mensagem += f" {total_duplicatas} duplicatas foram ignoradas."
                st.success(mensagem)
                st.balloons()
                # Forçar atualização dos dados
                st.rerun()
            else:
                if total_duplicatas > 0:
                    st.info(f"ℹ️ Processamento concluído! Nenhum registro novo encontrado. {total_duplicatas} duplicatas foram ignoradas.")
                else:
                    st.warning("⚠️ Nenhum registro foi processado.")
                
        except Exception as e:
            st.error(f"❌ Erro geral no processamento: {str(e)}")

def detectar_e_processar_arquivo(uploaded_file, converter, processor):
    """
    Detecta formato do arquivo e processa adequadamente.
    
    Args:
        uploaded_file: Arquivo enviado pelo usuário
        converter: Conversor de arquivos
        processor: Processador de Excel
    
    Returns:
        pd.DataFrame: DataFrame processado ou vazio em caso de erro
    """
    
    # Reset do buffer
    uploaded_file.seek(0)
    
    # Salvar arquivo temporário com nome único
    temp_path = f"temp_{uuid.uuid4().hex[:8]}_{uploaded_file.name}"
    
    try:
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        uploaded_file.seek(0)
        
        # Detectar formato Modelo_Contas_Pagar primeiro (mais específico)
        if converter.detectar_formato_modelo_contas_pagar(temp_path):
            st.info(f"📊 {uploaded_file.name} - Formato Modelo_Contas_Pagar detectado, convertendo...")
            df_convertido = converter.converter_modelo_contas_pagar(temp_path)
            
            if df_convertido is not None and not df_convertido.empty:
                st.success(f"✅ {uploaded_file.name} - {len(df_convertido)} registros convertidos do formato Modelo_Contas_Pagar")
                return df_convertido
            else:
                st.error(f"❌ Erro na conversão do formato Modelo_Contas_Pagar: {uploaded_file.name}")
                return pd.DataFrame()
        
        # Detectar se é formato ERP do cliente
        elif converter.detectar_formato_cliente(temp_path):
            st.info(f"🔄 {uploaded_file.name} - Formato ERP detectado, convertendo...")
            resultado = converter.processar_arquivo_completo(temp_path, salvar_convertido=False)
            
            if resultado['sucesso']:
                return resultado['dados_convertidos']
            else:
                st.error(f"❌ Erro na conversão ERP: {resultado['erro']}")
                return pd.DataFrame()
        
        # Formato padrão
        else:
            st.info(f"📋 {uploaded_file.name} - Formato padrão detectado")
            return processar_arquivo_padrao(uploaded_file, processor)
    
    finally:
        # Limpar arquivo temporário
        remover_arquivo_temporario(temp_path)

def processar_arquivo_padrao(uploaded_file, processor):
    """
    Processa arquivo no formato padrão.
    
    Args:
        uploaded_file: Arquivo enviado pelo usuário
        processor: Processador de Excel
    
    Returns:
        pd.DataFrame: DataFrame processado
    """
    
    # Salvar temporariamente com nome único
    temp_path = f"temp_padrao_{uuid.uuid4().hex[:8]}_{uploaded_file.name}"
    
    try:
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Carregar com o processor
        df = processor.carregar_arquivo_excel(temp_path)
        return df
    
    finally:
        remover_arquivo_temporario(temp_path)

def simular_reimportacao(df_excel, _nome_arquivo):
    """
    Simula o que aconteceria se o arquivo fosse reimportado.
    
    Args:
        df_excel: DataFrame processado do Excel
        _nome_arquivo: Nome do arquivo original (não utilizado atualmente)
    """
    try:
        # Importar cliente Supabase
        auth_mgr = st.session_state.get('auth_manager')
        if not auth_mgr:
            st.error("❌ Erro: Gerenciador de autenticação não encontrado")
            return
            
        supabase_client = auth_mgr.get_supabase_client()
        
        st.markdown("#### 🧪 Simulação de Re-importação")
        
        with st.spinner("Verificando duplicatas..."):
            # Simular verificação de duplicatas
            verificar_duplicatas = st.session_state.get('verificar_duplicatas', True)
            
            if verificar_duplicatas:
                duplicatas_info = supabase_client.verificar_duplicatas_contas_a_pagar(df_excel)
                
                registros_novos = duplicatas_info.get("novos", 0)
                duplicatas_encontradas = duplicatas_info.get("duplicatas", 0)
                total_registros = len(df_excel)
                
                st.markdown("##### 📊 Resultado da Simulação:")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "📄 Total no Arquivo",
                        total_registros,
                        "registros"
                    )
                
                with col2:
                    st.metric(
                        "✅ Seriam Importados",
                        registros_novos,
                        "novos registros"
                    )
                
                with col3:
                    st.metric(
                        "🔄 Duplicatas Ignoradas",
                        duplicatas_encontradas,
                        "já existem"
                    )
                
                # Explicação do que aconteceria
                if registros_novos > 0:
                    st.success(f"✅ **{registros_novos} registros novos** seriam importados para o banco de dados.")
                    
                    if duplicatas_encontradas > 0:
                        st.info(f"ℹ️ **{duplicatas_encontradas} duplicatas** seriam ignoradas (já existem no sistema).")
                    
                    st.markdown("**🎯 Conclusão:** Fazer o upload novamente importaria apenas os registros que ainda não estão no banco.")
                    
                else:
                    if duplicatas_encontradas > 0:
                        st.info(f"ℹ️ **Todos os {duplicatas_encontradas} registros já existem no sistema.** Nenhum seria importado.")
                    else:
                        st.warning("⚠️ **Nenhum registro seria importado.** Posível problema no arquivo ou configuração.")
                
                # Mostrar registros que seriam importados
                if registros_novos > 0 and 'df_novos' in duplicatas_info:
                    st.markdown("#### 📋 Registros que seriam importados:")
                    st.dataframe(duplicatas_info['df_novos'].head(10), use_container_width=True, hide_index=True)
            
            else:
                st.warning("⚠️ **Verificação de duplicatas desabilitada:** Todos os registros seriam importados, podendo gerar duplicatas no banco.")
                st.info("💡 **Recomendação:** Ative a verificação de duplicatas no sidebar antes de fazer o upload.")
        
        # Diagnóstico do motivo dos registros faltantes
        st.markdown("---")
        st.markdown("##### 🔍 **Por que alguns registros não foram importados?**")
        
        st.markdown("""
        **Possíveis motivos pelos quais registros podem ter sido excluídos na importação original:**
        
        1. **🚫 Valores zerados ou vazios**: Registros com valor = 0 ou campo vazio são automaticamente filtrados
        2. **📅 Datas inválidas**: Registros sem data de vencimento válida são removidos
        3. **🏢 Empresas vazias**: Registros sem nome da empresa são filtrados
        4. **🔄 Duplicatas**: Se a verificação estava ativada, registros duplicados foram ignorados
        5. **💥 Erros de conversão**: Campos que não puderam ser convertidos (ex: texto em campo numérico)
        """)
        
        # Recomendações
        st.markdown("##### 💡 **Recomendações:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🔧 Para importar registros faltantes:**
            - ✅ Verificar se verificação de duplicatas está ativada
            - ✅ Fazer upload novamente do mesmo arquivo
            - ✅ Apenas registros novos serão importados
            """)
        
        with col2:
            st.markdown("""
            **⚠️ Para evitar problemas futuros:**
            - 📊 Verificar dados antes do upload (sem valores zerados)  
            - 📅 Confirmar que todas as datas estão preenchidas
            - 🏢 Verificar se todas as empresas estão nomeadas
            """)
            
    except Exception as e:
        st.error(f"❌ Erro na simulação: {str(e)}")
