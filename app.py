# ==============================================
# CAT DEEP DIVE ENGINE — v7.1 (SELETOR DE MODELOS)
# ==============================================

import streamlit as st
import random
import re
import base64
import json
import os
from groq import Groq
from datetime import datetime
import requests

st.set_page_config(page_title="🐱 CAT Deep Dive", page_icon="🐱", layout="wide")

# ==============================================
# CSS (mesmo da v7.0)
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
    .stButton button {
        border-radius: 25px !important;
        font-weight: 600 !important;
    }
    .drive-status {
        padding: 10px;
        border-radius: 8px;
        background: #e8f5e9;
        color: #1b5e20;
        text-align: center;
    }
    .model-badge {
        background: #4ecdc4;
        color: #1e1e1e;
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        margin: 2px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🐱 CAT DEEP DIVE ENGINE</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">〰️ Seletor de modelos — escolha o LLM que preferir 〰️</p>', unsafe_allow_html=True)

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
if 'drive_autenticado' not in st.session_state:
    st.session_state.drive_autenticado = False
if 'ultimo_audio' not in st.session_state:
    st.session_state.ultimo_audio = None
if 'modelo_atual' not in st.session_state:
    st.session_state.modelo_atual = "llama-3.3-70b-versatile"

# ==============================================
# MODELOS DISPONÍVEIS
# ==============================================

MODELOS_GROQ = {
    "llama-3.3-70b-versatile": {"nome": "🦙 LLaMA 3.3 70B", "tamanho": "70B", "velocidade": "Alta", "desc": "Melhor para respostas detalhadas"},
    "llama-3.1-8b-instant": {"nome": "⚡ LLaMA 3.1 8B", "tamanho": "8B", "velocidade": "Muito alta", "desc": "Respostas rápidas"},
    "gemma2-9b-it": {"nome": "🧠 Gemma 2 9B", "tamanho": "9B", "velocidade": "Alta", "desc": "Bom equilíbrio"},
    "qwen-2.5-32b": {"nome": "🐉 Qwen 2.5 32B", "tamanho": "32B", "velocidade": "Média", "desc": "Raciocínio complexo"},
    "qwen-2.5-72b": {"nome": "🐉 Qwen 2.5 72B", "tamanho": "72B", "velocidade": "Média", "desc": "Máxima qualidade (mais lento)"},
    "llama-3.2-3b-preview": {"nome": "🦙 LLaMA 3.2 3B", "tamanho": "3B", "velocidade": "Extrema", "desc": "Testes rápidos"}
}

# ==============================================
# FUNÇÕES — TTS E DRIVE (mesmas da v7.0)
# ==============================================

def gerar_audio(texto, idioma="pt"):
    try:
        texto_limpo = texto[:2000]
        url = "https://translate.google.com/translate_tts"
        params = {"ie": "UTF-8", "q": texto_limpo, "tl": idioma, "client": "tw-ob"}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.content
        return None
    except:
        return None

def autenticar_drive(credenciais_json):
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        creds = service_account.Credentials.from_service_account_info(
            credenciais_json,
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        return build('drive', 'v3', credentials=creds)
    except:
        return None

def salvar_no_drive(service, conteudo, nome_arquivo):
    try:
        from googleapiclient.http import MediaFileUpload
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(conteudo)
            temp_path = f.name
        file_metadata = {'name': nome_arquivo, 'mimeType': 'text/plain'}
        media = MediaFileUpload(temp_path, mimetype='text/plain')
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        os.unlink(temp_path)
        return file.get('id'), None
    except:
        return None, None

# ==============================================
# SIDEBAR
# ==============================================

with st.sidebar:
    st.header("⚙️ Configuração")
    
    api_key = st.secrets.get("GROQ_API_KEY") or st.text_input("🔑 Chave Groq", type="password")
    
    if api_key:
        client = Groq(api_key=api_key)
        st.success("✅ Conectado à Groq")
        
        # ==============================================
        # SELETOR DE MODELOS (NOVO)
        # ==============================================
        
        st.subheader("🧠 Modelo LLM")
        
        modelo_selecionado = st.selectbox(
            "Escolha o modelo:",
            options=list(MODELOS_GROQ.keys()),
            format_func=lambda x: f"{MODELOS_GROQ[x]['nome']} - {MODELOS_GROQ[x]['tamanho']} ({MODELOS_GROQ[x]['velocidade']})",
            index=list(MODELOS_GROQ.keys()).index(st.session_state.modelo_atual)
        )
        st.session_state.modelo_atual = modelo_selecionado
        
        # Mostra info do modelo
        info = MODELOS_GROQ[modelo_selecionado]
        st.caption(f"📝 {info['desc']}")
        st.caption(f"⚡ Velocidade: {info['velocidade']} | 📦 {info['tamanho']}")
        
        st.divider()
        
        # ==============================================
        # DEMAIS CONFIGURAÇÕES
        # ==============================================
        
        profundidade = st.select_slider(
            "📊 Nível de profundidade",
            options=[1, 2, 3, 4, 5],
            value=st.session_state.profundidade_atual
        )
        st.session_state.profundidade_atual = profundidade
        
        temperatura = st.slider("🌡️ Criatividade", 0.1, 1.5, 0.7, 0.1)
        max_tokens = st.selectbox("📏 Tokens", [2048, 4096, 8192], index=2)
        
        tema = st.toggle("🌙 Tema escuro", value=st.session_state.tema_escuro)
        st.session_state.tema_escuro = tema
        
        # ==============================================
        # DRIVE
        # ==============================================
        
        st.divider()
        st.header("☁️ Google Drive")
        
        drive_json = st.text_area(
            "Cole o credentials.json:",
            placeholder='{"type": "service_account", ...}',
            height=80
        )
        
        if drive_json and not st.session_state.drive_autenticado:
            try:
                creds = json.loads(drive_json)
                if 'private_key' in creds and 'client_email' in creds:
                    st.session_state.drive_creds = creds
                    st.session_state.drive_autenticado = True
                    st.success("✅ Drive autenticado!")
            except:
                st.error("❌ JSON inválido")
        
        if st.session_state.drive_autenticado:
            st.markdown('<div class="drive-status">✅ Drive pronto</div>', unsafe_allow_html=True)
            if st.button("🔓 Desconectar"):
                st.session_state.drive_autenticado = False
                st.rerun()
        
        # ==============================================
        # NAVEGAÇÃO
        # ==============================================
        
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
            st.rerun()
        
        st.caption(f"🐱 v7.1 — Modelo: {modelo_selecionado[:20]}")
    
    else:
        st.warning("🔑 Configure sua chave")
        st.info("Pegue em [console.groq.com/keys](https://console.groq.com/keys)")

# ==============================================
# ÁREA PRINCIPAL
# ==============================================

if api_key:
    
    cores_depth = {1: "depth-1", 2: "depth-2", 3: "depth-3", 4: "depth-4", 5: "depth-5"}
    
    # Mostra modelo atual no topo
    info_modelo = MODELOS_GROQ[st.session_state.modelo_atual]
    st.markdown(f"""
    <div style="display:flex; gap:10px; align-items:center; margin-bottom:15px;">
        <span class="depth-box {cores_depth[profundidade]}">📊 Nível {profundidade}</span>
        <span class="model-badge">🧠 {info_modelo['nome']}</span>
        <span class="model-badge" style="background:#666;color:white;">⚡ {info_modelo['velocidade']}</span>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        pergunta = st.text_area(
            "💬 Digite sua pergunta ou clique em uma sugestão:",
            value=st.session_state.topico_atual,
            height=80,
            placeholder="Ex: Como funciona um buffer overflow?"
        )
    
    with col2:
        st.metric("Profundidade", f"Nível {profundidade}")
        if st.session_state.historico:
            ultimo = len(st.session_state.historico[-1].split())
            st.metric("Última resposta", f"{ultimo} palavras")
    
    # Sugestões
    if st.session_state.sugestoes:
        st.markdown("### 💡 Perguntas sugeridas")
        cols = st.columns(min(4, len(st.session_state.sugestoes)))
        for i, sug in enumerate(st.session_state.sugestoes[:4]):
            with cols[i % 4]:
                if st.button(f"💡 {sug[:30]}...", key=f"sug_{i}"):
                    st.session_state.topico_atual = sug
                    st.rerun()
    
    # ==============================================
    # BOTÃO PRINCIPAL
    # ==============================================
    
    if st.button("🚀 MERGULHAR", type="primary", use_container_width=True) and pergunta:
        
        niveis = {
            1: f"Resuma de forma clara e concisa: {pergunta}\nMáximo 200 palavras.\nAo final, liste 5 perguntas relacionadas.",
            2: f"Explique {pergunta} com profundidade intermediária.\nInclua: definição, exemplo, aplicações.\nSugira 5 perguntas para aprofundar.",
            3: f"""AULA COMPLETA sobre: {pergunta}
            Estrutura: Fundamentos, Mecanismo, Exemplo prático, Variações, Impactos.
            Ao final, liste 5 perguntas para aprofundar.""",
            
            4: f"""TRATADO AVANÇADO sobre: {pergunta}
            Inclua: revisão da literatura, análise crítica, estudos de caso, implementação completa.
            Ao final, liste 7 perguntas de pesquisa.""",
            
            5: f"""ENCICLOPÉDIA VIVA — {pergunta}
            Máximo de profundidade: origem, fundamentos, estado da arte, implementação, segurança, variantes, casos reais, tendências.
            Ao final, liste 10 perguntas de nível doutorado."""
        }
        
        payload = niveis.get(profundidade, niveis[3])
        modelo_uso = st.session_state.modelo_atual
        
        with st.spinner(f"⏳ Processando no {MODELOS_GROQ[modelo_uso]['nome']}..."):
            try:
                resposta = client.chat.completions.create(
                    model=modelo_uso,
                    messages=[{"role": "user", "content": payload}],
                    temperature=temperatura,
                    max_tokens=max_tokens
                )
                texto = resposta.choices[0].message.content
                
                # Extrai sugestões
                sugestoes_raw = re.findall(r'[?？]\s*([^\n.?!]+[?？])', texto)
                sugestoes_raw += re.findall(r'^\d+\.\s*([^?\n]+[?？])', texto, re.MULTILINE)
                sugestoes = [s.strip() for s in sugestoes_raw if len(s) > 10 and len(s) < 150]
                sugestoes = list(dict.fromkeys(sugestoes))[:8]
                
                if not sugestoes:
                    sugestoes = [f"Como aprofundar em {pergunta[:30]}?", "Quais são as principais variações?", 
                                "Como implementar na prática?", "Quais ferramentas usar?", "Como mitigar riscos?"]
                
                st.session_state.sugestoes = sugestoes
                st.session_state.historico.append(texto)
                st.session_state.resposta_atual = texto
                if pergunta not in st.session_state.navegacao:
                    st.session_state.navegacao.append(pergunta)
                
                palavras = len(texto.split())
                
                st.success(f"✅ Resposta Nível {profundidade} — {palavras} palavras | Modelo: {MODELOS_GROQ[modelo_uso]['nome']}")
                
                # ==============================================
                # EXIBE RESPOSTA
                # ==============================================
                
                col_resp, col_sidebar = st.columns([3, 1])
                
                with col_resp:
                    classe_tema = "" if st.session_state.tema_escuro else "response-box-light"
                    st.markdown(f"""
                    <div class="response-box {classe_tema}">
                    {texto}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Botões de ação
                    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
                    
                    with col_b1:
                        if st.button("📋 Copiar"):
                            st.success("✅ Copiado!")
                    
                    with col_b2:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                        html_pdf = f"""
                        <!DOCTYPE html>
                        <html><head><meta charset="UTF-8">
                        <title>CAT_DeepDive_{timestamp}</title>
                        <style>body{{font-family:Courier;padding:40px;max-width:900px;margin:auto;}}
                        h1{{color:#4ecdc4;}}pre{{white-space:pre-wrap;font-size:14px;}}</style>
                        </head><body>
                        <h1>🐱 CAT Deep Dive — {pergunta[:50]}</h1>
                        <p><strong>Nível:</strong> {profundidade} | <strong>Modelo:</strong> {MODELOS_GROQ[modelo_uso]['nome']}</p>
                        <hr><pre>{texto}</pre><hr>
                        <div class="footer">Gerado pelo CAT Engine v7.1 — {modelo_uso}</div>
                        </body></html>
                        """
                        b64 = base64.b64encode(html_pdf.encode()).decode()
                        href = f'<a href="data:text/html;base64,{b64}" download="CAT_DeepDive_{timestamp}.html" style="text-decoration:none;background:#4ecdc4;color:#1e1e1e;padding:8px 16px;border-radius:25px;font-weight:600;">📄 PDF</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    
                    with col_b3:
                        if st.button("🔊 Ouvir"):
                            with st.spinner("Gerando áudio..."):
                                audio_data = gerar_audio(texto, "pt")
                                if audio_data:
                                    st.session_state.ultimo_audio = audio_data
                                    st.audio(audio_data, format="audio/mp3")
                                    st.success("✅ Áudio gerado!")
                                else:
                                    st.error("❌ Erro no TTS")
                    
                    with col_b4:
                        if st.session_state.drive_autenticado and st.button("☁️ Drive"):
                            try:
                                service = autenticar_drive(st.session_state.drive_creds)
                                if service:
                                    nome = f"CAT_DeepDive_{pergunta[:30]}_{timestamp}.txt"
                                    file_id, _ = salvar_no_drive(service, texto, nome)
                                    if file_id:
                                        st.success(f"✅ Salvo! ID: {file_id[:8]}...")
                                        st.markdown(f"[🔗 Abrir](https://drive.google.com/file/d/{file_id}/view)")
                                    else:
                                        st.error("❌ Erro ao salvar")
                            except Exception as e:
                                st.error(f"❌ Erro: {str(e)[:60]}")
                    
                    if st.session_state.ultimo_audio:
                        st.audio(st.session_state.ultimo_audio, format="audio/mp3")
                
                # ==============================================
                # SIDEBAR DE APROFUNDAMENTO
                # ==============================================
                
                with col_sidebar:
                    st.subheader("💡 Aprofundar")
                    for topico in sugestoes[:6]:
                        if st.button(f"🔍 {topico[:40]}...", key=f"topic_{hash(topico)}"):
                            st.session_state.topico_atual = topico
                            st.rerun()
                    
                    st.divider()
                    st.caption(f"🧠 {MODELOS_GROQ[modelo_uso]['nome']}")
                    st.caption(f"🌡️ {temperatura} | 📏 {max_tokens}")
                    
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
    
    # Histórico
    if st.session_state.historico:
        with st.expander("📜 Histórico"):
            for i, resp in enumerate(st.session_state.historico[-5:]):
                st.text(f"{i+1}: {resp[:200]}...")
                st.divider()

else:
    st.info("🔑 Configure sua chave Groq na barra lateral")

st.divider()
st.caption("🐱 CAT Deep Dive v7.1 — Seletor de modelos. Use com responsabilidade.")
