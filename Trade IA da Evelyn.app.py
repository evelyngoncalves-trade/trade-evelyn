import streamlit as st
import pandas as pd
import json
import os
from openai import OpenAI

# ------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Trade Co-Pilot | Evelyn",
    page_icon="📈",
    layout="wide"
)

# Estilo personalizado para ficar limpo e moderno
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .success-text { color: #2ea043; font-weight: bold; }
    .danger-text { color: #da3633; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# INICIALIZAÇÃO DE ESTADO (BANCO DE DADOS LOCAL EM SESSÃO)
# ------------------------------------------------------------------
if 'banca' not in st.session_state:
    st.session_state.banca = 50.0  # Banca Inicial Padrão
if 'historico' not in st.session_state:
    st.session_state.historico = []
if 'wins' not in st.session_state:
    st.session_state.wins = 0
if 'losses' not in st.session_state:
    st.session_state.losses = 0

# ------------------------------------------------------------------
# BARRA LATERAL - CONFIGURAÇÕES & CHAVE DE API
# ------------------------------------------------------------------
st.sidebar.title("⚙️ Configurações")
api_key = st.sidebar.text_input("Cole sua OpenAI API Key aqui:", type="password")
st.sidebar.markdown("---")

st.sidebar.subheader("💰 Parâmetros da Banca")
banca_input = st.sidebar.number_input("Banca Atual (R$)", value=float(st.session_state.banca), step=5.0)
st.session_state.banca = banca_input

mao_entrada = st.sidebar.number_input("Valor por Entrada (R$)", value=5.0, step=1.0)
payout = st.sidebar.slider("Payout Corretora (%)", min_value=70, max_value=95, value=80) / 100

st.sidebar.markdown("---")
st.sidebar.subheader("🛑 Trava Antiemoção")
max_wins = st.sidebar.number_input("Stop Win (Nº de Wins)", value=3)
max_losses = st.sidebar.number_input("Stop Loss (Nº de Losses)", value=2)

if st.sidebar.button("🔄 Resetar Dia"):
    st.session_state.wins = 0
    st.session_state.losses = 0
    st.rerun()

# ------------------------------------------------------------------
# TÍTULO PRINCIPAL
# ------------------------------------------------------------------
st.title("⚡ Painel Trade Co-Pilot")
st.caption("Foco: Renda Extra com Disciplina | Meta Intermediária: R$ 150,00")

# Alertas de Trava Diária
if st.session_state.wins >= max_wins:
    st.balloons()
    st.success("🎉 META BATIDA (STOP WIN ALCANÇADO)! Feche a plataforma por hoje e vá focar nos seus projetos!")
elif st.session_state.losses >= max_losses:
    st.error("🛑 STOP LOSS ATINGIDO! Pare imediatamente. O mercado não está favorável hoje. Volte amanhã com a mente fria.")

# ------------------------------------------------------------------
# ESTRUTURA DE COLUNAS DA PLATAFORMA
# ------------------------------------------------------------------
col_dash, col_ia = st.columns([1, 1.2])

# ==================================================================
# PAINEL ESQUERDO: DASHBOARD DE GERENCIAMENTO
# ==================================================================
with col_dash:
    st.subheader("📊 Gerenciamento Diário")
    
    # Métricas
    m1, m2, m3 = st.columns(3)
    m1.metric("Banca Atual", f"R$ {st.session_state.banca:.2f}")
    m2.metric("Placar do Dia", f"{st.session_state.wins}W - {st.session_state.losses}L")
    lucro_hoje = sum([h['resultado'] for h in st.session_state.historico if h['data'] == 'Hoje'])
    m3.metric("Lucro Sessão", f"R$ {lucro_hoje:.2f}")

    # Progresso rumo aos R$ 150
    progresso = min(st.session_state.banca / 150.0, 1.0)
    st.markdown(f"**Progresso para a Meta de R$ 150,00:** {progresso * 100:.1f}%")
    st.progress(progresso)

    st.markdown("---")
    st.subheader("📝 Registrar Operação")
    
    btn_win, btn_loss = st.columns(2)
    
    if btn_win.button("✅ REGISTRAR WIN (+R$ {:.2f})".format(mao_entrada * payout)):
        if st.session_state.wins < max_wins and st.session_state.losses < max_losses:
            ganho = mao_entrada * payout
            st.session_state.banca += ganho
            st.session_state.wins += 1
            st.session_state.historico.append({'tipo': 'WIN', 'resultado': ganho, 'data': 'Hoje'})
            st.rerun()

    if btn_loss.button("❌ REGISTRAR LOSS (-R$ {:.2f})".format(mao_entrada)):
        if st.session_state.wins < max_wins and st.session_state.losses < max_losses:
            st.session_state.banca -= mao_entrada
            st.session_state.losses += 1
            st.session_state.historico.append({'tipo': 'LOSS', 'resultado': -mao_entrada, 'data': 'Hoje'})
            st.rerun()

    # Tabela de Histórico
    if st.session_state.historico:
        st.markdown("### Histórico da Sessão")
        df_hist = pd.DataFrame(st.session_state.historico)
        st.dataframe(df_hist, use_container_width=True)

# ==================================================================
# PAINEL DIREITO: IA CO-PILOTO (ANÁLISE DE GRÁFICO)
# ==================================================================
with col_ia:
    st.subheader("🤖 IA Co-Piloto de Análise")
    
    uploaded_file = st.file_uploader("Envie o Print do Gráfico da Gomere Broker (M1/M5)", type=["png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Gráfico Carregado", use_column_width=True)
        
        analisar = st.button("🔍 Analisar Entrada com IA")
        
        if analisar:
            if not api_key:
                st.warning("⚠️ Insira sua OpenAI API Key na barra lateral para habilitar a análise da IA!")
            else:
                with st.spinner("Analisando suporte, resistência e tendência..."):
                    try:
                        # Preparando imagem para a API Vision
                        bytes_data = uploaded_file.getvalue()
                        import base64
                        base64_image = base64.b64encode(bytes_data).decode('utf-8')
                        
                        client = OpenAI(api_key=api_key)
                        
                        # Prompt especialista pré-configurado
                        prompt_sistema = """
                        Você é uma IA assistente de Day Trade em M1/Blitz para a Evelyn. 
                        Regras fixas da Evelyn:
                        - Mão fixa de R$ 5,00.
                        - Foco em altíssima assertividade (Suporte/Resistência a favor da tendência).
                        - Não arriscar. Se o gráfico estiver confuso ou sem direção, recomende NÃO entrar.

                        Analise a imagem enviada e responda no seguinte formato:
                        1. **Tendência Principal:** [Alta / Baixa / Consolidação]
                        2. **Regiões Chave:** Onde estão o Suporte (Chão) e Resistência (Teto) mais próximos.
                        3. **Veredito:** [ENTRADA FAVORÁVEL DE COMPRA / ENTRADA FAVORÁVEL DE VENDA / AGUARDAR FORA DO MERCADO]
                        4. **Motivo Rápido:** 2 linhas resumindo a decisão.
                        """

                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": prompt_sistema},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/jpeg;base64,{base64_image}"
                                            },
                                        },
                                    ],
                                }
                            ],
                            max_tokens=350,
                        )
                        
                        resultado = response.choices[0].message.content
                        st.markdown("### 📋 Resposta da IA:")
                        st.info(resultado)

                    except Exception as e:
                        st.error(f"Erro ao processar imagem: {e}")