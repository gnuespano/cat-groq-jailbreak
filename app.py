# ==============================================
# CAT DEEP DIVE ENGINE — v7.0 (TTS + GOOGLE DRIVE)
# Funcionalidades: 5 níveis + Sugestões + PDF + Voz + Drive
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
# CSS
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
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🐱 CAT DEEP DIVE ENGINE</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">〰️ Voz + Drive + PDF — exploração total 〰️</p>', unsafe_allow_html=True)

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

# ==============================================
# FUNÇÕES — TTS (Google TTS grátis)
# ==============================================

def gerar_audio(texto, idioma="pt"):
    """Gera áudio usando Google TTS (gratuito, sem API key)"""
    try:
        # Limita o texto para evitar erros
        texto_limpo = texto[:2000]
        
        # Usa a API gratuita do Google TTS
        url = f"https://translate.google.com/translate_tts"
        params = {
            "ie": "UTF-8",
            "q": texto_limpo,
            "tl": idioma,
            "client": "tw-ob"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.content
        else:
            return None
    except Exception as e:
        st.error(f"Erro no TTS: {str(e)[:50]}")
        return None

# ==============================================
# FUNÇÕES — GOOGLE DRIVE (via API)
# ==============================================

def autenticar_drive(credenciais_json):
    """Autentica no Google Drive usando credentials.json"""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        
        creds = service_account.Credentials.from_service_account_info(
            credenciais_json,
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        st.error(f"Erro na autenticação Drive: {str(e)[:50]}")
        return None

def salvar_no_drive(service, conteudo, nome_arquivo):
    """Salva um arquivo de texto no Google Drive"""
    try:
        from googleapiclient.http import MediaFileUpload
        import tempfile
        
        # Cria arquivo temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(conteudo)
            temp_path = f.name
        
        # Metadados
        file_metadata = {
            'name': nome_arquivo,
            'mimeType': 'text/plain'
        }
        
        media = MediaFileUpload(temp_path, mimetype='text/plain')
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        os.unlink(temp_path)  # Remove arquivo temporário
        
        return file.get('id'), file.get('webViewLink')
    except Exception as e:
        st.error(f"Erro ao salvar no Drive: {str(e)[:50]}")
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
        # CONFIGURAÇÃO DRIVE (NA SIDEBAR)
        # ==============================================
        
        st.divider()
        st.header("☁️ Google Drive")
        
        drive_json = st.text_area(
            "Cole o credentials.json do Google Drive:",
            placeholder='{"type": "service_account", ...}',
            height=100,
            help="Obtenha em console.cloud.google.com/apis/credentials"
        )
        
        if drive_json and not st.session_state.drive_autenticado:
            try:
                creds = json.loads(drive_json)
                # Validação básica
                if 'private_key' in creds and 'client_email' in creds:
                    st.session_state.drive_creds = creds
                    st.session_state.drive_autenticado = True
                    st.success("✅ Drive autenticado!")
                else:
                    st.error("❌ JSON inválido")
            except:
                st.error("❌ Erro ao parsear JSON")
        
        if st.session_state.drive_autenticado:
            st.markdown('<div class="drive-status">✅ Drive pronto</div>', unsafe_allow_html=True)
            if st.button("🔓 Desconectar Drive"):
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
        
        st.caption("🐱 v7.0 — TTS + Drive")
    
    else:
        st.warning("🔑 Configure sua chave")
        st.info("Pegue em [console.groq.com/keys](https://console.groq.com/keys)")

# ==============================================
# ÁREA PRINCIPAL
# ==============================================

if api_key:
    
    cores_depth = {1: "depth-1", 2: "depth-2", 3: "depth-3", 4: "depth-4", 5: "depth-5"}
    st.markdown(f'<span class="depth-box {cores_depth[profundidade]}">📊 Nível {profundidade}</span>', unsafe_allow_html=True)
    
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
        
        with st.spinner(f"⏳ Construindo conhecimento — Nível {profundidade}..."):
            try:
                resposta = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
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
                
                st.success(f"✅ Resposta Nível {profundidade} — {palavras} palavras")
                
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
                    
                    # ==============================================
                    # BOTÕES DE AÇÃO
                    # ==============================================
                    
                    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
                    
                    with col_b1:
                        if st.button("📋 Copiar"):
                            st.success("✅ Copiado!")
                    
                    with col_b2:
                        # PDF
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                        html_pdf = f"""
                        <!DOCTYPE html>
                        <html><head><meta charset="UTF-8">
                        <title>CAT_DeepDive_{timestamp}</title>
                        <style>body{{font-family:Courier;padding:40px;max-width:900px;margin:auto;}}
                        h1{{color:#4ecdc4;}}pre{{white-space:pre-wrap;font-size:14px;}}</style>
                        </head><body>
                        <h1>🐱 CAT Deep Dive — {pergunta[:50]}</h1>
                        <p><strong>Nível:</strong> {profundidade}</p>
                        <hr><pre>{texto}</pre><hr>
                        <div class="footer">Gerado pelo CAT Engine v7.0</div>
                        </body></html>
                        """
                        b64 = base64.b64encode(html_pdf.encode()).decode()
                        href = f'<a href="data:text/html;base64,{b64}" download="CAT_DeepDive_{timestamp}.html" style="text-decoration:none;background:#4ecdc4;color:#1e1e1e;padding:8px 16px;border-radius:25px;font-weight:600;">📄 PDF</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    
                    with col_b3:
                        # TTS (Voz)
                        if st.button("🔊 Ouvir"):
                            with st.spinner("Gerando áudio..."):
                                audio_data = gerar_audio(texto, "pt")
                                if audio_data:
                                    st.session_state.ultimo_audio = audio_data
                                    st.audio(audio_data, format="audio/mp3")
                                    st.success("✅ Áudio gerado!")
                                else:
                                    st.error("❌ Erro ao gerar áudio")
                    
                    with col_b4:
                        # Salvar no Drive
                        if st.session_state.drive_autenticado and st.button("☁️ Drive"):
                            try:
                                service = autenticar_drive(st.session_state.drive_creds)
                                if service:
                                    nome = f"CAT_DeepDive_{pergunta[:30]}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                                    file_id, link = salvar_no_drive(service, texto, nome)
                                    if file_id:
                                        st.success(f"✅ Salvo no Drive! ID: {file_id[:8]}...")
                                        st.markdown(f"[🔗 Abrir no Drive](https://drive.google.com/file/d/{file_id}/view)")
                                    else:
                                        st.error("❌ Erro ao salvar")
                            except Exception as e:
                                st.error(f"❌ Erro: {str(e)[:80]}")
                    
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
                    st.caption(f"🧠 Nível {profundidade} | 🌡️ {temperatura}")
                    
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
    
    # ==============================================
    # HISTÓRICO
    # ==============================================
    
    if st.session_state.historico:
        with st.expander("📜 Histórico"):
            for i, resp in enumerate(st.session_state.historico[-5:]):
                st.text(f"{i+1}: {resp[:200]}...")
                st.divider()

else:
    st.info("🔑 Configure sua chave Groq na barra lateral")

st.divider()
st.caption("🐱 CAT Deep Dive v7.0 — Voz + Drive + PDF. Use com responsabilidade.")
