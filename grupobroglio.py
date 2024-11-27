import streamlit as st
import pandas as pd
import plotly.express as px
import firebase_admin
from firebase_admin import credentials, db
import io

# Configuração inicial da página do Streamlit
st.set_page_config(page_title="Dashboard Financeiro Neon", layout="wide")

# Inicializar o Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(st.secrets["firebase"])
    firebase_admin.initialize_app(cred, {
        'databaseURL': st.secrets["firebase"]["database_url"]
    })

# Referência ao nó principal do Realtime Database
db_ref = db.reference("/")

# Funções para salvar e carregar dados no Firebase
def save_to_firebase(file_content):
    try:
        file_bytes = io.BytesIO(file_content)
        df = pd.read_excel(file_bytes)
        data = df.to_dict(orient="records")  # Converter DataFrame para JSON
        db_ref.set(data)  # Salvar no Firebase
        return df
    except Exception as e:
        st.error(f"Erro ao salvar no Firebase: {e}")
        return None

def load_from_firebase():
    try:
        data = db_ref.get()
        if data:
            df = pd.DataFrame(data)
            return df
        return None
    except Exception as e:
        st.error(f"Erro ao carregar dados do Firebase: {e}")
        return None

# Função para converter DataFrame para CSV
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# --- Estilos CSS Personalizados ---
st.markdown("""
    <style>
    /* Estilo dos títulos */
    h1, h2, h3, h4, h5, h6 {
        color: #39ff14;
    }
    /* Estilo dos textos */
    .st-text, .st-dataframe {
        color: #ffffff;
    }
    /* Estilo dos botões */
    .stButton>button {
        background-color: #39ff14;
        color: #000000;
    }
    </style>
""", unsafe_allow_html=True)

# --- Barra Lateral ---
st.sidebar.title("⚙️ Configurações")

# Upload do arquivo Excel
uploaded_file = st.sidebar.file_uploader("📥 Importar arquivo Excel", type=["xlsx"])

if uploaded_file:
    df = save_to_firebase(uploaded_file.getvalue())
    if df is not None:
        st.sidebar.success("Arquivo carregado e salvo no Firebase.")
        st.session_state['df'] = df
elif 'df' in st.session_state:
    df = st.session_state['df']
else:
    df = load_from_firebase()
    if df is not None:
        st.sidebar.info("Dados carregados do Firebase.")
        st.session_state['df'] = df
    else:
        st.sidebar.warning("Nenhum dado encontrado. Faça o upload de um arquivo.")

if df is not None:
    # Tratamento de dados (formatação de datas)
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')

    # Filtro por loja
    lojas = df['Loja'].unique() if 'Loja' in df.columns else []
    loja_selecionada = st.sidebar.selectbox("🏬 Filtrar por Loja:", ["Todas as Lojas"] + list(lojas))

    # Aplicar filtro por loja
    if loja_selecionada != "Todas as Lojas":
        df_filtrado = df[df['Loja'] == loja_selecionada]
    else:
        df_filtrado = df

    # Filtro por plano de contas
    filtro_plano_contas = st.sidebar.text_input("🔍 Filtrar Plano de Contas:")
    if filtro_plano_contas:
        df_filtrado = df_filtrado[df_filtrado['Plano de contas'].str.contains(filtro_plano_contas, case=False, na=False)]

    # --- Cabeçalho ---
    st.title("💹 Dashboard Financeiro Neon")
    st.markdown("Visualize e analise os dados de vendas e despesas com um visual moderno.")

    # --- Criação das Abas ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Resumo", "📄 Dados", "📈 Gráficos", "💾 Exportação"])

    # --- Aba Resumo ---
    with tab1:
        st.subheader("Resumo de Vendas")
        if 'Plano de contas' in df_filtrado.columns and 'Valor' in df_filtrado.columns:
            total_vendas = df_filtrado[df_filtrado['Plano de contas'].str.contains(r'(?i)^vendas$', na=False)]['Valor'].sum()
            total_vendas_balcao = df_filtrado[df_filtrado['Plano de contas'].str.contains(r'(?i)vendas no balcão', na=False)]['Valor'].sum()

            col1, col2 = st.columns(2)
            col1.metric("Total Vendas 🛒", f"R$ {total_vendas:,.2f}")
            col2.metric("Total Vendas Balcão 🏬", f"R$ {total_vendas_balcao:,.2f}")

            # Resumo por plano de contas
            if 'Data' in df_filtrado.columns:
                df_filtrado['Mês/Ano'] = df_filtrado['Data'].dt.to_period('M')
                resumo = df_filtrado.groupby(['Plano de contas', 'Mês/Ano'])['Valor'].sum().reset_index()
                resumo_pivot = resumo.pivot(index='Plano de contas', columns='Mês/Ano', values='Valor').fillna(0)
                resumo_pivot['Total'] = resumo_pivot.sum(axis=1)

                st.subheader("Resumo por Plano de Contas")
                st.dataframe(resumo_pivot)

    # --- Aba Dados ---
    with tab2:
        st.subheader("Dados Importados")
        st.dataframe(df_filtrado)

    # --- Aba Gráficos ---
    with tab3:
        st.subheader("📊 Gráficos")
        if 'Plano de contas' in df_filtrado.columns and 'Valor' in df_filtrado.columns:
            fig = px.bar(df_filtrado.groupby('Plano de contas')['Valor'].sum().reset_index(),
                         x='Plano de contas', y='Valor', title="Valores por Plano de Contas")
            st.plotly_chart(fig)

    # --- Aba Exportação ---
    with tab4:
        st.subheader("Exportar Resumo")
        csv_data = convert_df_to_csv(df_filtrado)
        st.download_button("💾 Exportar para CSV", csv_data, "dados_financeiros.csv", "text/csv")

else:
    st.warning("📥 Por favor, faça o upload de um arquivo Excel para começar.")
