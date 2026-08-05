import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
from PIL import Image

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
        st.rerun()

# Inicialização do Session State
if "wins" not in st.session_state:
    st.session_state.wins = 0
if "losses" not in st.session_state:
    st.session_state.losses = 0

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

    uploaded_file = st.file_uploader("Envie ou arraste o print do gráfico (M1/M5)", type=["png", "jpg", "jpeg"], key="grafico_uploader")

    if uploaded_file:
        st.image(uploaded_file, caption="Gráfico Carregado", use_container_width=True)

    if st.button("🔍 Analisar Entrada com IA"):
        if not api_key:
            st.warning("⚠️ Insira sua Gemini API Key na barra lateral para habilitar a análise da IA!")
        elif not uploaded_file:
            st.warning("⚠️ Envie uma imagem do gráfico antes de analisar!")
        else:
            with st.spinner("Analisando suporte, resistência e tendência..."):
                try:
                    # Carrega a imagem via PIL
                    image = Image.open(uploaded_file)

                    # Inicializa o cliente da API do Gemini
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
                        model='gemini-2.0-flash',
                        contents=[prompt, image]
                    )

                    st.markdown("### 📊 Análise da IA (Gemini)")
                    st.write(response.text)

                except Exception as e:
                    st.error(f"Erro ao processar análise da IA: {e}")

