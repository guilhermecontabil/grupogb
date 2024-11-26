import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import random

# Configurar a página do Streamlit
st.set_page_config(page_title="Dashboard Financeira", layout="wide")

# Título da aplicação
st.title("Dashboard Financeira")

# Upload do arquivo Excel
uploaded_file = st.file_uploader("Faça upload do arquivo Excel", type=["xlsx"])

# Verificar se o arquivo foi carregado
if uploaded_file:
    # Carregar o arquivo Excel
    df = pd.read_excel(uploaded_file)

    # Limpar e exibir os dados
    st.write("### Dados Importados:")
    st.dataframe(df)

    # Criar um filtro por loja
    lojas = df['Loja'].unique()
    loja_selecionada = st.selectbox("Selecione a Loja:", ["Todas as Lojas"] + list(lojas))

    # Filtrar os dados com base na loja selecionada
    if loja_selecionada != "Todas as Lojas":
        df = df[df['Loja'] == loja_selecionada]

    # Exibir totais
    total_vendas = df[df['Plano de contas'].str.contains('vendas', case=False)]['Valor'].sum()
    total_vendas_balcao = df[df['Plano de contas'].str.contains('vendas no balcão', case=False)]['Valor'].sum()

    col1, col2 = st.columns(2)
    col1.metric("Total Vendas", f"R$ {total_vendas:,.2f}")
    col2.metric("Total Vendas Balcão", f"R$ {total_vendas_balcao:,.2f}")

    # Função para gerar uma cor aleatória
    def get_random_color():
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    # Gráfico de Entradas de Disponibilidade (Valores Positivos)
    st.write("### Gráfico de Entradas de Disponibilidade")
    df_positivo = df[df['Valor'] > 0]
    categorias_positivas = df_positivo['Plano de contas'].unique()
    valores_por_categoria_positiva = df_positivo.groupby('Plano de contas')['Valor'].sum()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(categorias_positivas, valores_por_categoria_positiva, color='green', alpha=0.7)
    ax.set_ylabel('Valor (R$)')
    ax.set_title('Entradas de Disponibilidade (Valores Positivos)')
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    st.pyplot(fig)

    # Gráfico de Despesas (Valores Negativos)
    st.write("### Gráfico de Despesas (Valores Negativos)")
    df_negativo = df[df['Valor'] < 0]
    categorias_negativas = df_negativo['Plano de contas'].unique()
    valores_por_categoria_negativa = df_negativo.groupby('Plano de contas')['Valor'].sum()

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    ax2.bar(categorias_negativas, valores_por_categoria_negativa, color='red', alpha=0.7)
    ax2.set_ylabel('Valor (R$)')
    ax2.set_title('Despesas (Valores Negativos)')
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    st.pyplot(fig2)

    # Top 5 categorias de despesas
    st.write("### Top 5 Categorias de Despesas (Valores Negativos)")
    top_despesas = df_negativo.groupby('Plano de contas')['Valor'].sum().nsmallest(5)

    fig3, ax3 = plt.subplots(figsize=(10, 6))
    ax3.bar(top_despesas.index, top_despesas.values, color='orange', alpha=0.7)
    ax3.set_ylabel('Valor (R$)')
    ax3.set_title('Top 5 Categorias de Despesas (Valores Negativos)')
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    st.pyplot(fig3)

    # Filtro de Contas para Card de Resumo
    st.write("### Filtrar Contas para Resumo")
    conta_filtrada = st.text_input("Digite o nome da Conta para filtrar:")

    if conta_filtrada:
        df_filtrado = df[df['Plano de contas'].str.contains(conta_filtrada, case=False, na=False)]
        total_conta = df_filtrado['Valor'].sum()
        st.metric(f"Total da Conta Filtrada: {conta_filtrada}", f"R$ {total_conta:,.2f}")
