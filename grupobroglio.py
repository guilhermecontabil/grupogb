import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import openpyxl
import plotly.express as px
import random
import os

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

# Função para carregar ou substituir o arquivo Excel
DEFAULT_FILE_PATH = "default_data.xlsx"

if os.path.exists(DEFAULT_FILE_PATH):
    default_file = pd.read_excel(DEFAULT_FILE_PATH)
else:
    default_file = None

uploaded_file = st.file_uploader("Importar ou substituir o arquivo Excel", type=["xlsx"])

if uploaded_file:
    # Salvar o arquivo como padrão
    with open(DEFAULT_FILE_PATH, "wb") as f:
        f.write(uploaded_file.getbuffer())
    df = pd.read_excel(uploaded_file)
    st.success("Arquivo carregado com sucesso e definido como padrão.")
elif default_file is not None:
    st.info("Usando arquivo padrão salvo anteriormente.")
    df = default_file
else:
    st.warning("Por favor, faça o upload de um arquivo Excel para começar.")
    df = None

if df is not None:
    # Tratamento de dados (formatação de datas)
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')

    # Filtro por loja
    lojas = df['Loja'].unique()
    loja_selecionada = st.selectbox("Filtrar por Loja:", ["Todas as Lojas"] + list(lojas))

    # Aplicando o filtro de loja
    if loja_selecionada != "Todas as Lojas":
        df_filtrado = df[df['Loja'] == loja_selecionada]
    else:
        df_filtrado = df

    # Exibir dados em uma tabela
    st.write("### Dados Importados")
    st.dataframe(df_filtrado)

    # Exibir cards de resumo com totais
    st.write("### Resumo de Vendas")
    total_vendas = df_filtrado[df_filtrado['Plano de contas'].str.contains(r'(?i)^vendas$', na=False)]['Valor'].sum()
    total_vendas_balcao = df_filtrado[df_filtrado['Plano de contas'].str.contains(r'(?i)vendas no balcão', na=False)]['Valor'].sum()

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

    # Resumo por plano de contas agrupado por Mês/Ano
    df_filtrado['Mês/Ano'] = df_filtrado['Data'].dt.to_period('M')
    summary = df_filtrado.groupby(['Plano de contas', 'Mês/Ano'])['Valor'].sum().reset_index()

    st.write("### Total por Plano de Contas (Agrupado por Mês/Ano)")
    summary_pivot = summary.pivot(index='Plano de contas', columns='Mês/Ano', values='Valor').fillna(0)
    summary_pivot['Total'] = summary_pivot.sum(axis=1)
    st.dataframe(summary_pivot)

    # Gráfico de Entradas de Disponibilidade (valores positivos) - Usando Plotly para interatividade
    st.write("### Gráfico de Entradas de Disponibilidade (Valores Positivos)")
    df_positivo = df_filtrado[df_filtrado['Valor'] > 0]
    df_positivo_agrupado = df_positivo.groupby('Plano de contas')['Valor'].sum().reset_index()
    if not df_positivo_agrupado.empty:
        fig = px.bar(df_positivo_agrupado, x='Plano de contas', y='Valor', color='Plano de contas', title='Entradas de Disponibilidade por Plano de Contas', labels={'Valor': 'Valor (R$)'}, template='plotly_dark')
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Não há valores positivos para exibir.")

    # Top 5 categorias de despesas - Usando Plotly para interatividade
    st.write("### Top 5 Categorias de Despesas")
    df_negativo = df_filtrado[df_filtrado['Valor'] < 0]
    df_negativo_agrupado = df_negativo.groupby('Plano de contas')['Valor'].sum().abs().reset_index()
    if not df_negativo_agrupado.empty:
        top_5 = df_negativo_agrupado.nsmallest(5, 'Valor')
        fig3 = px.bar(top_5, y='Plano de contas', x='Valor', orientation='h', title='Top 5 Categorias de Despesas', labels={'Valor': 'Valor (R$)', 'Plano de contas': 'Plano de Contas'}, template='plotly_dark', color_discrete_sequence=['#ff6347'])
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.write("Não há valores negativos para exibir nas top 5 despesas.")

    # Exportar Tabela para CSV
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    st.write("### Exportar Resumo para Excel")
    csv_data = convert_df(summary_pivot)
    st.download_button(label="Exportar para CSV", data=csv_data, file_name='Resumo_Plano_De_Contas.csv', mime='text/csv')
