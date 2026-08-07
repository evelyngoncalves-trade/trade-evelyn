import streamlit as st
from google import genai
from google.genai import types
import base64
import io
from PIL import Image

# Configuração da página
st.set_page_config(page_title="Trade IA - Evelyn", layout="wide")

st.title("📈 Co-Piloto de Trade IA")

# Sidebar - Configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    api_key = st.text_input("Cole sua Gemini API Key (AIza...):", type="password")
    st.caption("Pegue grátis em: https://aistudio.google.com/apikey")

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
        st.rerun()

# Inicialização do Session State
if "wins" not in st.session_state:
    st.session_state.wins = 0
if "losses" not in st.session_state:
    st.session_state.losses = 0
if "analise_resultado" not in st.session_state:
    st.session_state.analise_resultado = None

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

    uploaded_file = st.file_uploader(
        "📸 Envie o print ou arquivo do gráfico (M1/M5):",
        type=["png", "jpg", "jpeg"],
        key="grafico_uploader"
    )

    if uploaded_file:
        st.image(uploaded_file, caption="Gráfico Carregado", use_container_width=True)

    if st.button("🔍 Analisar Entrada com IA"):
        if not api_key:
            st.warning("⚠️ Insira sua Gemini API Key na barra lateral para habilitar a análise!")
        elif not uploaded_file:
            st.warning("⚠️ Envie uma imagem do gráfico antes de analisar!")
        else:
            with st.spinner("Analisando gráfico com IA..."):
                try:
                    # Redimensiona a imagem para acelerar o upload/análise
                    img = Image.open(uploaded_file)
                    img.thumbnail((1024, 1024))
                    buf = io.BytesIO()
                    img.convert("RGB").save(buf, format="JPEG", quality=85)
                    image_bytes = buf.getvalue()

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
                        model="gemini-3.5-flash-lite",
                        contents=[
                            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                            prompt,
                        ],
                    )

                    st.session_state.analise_resultado = response.text

                except Exception as e:
                    erro_txt = str(e).lower()
                    if "resource_exhausted" in erro_txt or "429" in erro_txt or "quota" in erro_txt:
                        st.error(
                            "🚦 Limite gratuito atingido! O plano grátis do Gemini permite poucas "
                            "análises por minuto e um número máximo por dia. Espere alguns instantes "
                            "e tente novamente, ou volte amanhã quando a cota reiniciar."
                        )
                    else:
                        st.error(f"Erro na análise da IA: {e}")

    # Exibe o resultado da análise
    if st.session_state.analise_resultado:
        st.markdown("---")
        st.markdown("### 📊 Análise da IA")
        st.write(st.session_state.analise_resultado)
        st.caption(
            "⚠️ Isto é uma leitura automática de padrões gráficos, não é garantia de resultado. "
            "Opções binárias envolvem alto risco — use apenas o valor definido na sua gestão de banca."
        )
