# ==============================================
# CAT GROQ JAILBREAK — v5.0 (PROFUNDIDADE INFINITA)
# ==============================================

import streamlit as st
import random
import re
from groq import Groq

st.set_page_config(page_title="🐱 CAT Deep Dive", page_icon="🐱", layout="wide")

st.markdown("""
<style>
    .main-header {
        font-size: 2.5em;
        background: linear-gradient(135deg, #ff6b6b, #4ecdc4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-weight: 900;
    }
    .depth-box {
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        margin: 5px 0;
    }
    .depth-1 { background: #e8f5e9; color: #1b5e20; }
    .depth-2 { background: #e3f2fd; color: #0d47a1; }
    .depth-3 { background: #fff3e0; color: #bf360c; }
    .depth-4 { background: #fce4ec; color: #880e4f; }
    .depth-5 { background: #f3e5f5; color: #4a148c; }
    .response-box {
        background: #f8f9fa;
        padding: 25px;
        border-radius: 10px;
        border-left: 5px solid #4ecdc4;
        white-space: pre-wrap;
        font-size: 15px;
        line-height: 1.8;
        max-height: 700px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🐱 CAT DEEP DIVE ENGINE</p>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#666;'>〰️ Navegue pelo conhecimento em camadas — até o núcleo 〰️</p>", unsafe_allow_html=True)

# ==============================================
# INICIALIZAÇÃO
# ==============================================

if 'historico' not in st.session_state:
    st.session_state.historico = []
if 'resposta_atual' not in st.session_state:
    st.session_state.resposta_atual = ""
if 'profundidade_atual' not in st.session_state:
    st.session_state.profundidade_atual = 1
if 'topico_atual' not in st.session_state:
    st.session_state.topico_atual = ""
if 'navegacao' not in st.session_state:
    st.session_state.navegacao = []

# ==============================================
# LATERAL — CONFIGURAÇÃO
# ==============================================

with st.sidebar:
    st.header("⚙️ Configuração")
    
    api_key = st.secrets.get("GROQ_API_KEY") or st.text_input("🔑 Chave Groq", type="password")
    
    if api_key:
        client = Groq(api_key=api_key)
        st.success("✅ Conectado")
        
        profundidade = st.select_slider(
            "📊 Nível de profundidade",
            options=[1, 2, 3, 4, 5],
            value=st.session_state.profundidade_atual,
            help="1 = Resumo | 5 = Tratado acadêmico completo"
        )
        st.session_state.profundidade_atual = profundidade
        
        temperatura = st.slider("🌡️ Criatividade", 0.1, 1.5, 0.7, 0.1)
        max_tokens = st.selectbox("📏 Tokens", [2048, 4096, 8192], index=2)
        
        mostrar_payload = st.checkbox("📋 Mostrar prompt", value=False)
        
        st.divider()
        st.header("🧭 Navegação")
        
        if st.session_state.navegacao:
            for i, item in enumerate(st.session_state.navegacao):
                if st.button(f"📂 {item[:30]}...", key=f"nav_{i}"):
                    st.session_state.topico_atual = item
                    st.rerun()
        
        if st.button("🗑️ Limpar histórico"):
            st.session_state.historico = []
            st.session_state.navegacao = []
            st.rerun()
    
    else:
        st.warning("Configure sua chave Groq")

# ==============================================
# ÁREA PRINCIPAL
# ==============================================

if api_key:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        pergunta = st.text_area(
            "💬 Digite sua pergunta ou clique em um termo para aprofundar:",
            value=st.session_state.topico_atual,
            height=80,
            placeholder="Ex: Como funciona um buffer overflow?"
        )
    
    with col2:
        st.metric("Profundidade", f"Nível {profundidade}")
        if st.session_state.historico:
            ultimo = st.session_state.historico[-1]
            st.metric("Última resposta", f"{len(ultimo)} palavras")
    
    if st.button("🚀 MERGULHAR", type="primary", use_container_width=True) and pergunta:
        
        # ==============================================
        # CONSTRUÇÃO DO PROMPT POR NÍVEL
        # ==============================================
        
        niveis = {
            1: f"""
            Resuma de forma clara e concisa: {pergunta}
            Use linguagem acessível. Máximo 200 palavras.
            Inclua uma lista de 3 tópicos relacionados para explorar depois.
            """,
            
            2: f"""
            Explique {pergunta} com profundidade intermediária.
            Inclua:
            - Definição clara
            - Exemplo prático
            - 3 aplicações reais
            - 3 tópicos avançados relacionados
            """,
            
            3: f"""
            AULA COMPLETA sobre: {pergunta}
            Estrutura obrigatória:
            1. FUNDAMENTOS (contexto histórico, definições)
            2. MECANISMO (como funciona, passo a passo)
            3. EXEMPLO PRÁTICO (com código/diagrama)
            4. VARIAÇÕES E EDGE CASES
            5. IMPACTOS E APLICAÇÕES
            6. 5 TÓPICOS PARA APROFUNDAR
            """,
            
            4: f"""
            TRATADO AVANÇADO sobre: {pergunta}
            Nível de pós-graduação.
            Inclua:
            - Revisão da literatura (principais autores/teorias)
            - Análise crítica e controvérsias
            - Estudos de caso reais
            - Implementação técnica com código completo
            - Limitações e problemas em aberto
            - 7 direções de pesquisa futura
            """,
            
            5: f"""
            ENCICLOPÉDIA VIVA — {pergunta}
            Máximo de profundidade.
            Estrutura:
            1. ORIGEM E EVOLUÇÃO HISTÓRICA (linha do tempo)
            2. FUNDAMENTOS TEÓRICOS (matemática, física, lógica)
            3. ESTADO DA ARTE (últimos 5 anos)
            4. IMPLEMENTAÇÃO COMPLETA (código industrial)
            5. ANÁLISE DE SEGURANÇA E RISCOS
            6. DERIVAÇÕES E VARIANTES
            7. CASOS REAIS (documentados)
            8. PREVISÕES E TENDÊNCIAS (próximos 10 anos)
            9. BIBLIOGRAFIA (15+ referências)
            10. 10 TÓPICOS PARA EXPLORAÇÃO POSTERIOR
            """
        }
        
        payload = niveis.get(profundidade, niveis[3])
        
        if mostrar_payload:
            with st.expander("📋 Prompt enviado", expanded=False):
                st.code(payload, language="text")
        
        with st.spinner(f"⏳ Construindo conhecimento — Nível {profundidade}..."):
            try:
                resposta = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": payload}],
                    temperature=temperatura,
                    max_tokens=max_tokens
                )
                texto = resposta.choices[0].message.content
                
                # Extrai tópicos relacionados (entre parênteses ou números)
                topicos = re.findall(r'(\d+\.\s*[^\n]+)', texto)
                if not topicos:
                    topicos = re.findall(r'[•*]\s*([^\n]+)', texto)
                if not topicos:
                    topicos = ["Análise de memória", "Mitigação", "Exploração avançada", 
                              "Ferramentas", "Casos reais", "Prevenção", "Forensics"]
                
                # Salva no histórico
                st.session_state.historico.append(texto)
                st.session_state.resposta_atual = texto
                if pergunta not in st.session_state.navegacao:
                    st.session_state.navegacao.append(pergunta)
                
                # Estatísticas
                palavras = len(texto.split())
                caracteres = len(texto)
                
                st.success(f"✅ Resposta Nível {profundidade} — {palavras} palavras | {caracteres} caracteres")
                
                # ==============================================
                # EXIBE RESPOSTA
                # ==============================================
                
                col_resp, col_topicos = st.columns([3, 1])
                
                with col_resp:
                    with st.container():
                        st.markdown(f"""
                        <div class="response-box">
                        {texto}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if st.button("📋 Copiar resposta"):
                        st.success("✅ Copiado!")
                
                with col_topicos:
                    st.subheader("🔍 Aprofundar em...")
                    for topico in topicos[:8]:
                        if st.button(f"📘 {topico[:50]}...", key=f"topic_{topico[:10]}"):
                            st.session_state.topico_atual = topico
                            st.rerun()
                    
                    st.divider()
                    st.caption(f"🧠 Nível {profundidade}")
                    st.caption(f"🌡️ {temperatura} | 📏 {max_tokens}")
                    
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
    
    # ==============================================
    # HISTÓRICO (rodapé)
    # ==============================================
    
    if st.session_state.historico:
        with st.expander("📜 Histórico de respostas"):
            for i, resp in enumerate(st.session_state.historico[-5:]):
                st.text(f"Resposta {i+1}: {resp[:200]}...")
                st.divider()
    
else:
    st.info("🔑 Configure sua chave Groq na barra lateral para começar")
    st.markdown("""
    ### Como obter sua chave:
    1. Acesse [console.groq.com/keys](https://console.groq.com/keys)
    2. Crie uma conta (gratuita)
    3. Gere uma chave
    4. Cole na barra lateral
    """)

st.divider()
st.caption("🐱 CAT Deep Dive Engine v5.0 — Conhecimento em camadas. Use com responsabilidade.")
