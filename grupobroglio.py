import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import openpyxl
import random

# Configuração inicial da página do Streamlit
st.set_page_config(page_title="Dashboard Financeira", layout="wide")

# Estilos CSS personalizados para a interface
st.markdown("""
    <style>
        body {
            background-color: #1c1f26;
            color: #e0e0e0;
            font-family: 'Roboto', sans-serif;
        }
        h2, h3 {
            color: #ffffff;
        }
        .card-summary {
            margin-bottom: 20px;
            padding: 30px;
            border-radius: 15px;
            background-color: #3a3f4b;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
            text-align: center;
        }
        .card-summary h4 {
            font-size: 1.7rem;
            color: #17a2b8;
        }
        .card-summary span {
            font-size: 2.5rem;
            font-weight: bold;
            color: #17a2b8;
        }
        .dataframe {
            margin-top: 20px;
            background-color: #2a2e38;
            color: #ffffff;
        }
    </style>
""", unsafe_allow_html=True)

# Título da página
st.title("Dashboard Financeira - Importar Excel e Gerar Resumo")

# Upload do arquivo Excel
uploaded_file = st.file_uploader("Importar Arquivo Excel", type=["xlsx"])

if uploaded_file:
    # Leitura do arquivo Excel
    df = pd.read_excel(uploaded_file)

    # Tratamento de dados (formatação de datas)
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')

    # Filtro por loja
    lojas = df['Loja'].unique()
    loja_selecionada = st.selectbox("Filtrar por Loja:", ["Todas as Lojas"] + list(lojas))

    # Aplicando o filtro de loja
    if loja_selecionada != "Todas as Lojas":
        df = df[df['Loja'] == loja_selecionada]

    # Exibir dados em uma tabela
    st.write("### Dados Importados")
    st.dataframe(df)

    # Exibir cards de resumo com totais
    st.write("### Resumo de Vendas")
    total_vendas = df[df['Plano de contas'].str.contains('vendas', case=False)]['Valor'].sum()
    total_vendas_balcao = df[df['Plano de contas'].str.contains('vendas no balcão', case=False)]['Valor'].sum()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <div class="card-summary">
                <h4>Total Vendas</h4>
                <span>R$ {:,.2f}</span>
            </div>
        """.format(total_vendas), unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div class="card-summary">
                <h4>Total Vendas Balcão</h4>
                <span>R$ {:,.2f}</span>
            </div>
        """.format(total_vendas_balcao), unsafe_allow_html=True)

    # Função para gerar uma cor aleatória para os gráficos
    def get_random_color():
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    # Resumo por plano de contas agrupado por Mês/Ano
    df['Mês/Ano'] = df['Data'].dt.to_period('M')
    summary = df.groupby(['Plano de contas', 'Mês/Ano'])['Valor'].sum().reset_index()

    st.write("### Total por Plano de Contas (Agrupado por Mês/Ano)")
    summary_pivot = summary.pivot(index='Plano de contas', columns='Mês/Ano', values='Valor').fillna(0)
    summary_pivot['Total'] = summary_pivot.sum(axis=1)
    st.dataframe(summary_pivot)

    # Gráfico de Entradas de Disponibilidade (valores positivos)
    st.write("### Gráfico de Entradas de Disponibilidade (Valores Positivos)")
    df_positivo = df[df['Valor'] > 0]
    if not df_positivo.empty:
        fig, ax = plt.subplots(figsize=(12, 6))
        df_positivo.groupby('Plano de contas')['Valor'].sum().plot(kind='bar', ax=ax, color='green', alpha=0.8)
        ax.set_ylabel("Valor (R$)")
        ax.set_title("Entradas de Disponibilidade por Plano de Contas")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.write("Não há valores positivos para exibir.")

    # Top 5 categorias de despesas
    st.write("### Top 5 Categorias de Despesas")
    df_negativo = df[df['Valor'] < 0]
    if not df_negativo.empty:
        top_5 = df_negativo.groupby('Plano de contas')['Valor'].sum().nsmallest(5).abs()
        fig3, ax3 = plt.subplots(figsize=(12, 6))
        top_5.plot(kind='barh', ax=ax3, color='#ff6347', alpha=0.8)
        ax3.set_xlabel("Valor (R$)")
        ax3.set_title("Top 5 Categorias de Despesas")
        plt.tight_layout()
        st.pyplot(fig3)
    else:
        st.write("Não há valores negativos para exibir nas top 5 despesas.")

    # Exportar Tabela para CSV
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    st.write("### Exportar Resumo para Excel")
    csv_data = convert_df(summary_pivot)
    st.download_button(label="Exportar para CSV", data=csv_data, file_name='Resumo_Plano_De_Contas.csv', mime='text/csv')
