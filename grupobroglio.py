import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração inicial da página do Streamlit
st.set_page_config(page_title="Dashboard Financeiro Neon", layout="wide")

# Função para converter DataFrame para CSV
def convert_df(df):
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
    /* Estilo das métricas */
    .stMetric-label {
        color: #39ff14;
    }
    .stMetric-value {
        color: #39ff14;
    }
    /* Estilo dos botões */
    .stButton>button {
        background-color: #39ff14;
        color: #000000;
    }
    /* Estilo dos elementos da barra lateral */
    .sidebar .sidebar-content {
        background-color: #1a1a1a;
    }
    </style>
""", unsafe_allow_html=True)

# --- Barra Lateral ---
st.sidebar.title("⚙️ Configurações")

# Upload do arquivo Excel
uploaded_file = st.sidebar.file_uploader("📥 Importar arquivo Excel", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.sidebar.success("Arquivo carregado com sucesso.")
    st.session_state['df'] = df
elif 'df' in st.session_state:
    df = st.session_state['df']
else:
    st.sidebar.warning("Por favor, faça o upload de um arquivo Excel para começar.")
    df = None

if df is not None:
    # Tratamento de dados (formatação de datas)
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    
    # Filtro de Data - selecione o intervalo desejado
    min_date = df['Data'].min()
    max_date = df['Data'].max()
    selected_dates = st.sidebar.date_input("Selecione o intervalo de datas", [min_date, max_date])
    if isinstance(selected_dates, list) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
        df = df[(df['Data'] >= pd.to_datetime(start_date)) & (df['Data'] <= pd.to_datetime(end_date))]
    
    # Filtro por Loja
    lojas = df['Loja'].unique()
    loja_selecionada = st.sidebar.selectbox("🏬 Filtrar por Loja:", ["Todas as Lojas"] + list(lojas))
    if loja_selecionada != "Todas as Lojas":
        df_filtrado = df[df['Loja'] == loja_selecionada]
    else:
        df_filtrado = df
    
    # Filtro por Plano de Contas
    filtro_plano_contas = st.sidebar.text_input("🔍 Filtrar Plano de Contas:")
    if filtro_plano_contas:
        df_filtrado = df_filtrado[df_filtrado['Plano de contas'].str.contains(filtro_plano_contas, case=False, na=False)]
    
    # --- Cabeçalho ---
    st.title("💹 Dashboard Financeiro Neon")
    st.markdown("Bem-vindo ao dashboard financeiro com temática neon. Visualize e analise os dados de vendas e despesas com um visual moderno.")
    
    # Calcular métricas de vendas
    total_vendas = df_filtrado[df_filtrado['Plano de contas'].str.contains(r'(?i)^vendas$', na=False)]['Valor'].sum()
    total_vendas_balcao = df_filtrado[df_filtrado['Plano de contas'].str.contains(r'(?i)vendas no balcão', na=False)]['Valor'].sum()
    total_vendas_total = total_vendas + total_vendas_balcao
    
    # Exibir cards de vendas no cabeçalho
    colA, colB, colC = st.columns(3)
    colA.metric("Total Vendas 🛒", f"R$ {total_vendas:,.2f}")
    colB.metric("Total Vendas Balcão 🏬", f"R$ {total_vendas_balcao:,.2f}")
    colC.metric("Total Vendas Geral", f"R$ {total_vendas_total:,.2f}")
    
    # --- Criação das Abas ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Resumo", "📄 Dados", "📈 Gráficos", "💾 Exportação"])
    
    # --- Aba Resumo ---
    with tab1:
        st.subheader("Resumo de Vendas")
        
        # Agrupar por Plano de Contas e Mês/Ano
        df_filtrado['Mês/Ano'] = df_filtrado['Data'].dt.to_period('M').astype(str)
        summary = df_filtrado.groupby(['Plano de contas', 'Mês/Ano'])['Valor'].sum().reset_index()
        summary_pivot = summary.pivot(index='Plano de contas', columns='Mês/Ano', values='Valor').fillna(0)
        summary_pivot['Total'] = summary_pivot.sum(axis=1)
    
        st.subheader("Total por Plano de Contas (Agrupado por Mês/Ano)")
        st.dataframe(
            summary_pivot.style
            .format({'Total': 'R$ {:,.2f}'})
            .set_properties(**{'background-color': '#1a1a1a', 'color': '#ffffff'})
        )
    
    # --- Aba Dados ---
    with tab2:
        st.subheader("Dados Importados")
        st.dataframe(
            df_filtrado.style
            .format({'Valor': 'R$ {:,.2f}'})
            .set_properties(**{'background-color': '#1a1a1a', 'color': '#ffffff'})
        )
    
    # --- Aba Gráficos ---
    with tab3:
        # Gráfico de Entradas de Disponibilidade (valores positivos)
        st.subheader("Entradas de Disponibilidade (Valores Positivos)")
        df_positivo = df_filtrado[df_filtrado['Valor'] > 0]
        df_positivo_agrupado = df_positivo.groupby('Plano de contas')['Valor'].sum().reset_index()
        if not df_positivo_agrupado.empty:
            fig = px.bar(
                df_positivo_agrupado,
                x='Plano de contas',
                y='Valor',
                color='Plano de contas',
                title='Entradas de Disponibilidade por Plano de Contas',
                labels={'Valor': 'Valor (R$)'},
                template='plotly_dark',
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig.update_layout(
                xaxis_tickangle=-45,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#39ff14')
            )
            fig.update_yaxes(tickprefix="R$ ")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("Não há valores positivos para exibir.")
    
        # Top 5 categorias de despesas
        st.subheader("Top 5 Categorias de Despesas")
        df_negativo = df_filtrado[df_filtrado['Valor'] < 0]
        df_negativo_agrupado = df_negativo.groupby('Plano de contas')['Valor'].sum().abs().reset_index()
        if not df_negativo_agrupado.empty:
            top_5 = df_negativo_agrupado.nlargest(5, 'Valor')
            fig3 = px.bar(
                top_5,
                y='Plano de contas',
                x='Valor',
                orientation='h',
                title='Top 5 Categorias de Despesas',
                labels={'Valor': 'Valor (R$)', 'Plano de contas': 'Plano de Contas'},
                template='plotly_dark',
                color_discrete_sequence=['#ff1493']
            )
            fig3.update_layout(
                yaxis={'categoryorder':'total ascending'},
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#39ff14')
            )
            fig3.update_xaxes(tickprefix="R$ ")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.write("Não há valores negativos para exibir nas top 5 despesas.")
    
        # Novo Gráfico: DRE Mensal - Entradas vs Saídas
        st.subheader("DRE Mensal: Entradas vs Saídas")
        # Reutiliza a coluna 'Mês/Ano'
        df_filtrado['Mês/Ano'] = df_filtrado['Data'].dt.to_period('M').astype(str)
    
        # Agrupa entradas e saídas separadamente
        df_entradas = df_filtrado[df_filtrado['Valor'] > 0].groupby('Mês/Ano')['Valor'].sum().reset_index()
        df_saidas = df_filtrado[df_filtrado['Valor'] < 0].groupby('Mês/Ano')['Valor'].sum().reset_index()
        df_saidas['Valor'] = df_saidas['Valor'].abs()  # Converte para valor absoluto
    
        # Adiciona coluna identificando o tipo
        df_entradas['Tipo'] = 'Entradas'
        df_saidas['Tipo'] = 'Saídas'
    
        # Concatena os dois dataframes para visualização conjunta
        df_dre = pd.concat([df_entradas, df_saidas], axis=0)
    
        if not df_dre.empty:
            fig_dre = px.bar(
                df_dre,
                x='Mês/Ano',
                y='Valor',
                color='Tipo',
                barmode='group',
                title='DRE Mensal: Entradas vs Saídas',
                labels={'Valor': 'Valor (R$)'},
                template='plotly_dark'
            )
            fig_dre.update_yaxes(tickprefix="R$ ")
            st.plotly_chart(fig_dre, use_container_width=True)
        else:
            st.write("Não há dados suficientes para exibir o gráfico DRE.")
    
    # --- Aba Exportação ---
    with tab4:
        st.subheader("Exportar Resumo")
        csv_data = convert_df(summary_pivot)
        st.download_button(
            label="💾 Exportar Resumo para CSV",
            data=csv_data,
            file_name='Resumo_Plano_De_Contas.csv',
            mime='text/csv'
        )
else:
    st.warning("Por favor, faça o upload de um arquivo Excel para começar.")
