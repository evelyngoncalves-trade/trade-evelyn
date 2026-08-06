import streamlit as st
from google import genai
import pandas as pd
from PIL import Image

# Tenta importar o componente de colar imagem da área de transferência
try:
    from st_paste_button import paste_icon_button
    HAS_PASTE = True
except ImportError:
    HAS_PASTE = False

# Configuração da página
st.set_page_config(page_title="Trade IA - Evelyn", layout="wide")

st.title("📈 Co-Piloto de Trade IA")

# Sidebar - Configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    api_key = st.text_input("Cole sua Google Gemini API Key aqui:", type="password")
    
    st.header("💰 Parâmetros da Banca")
    banca_inicial = st.number_input("Banca Atual (R$)", value=50.0, step=5.0)
    valor_entrada = st.number_input("Valor por Entrada (R$)", value=5.0, step=1.0)
    payout = st.slider("Payout Corretora (%)", min_value=50, max_value=100, value=80)
    
    st.header("🛑 Trava Anti-emoção")
    stop_win = st.number_input("Stop Win (Nº de Wins)", value=3, step=1)
    stop_loss = st.number_input("Stop Loss (Nº de Losses)", value=2, step=1)
    
    if st.button("🔄 Resetar Dia"):
        st.session_state.wins = 0
        st.session_state.losses = 0
        st.session_state.analise_resultado = None
        st.session_state.imagem_pasted = None
        st.rerun()

# Inicialização do Session State
if "wins" not in st.session_state:
    st.session_state.wins = 0
if "losses" not in st.session_state:
    st.session_state.losses = 0
if "analise_resultado" not in st.session_state:
    st.session_state.analise_resultado = None
if "imagem_pasted" not in st.session_state:
    st.session_state.imagem_pasted = None

# Layout Principal (2 Colunas)
col_gestao, col_ia = st.columns(2)

with col_gestao:
    st.subheader("📝 Registrar Operação")
    
    lucro_win = valor_entrada * (payout / 100)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button(f"✅ REGISTRAR WIN (+R$ {lucro_win:.2f})"):
            st.session_state.wins += 1
    with col_btn2:
        if st.button(f"❌ REGISTRAR LOSS (-R$ {valor_entrada:.2f})"):
            st.session_state.losses += 1
            
    # Alertas de Stop
    if st.session_state.wins >= stop_win:
        st.balloons()
        st.success("🎉 META ATINGIDA! Hora de fechar o gráfico e curtir o dia!")
    elif st.session_state.losses >= stop_loss:
        st.error("🚨 STOP LOSS ATINGIDO! Respeite seu gerenciamento e volte amanhã!")

with col_ia:
    st.subheader("🤖 IA Co-Piloto de Análise")

    # Opção de Colar Print via CTRL+V
    if HAS_PASTE:
        st.write("📋 **Cole o print direto da área de transferência:**")
        paste_result = paste_icon_button(
            change_color=True,
            label="📋 Clique aqui e cole com CTRL+V",
            background_color="#262730",
            hover_background_color="#1E1E1E",
        )
        if paste_result.image_data is not None:
            st.session_state.imagem_pasted = paste_result.image_data

    # File Uploader Tradicional
    uploaded_file = st.file_uploader(
        "Ou envie a imagem do gráfico (M1/M5):", 
        type=["png", "jpg", "jpeg"], 
        key="grafico_uploader"
    )

    img_to_analyze = None

    if st.session_state.imagem_pasted is not None:
        img_to_analyze = st.session_state.imagem_pasted
        st.image(img_to_analyze, caption="Gráfico Capturado", use_container_width=True)
    elif uploaded_file is not None:
        img_to_analyze = Image.open(uploaded_file)
        st.image(img_to_analyze, caption="Gráfico Carregado", use_container_width=True)

    if st.button("🔍 Analisar Entrada com IA"):
        if not api_key:
            st.warning("⚠️ Insira sua Gemini API Key na barra lateral para habilitar a análise!")
        elif img_to_analyze is None:
            st.warning("⚠️ Envie ou cole uma imagem do gráfico antes de analisar!")
        else:
            with st.spinner("Analisando suporte, resistência e tendência..."):
                try:
                    client = genai.Client(api_key=api_key)

                    prompt = (
                        "Você é um especialista em Price Action para Opções Binárias (Blitz/M1/M5). "
                        "Analise a imagem deste gráfico e responda de forma objetiva:\n"
                        "1. Tendência Principal (Alta, Baixa ou Lateral)\n"
                        "2. Padrão das últimas velas e pavios\n"
                        "3. Níveis de Suporte ou Resistência mais próximos\n"
                        "4. Recomendação final: [COMPRA / VENDA / AGUARDAR] com breve justificativa."
                    )

                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=[prompt, img_to_analyze]
                    )

                    st.session_state.analise_resultado = response.text

                except Exception as e:
                    st.error(f"Erro ao processar análise da IA: {e}")

    # Exibe a análise salva
    if st.session_state.analise_resultado:
        st.markdown("---")
        st.markdown("### 📊 Análise da IA (Gemini)")
        st.write(st.session_state.analise_resultado)
