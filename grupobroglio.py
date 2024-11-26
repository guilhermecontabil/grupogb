import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

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

    # Gráfico de Entradas de Disponibilidade
    st.write("### Gráfico de Entradas de Disponibilidade")
    categorias = df['Plano de contas'].unique()
    valores_por_categoria = df.groupby('Plano de contas')['Valor'].sum()
    
    fig, ax = plt.subplots()
    ax.bar(categorias, valores_por_categoria)
    ax.set_ylabel('Valor')
    ax.set_title('Entradas de Disponibilidade')
    plt.xticks(rotation=45, ha="right")

    st.pyplot(fig)

    # Top 5 categorias de despesas (valores negativos)
    st.write("### Top 5 Categorias de Despesas (Valores Negativos)")
    despesas = df[df['Valor'] < 0].groupby('Plano de contas')['Valor'].sum().nsmallest(5)

    fig2, ax2 = plt.subplots()
    ax2.bar(despesas.index, despesas.values, color='red')
    ax2.set_ylabel('Valor')
    ax2.set_title('Top 5 Categorias de Despesas')
    plt.xticks(rotation=45, ha="right")

    st.pyplot(fig2)

    # Filtro de Contas para Card de Resumo
    st.write("### Filtrar Contas para Resumo")
    conta_filtrada = st.text_input("Digite o nome da Conta para filtrar:")

    if conta_filtrada:
        df_filtrado = df[df['Plano de contas'].str.contains(conta_filtrada, case=False, na=False)]
        total_conta = df_filtrado['Valor'].sum()
        st.metric(f"Total da Conta Filtrada: {conta_filtrada}", f"R$ {total_conta:,.2f}")
