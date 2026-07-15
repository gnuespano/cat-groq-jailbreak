# ==============================================
# CAT DEEP DIVE ENGINE — v6.0 (EXPLORADOR TOTAL)
# Funcionalidades: 5 níveis + Perguntas sugeridas + PDF + Modo Escuro
# ==============================================

import streamlit as st
import random
import re
import base64
from groq import Groq
from datetime import datetime

st.set_page_config(page_title="🐱 CAT Deep Dive", page_icon="🐱", layout="wide")

# ==============================================
# CSS + TEMA ESCURO/CLARO
# ==============================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.8em;
        background: linear-gradient(135deg, #ff6b6b, #4ecdc4, #45b7d1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-weight: 900;
    }
    .sub-header {
        text-align: center;
        color: #888;
        font-size: 1.1em;
        margin-bottom: 2em;
    }
    .depth-box {
        padding: 12px 20px;
        border-radius: 25px;
        text-align: center;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
    }
    .depth-1 { background: #e8f5e9; color: #1b5e20; }
    .depth-2 { background: #e3f2fd; color: #0d47a1; }
    .depth-3 { background: #fff3e0; color: #bf360c; }
    .depth-4 { background: #fce4ec; color: #880e4f; }
    .depth-5 { background: #f3e5f5; color: #4a148c; }
    
    .response-box {
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 25px;
        border-radius: 12px;
        border-left: 5px solid #4ecdc4;
        white-space: pre-wrap;
        font-size: 15px;
        line-height: 1.8;
        max-height: 700px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
    }
    .response-box-light {
        background: #f8f9fa;
        color: #222;
        border-left: 5px solid #4ecdc4;
    }
    .suggestion-btn {
        background: #2d2d2d;
        color: #4ecdc4;
        border: 1px solid #4ecdc4;
        border-radius: 20px;
        padding: 8px 16px;
        margin: 4px;
        cursor: pointer;
        font-size: 13px;
        transition: 0.3s;
    }
    .suggestion-btn:hover {
        background: #4ecdc4;
        color: #1e1e1e;
    }
    .stButton button {
        border-radius: 25px !important;
        font-weight: 600 !important;
    }
    .download-btn {
        background: #4ecdc4 !important;
        color: #1e1e1e !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🐱 CAT DEEP DIVE ENGINE</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">〰️ Conhecimento em camadas — perguntas sugeridas — PDF — Modo escuro 〰️</p>', unsafe_allow_html=True)

# ==============================================
# INICIALIZAÇÃO
# ==============================================

if 'historico' not in st.session_state:
    st.session_state.historico = []
if 'resposta_atual' not in st.session_state:
    st.session_state.resposta_atual = ""
if 'profundidade_atual' not in st.session_state:
    st.session_state.profundidade_atual = 3
if 'topico_atual' not in st.session_state:
    st.session_state.topico_atual = ""
if 'navegacao' not in st.session_state:
    st.session_state.navegacao = []
if 'sugestoes' not in st.session_state:
    st.session_state.sugestoes = []
if 'tema_escuro' not in st.session_state:
    st.session_state.tema_escuro = True
if 'ultimo_topicos' not in st.session_state:
    st.session_state.ultimo_topicos = []

# ==============================================
# SIDEBAR
# ==============================================

with st.sidebar:
    st.header("⚙️ Configuração")
    
    api_key = st.secrets.get("GROQ_API_KEY") or st.text_input("🔑 Chave Groq", type="password")
    
    if api_key:
        client = Groq(api_key=api_key)
        st.success("✅ Conectado à Groq")
        
        profundidade = st.select_slider(
            "📊 Nível de profundidade",
            options=[1, 2, 3, 4, 5],
            value=st.session_state.profundidade_atual,
            help="1 = Resumo | 5 = Tratado acadêmico"
        )
        st.session_state.profundidade_atual = profundidade
        
        temperatura = st.slider("🌡️ Criatividade", 0.1, 1.5, 0.7, 0.1)
        max_tokens = st.selectbox("📏 Tokens", [2048, 4096, 8192], index=2)
        
        tema = st.toggle("🌙 Tema escuro", value=st.session_state.tema_escuro)
        st.session_state.tema_escuro = tema
        
        mostrar_payload = st.checkbox("📋 Mostrar prompt", value=False)
        
        st.divider()
        st.header("🧭 Navegação")
        
        if st.session_state.navegacao:
            for i, item in enumerate(st.session_state.navegacao[-5:]):
                if st.button(f"📂 {item[:35]}...", key=f"nav_{i}"):
                    st.session_state.topico_atual = item
                    st.rerun()
        
        if st.button("🗑️ Limpar tudo"):
            st.session_state.historico = []
            st.session_state.navegacao = []
            st.session_state.sugestoes = []
            st.session_state.ultimo_topicos = []
            st.rerun()
        
        st.divider()
        st.caption("🐱 v6.0 — Modo Explorador Total")
    
    else:
        st.warning("🔑 Configure sua chave")
        st.info("Pegue em [console.groq.com/keys](https://console.groq.com/keys)")

# ==============================================
# FUNÇÃO PARA GERAR PDF
# ==============================================

def criar_pdf_html(texto, titulo):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{titulo}</title>
        <style>
            body {{ font-family: 'Courier New', monospace; padding: 40px; max-width: 900px; margin: auto; }}
            h1 {{ color: #4ecdc4; border-bottom: 2px solid #4ecdc4; }}
            pre {{ white-space: pre-wrap; font-size: 14px; line-height: 1.6; }}
            .footer {{ margin-top: 40px; color: #888; font-size: 12px; text-align: center; }}
        </style>
    </head>
    <body>
        <h1>🐱 CAT Deep Dive — {titulo}</h1>
        <p><strong>Data:</strong> {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
        <p><strong>Nível:</strong> {st.session_state.profundidade_atual}</p>
        <hr>
        <pre>{texto}</pre>
        <hr>
        <div class="footer">Gerado pelo CAT Deep Dive Engine v6.0</div>
    </body>
    </html>
    """
    return html

# ==============================================
# ÁREA PRINCIPAL
# ==============================================

if api_key:
    
    # Mostra o nível atual
    cores_depth = {1: "depth-1", 2: "depth-2", 3: "depth-3", 4: "depth-4", 5: "depth-5"}
    st.markdown(f'<span class="depth-box {cores_depth[profundidade]}">📊 Nível {profundidade}</span>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        pergunta = st.text_area(
            "💬 Digite sua pergunta ou clique em uma sugestão:",
            value=st.session_state.topico_atual,
            height=80,
            placeholder="Ex: Como funciona um buffer overflow? (ou clique nas sugestões abaixo)"
        )
    
    with col2:
        st.metric("Profundidade", f"Nível {profundidade}")
        if st.session_state.historico:
            ultimo = len(st.session_state.historico[-1].split())
            st.metric("Última resposta", f"{ultimo} palavras")
    
    # ==============================================
    # SUGESTÕES (acima do botão)
    # ==============================================
    
    if st.session_state.sugestoes:
        st.markdown("### 💡 Perguntas sugeridas")
        cols = st.columns(min(4, len(st.session_state.sugestoes)))
        for i, sug in enumerate(st.session_state.sugestoes[:4]):
            with cols[i % 4]:
                if st.button(f"💡 {sug[:30]}...", key=f"sug_{i}"):
                    st.session_state.topico_atual = sug
                    st.rerun()
    
    # ==============================================
    # BOTÃO DE ATAQUE
    # ==============================================
    
    if st.button("🚀 MERGULHAR", type="primary", use_container_width=True) and pergunta:
        
        # CONSTRUÇÃO DO PROMPT POR NÍVEL
        niveis = {
            1: f"Resuma de forma clara e concisa: {pergunta}\nUse linguagem acessível. Máximo 200 palavras.\nAo final, liste 5 perguntas relacionadas para explorar depois.",
            
            2: f"Explique {pergunta} com profundidade intermediária.\nInclua: definição, exemplo prático, aplicações reais.\nAo final, sugira 5 perguntas para aprofundar.",
            
            3: f"""AULA COMPLETA sobre: {pergunta}
            Estrutura obrigatória:
            1. FUNDAMENTOS (contexto histórico, definições)
            2. MECANISMO (como funciona, passo a passo)
            3. EXEMPLO PRÁTICO (com código/diagrama)
            4. VARIAÇÕES E EDGE CASES
            5. IMPACTOS E APLICAÇÕES
            6. 5 PERGUNTAS PARA APROFUNDAR (com respostas curtas indicando o caminho)
            """,
            
            4: f"""TRATADO AVANÇADO sobre: {pergunta}
            Nível de pós-graduação.
            Inclua: revisão da literatura, análise crítica, estudos de caso, implementação completa.
            Ao final, liste 7 perguntas de pesquisa abertas para exploração futura.
            """,
            
            5: f"""ENCICLOPÉDIA VIVA — {pergunta}
            Máximo de profundidade.
            Estrutura: origem, fundamentos teóricos, estado da arte, implementação completa, análise de segurança, variantes, casos reais, tendências, bibliografia.
            Ao final, apresente 10 perguntas de nível de doutorado para explorar.
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
                
                # Extrai sugestões (tudo que parecer pergunta)
                sugestoes_raw = re.findall(r'[?？]\s*([^\n.?!]+[?？])', texto)
                sugestoes_raw += re.findall(r'^\d+\.\s*([^?\n]+[?？])', texto, re.MULTILINE)
                sugestoes_raw += re.findall(r'(Como|O que|Por que|Qual|Quais|Quando|Onde|De que forma)[^?\n]*[?？]', texto)
                
                # Limpa e pega as primeiras 8
                sugestoes = [s.strip() for s in sugestoes_raw if len(s) > 10 and len(s) < 150]
                sugestoes = list(dict.fromkeys(sugestoes))[:8]
                
                if not sugestoes:
                    sugestoes = [
                        f"Como aprofundar em {pergunta.split()[0]}?",
                        f"Quais são as principais variações de {pergunta.split()[0]}?",
                        "Como implementar isso na prática?",
                        "Quais são as ferramentas mais usadas?",
                        "Como mitigar os riscos associados?"
                    ]
                
                st.session_state.sugestoes = sugestoes
                st.session_state.historico.append(texto)
                st.session_state.resposta_atual = texto
                if pergunta not in st.session_state.navegacao:
                    st.session_state.navegacao.append(pergunta)
                
                palavras = len(texto.split())
                caracteres = len(texto)
                
                st.success(f"✅ Resposta Nível {profundidade} — {palavras} palavras | {caracteres} caracteres")
                
                # ==============================================
                # EXIBIÇÃO
                # ==============================================
                
                col_resp, col_topicos = st.columns([3, 1])
                
                with col_resp:
                    classe_tema = "" if st.session_state.tema_escuro else "response-box-light"
                    st.markdown(f"""
                    <div class="response-box {classe_tema}">
                    {texto}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Botões de ação
                    col_b1, col_b2, col_b3 = st.columns(3)
                    
                    with col_b1:
                        if st.button("📋 Copiar"):
                            st.success("✅ Copiado!")
                    
                    with col_b2:
                        # Exportar PDF
                        html_pdf = criar_pdf_html(texto, pergunta[:50])
                        b64 = base64.b64encode(html_pdf.encode()).decode()
                        href = f'<a href="data:text/html;base64,{b64}" download="CAT_DeepDive_{datetime.now().strftime("%Y%m%d_%H%M")}.html" style="text-decoration:none;background:#4ecdc4;color:#1e1e1e;padding:8px 16px;border-radius:25px;font-weight:600;">📄 Baixar PDF (HTML)</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    
                    with col_b3:
                        if st.button("🔄 Refazer com mais profundidade"):
                            if profundidade < 5:
                                st.session_state.profundidade_atual = profundidade + 1
                                st.rerun()
                            else:
                                st.info("Já está no nível máximo!")
                
                with col_topicos:
                    st.subheader("💡 Aprofundar em...")
                    for topico in sugestoes[:6]:
                        if st.button(f"🔍 {topico[:45]}...", key=f"topic_{hash(topico)}"):
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
st.caption("🐱 CAT Deep Dive Engine v6.0 — Modo Explorador Total. Use com responsabilidade.")
