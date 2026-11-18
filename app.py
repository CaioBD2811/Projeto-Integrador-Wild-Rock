import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da Página
st.set_page_config(
    page_title="Dashboard Wild Rock Store",
    page_icon="🎸",
    layout="wide"
)

# Estilo Visual Dark (Rock Theme)
st.markdown("""
    <style>
    .main { background-color: #121212; color: #FFFFFF; }
    .stMetric { background-color: #1A1A1A; padding: 15px; border-radius: 8px; border: 1px solid #333333; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def carregar_dados():
    excel_path = "Base_Dados_Wild_Rock_BI_2025.xlsx"
    xls = pd.ExcelFile(excel_path)
    
    produtos = pd.read_excel(xls, 'Produtos')
    vendas = pd.read_excel(xls, 'Vendas')
    estoque = pd.read_excel(xls, 'Estoque')
    calendario = pd.read_excel(xls, 'Calendario')
    
    # Merge das tabelas de vendas
    df = vendas.merge(produtos, on='ID_Produto', how='left').merge(calendario, left_on='Data_Venda', right_on='Data', how='left')
    return df, produtos, estoque, calendario

df, produtos, estoque, calendario = carregar_dados()

# Título Principal do Dashboard (Exigência do Slide)
st.title("🎸 Dashboard Executivo - Wild Rock Store (2025)")
st.markdown("Painel interativo de Business Intelligence para análise de vendas, lucratividade, mix de estilos e controle de estoque.")
st.markdown("---")

# Barra Lateral de Filtros Interativos
st.sidebar.header("🔍 Filtros do Dashboard")
mes_selecionado = st.sidebar.multiselect("Selecione o Mês:", options=calendario['Mes_Nome'].unique(), default=calendario['Mes_Nome'].unique())
cat_selecionada = st.sidebar.multiselect("Selecione a Categoria:", options=df['Categoria'].unique(), default=df['Categoria'].unique())
subcat_selecionada = st.sidebar.multiselect("Selecione o Estilo Rock (Subcategoria):", options=df['Subcategoria'].unique(), default=df['Subcategoria'].unique())

# Filtrar DataFrame com base na barra lateral
df_filtrado = df[
    (df['Mes_Nome'].isin(mes_selecionado)) &
    (df['Categoria'].isin(cat_selecionada)) &
    (df['Subcategoria'].isin(subcat_selecionada))
]

# Exigência: Mínimo de 4 Visualizações (KPIs contam como bloco inicial + 4 gráficos)
# 1. CARTÕES DE KPIS (Visualização 1)
col1, col2, col3, col4 = st.columns(4)

fat_total = df_filtrado['Valor_Total'].sum()
lucro_total = df_filtrado['Lucro_Bruto'].sum()
margem_media = (lucro_total / fat_total * 100) if fat_total > 0 else 0
pedidos_total = df_filtrado['ID_Pedido'].nunique()
itens_total = df_filtrado['Quantidade'].sum()
ticket_medio = fat_total / pedidos_total if pedidos_total > 0 else 0

col1.metric("💰 Faturamento Total", f"R$ {fat_total:,.2f}", "Meta Anual Atingida")
col2.metric("📈 Lucro Bruto", f"R$ {lucro_total:,.2f}", f"Margem: {margem_media:.1f}%")
col3.metric("📦 Total de Pedidos", f"{pedidos_total} Pedidos", f"{itens_total} Itens")
col4.metric("🏷️ Ticket Médio", f"R$ {ticket_medio:,.2f}", "Por Pedido")

st.markdown("---")

# Linha 1 de Gráficos: Linha e Rosca
col_g1, col_g2 = st.columns([2, 1])

with col_g1:
    st.subheader("📊 Evolução Mensal de Faturamento e Lucro")
    df_mensal = df_filtrado.groupby(['Mes_Numero', 'Mes_Nome']).agg({'Valor_Total': 'sum', 'Lucro_Bruto': 'sum'}).reset_index().sort_values('Mes_Numero')
    
    fig_linha = px.line(df_mensal, x='Mes_Nome', y=['Valor_Total', 'Lucro_Bruto'], 
                        labels={'value': 'Valor (R$)', 'Mes_Nome': 'Mês', 'variable': 'Métrica'},
                        markers=True, color_discrete_sequence=['#E63946', '#457B9D'])
    fig_linha.update_layout(plot_bgcolor='#1A1A1A', paper_bgcolor='#1A1A1A', font_color='#FFFFFF')
    st.plotly_chart(fig_linha, use_container_width=True)

with col_g2:
    st.subheader("🍩 Share por Estilo Rock")
    df_subcat = df_filtrado.groupby('Subcategoria')['Valor_Total'].sum().reset_index()
    fig_pizza = px.pie(df_subcat, names='Subcategoria', values='Valor_Total', hole=0.4,
                       color_discrete_sequence=px.colors.qualitative.Bold)
    fig_pizza.update_layout(plot_bgcolor='#1A1A1A', paper_bgcolor='#1A1A1A', font_color='#FFFFFF', legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig_pizza, use_container_width=True)

# Linha 2 de Gráficos: Barras de Categoria e Alerta de Estoque
col_g3, col_g4 = st.columns(2)

with col_g3:
    st.subheader("👕 Faturamento por Categoria de Produto")
    df_cat = df_filtrado.groupby('Categoria')['Valor_Total'].sum().reset_index().sort_values('Valor_Total', ascending=True)
    fig_bar = px.bar(df_cat, x='Valor_Total', y='Categoria', orientation='h',
                     text_auto='.2s', color='Valor_Total', color_continuous_scale='Reds')
    fig_bar.update_layout(plot_bgcolor='#1A1A1A', paper_bgcolor='#1A1A1A', font_color='#FFFFFF', coloraxis_showscale=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_g4:
    st.subheader("⚠️ Top Produtos com Menor Estoque (Alerta de Ruptura)")
    # Calcular saldo final de estoque
    mov = estoque.groupby(['ID_Produto', 'Tipo_Movimentacao'])['Quantidade'].sum().unstack(fill_value=0).reset_index()
    est_final = produtos[['ID_Produto', 'Nome_Produto', 'Quantidade_Estoque_Inicial']].merge(mov, on='ID_Produto', how='left').fillna(0)
    est_final['Saldo_Final'] = est_final['Quantidade_Estoque_Inicial'] + est_final.get('Entrada', 0) - est_final.get('Saída', 0)
    est_final = est_final.sort_values('Saldo_Final').head(5)
    
    fig_est = px.bar(est_final, x='Saldo_Final', y='Nome_Produto', orientation='h',
                     text='Saldo_Final', color='Saldo_Final', color_continuous_scale='Oranges')
    fig_est.update_layout(plot_bgcolor='#1A1A1A', paper_bgcolor='#1A1A1A', font_color='#FFFFFF', coloraxis_showscale=False)
    st.plotly_chart(fig_est, use_container_width=True)

st.markdown("---")
st.markdown("💡 **Desenvolvido para o Projeto Integrador (Senac EAD - ADS)** | Base de Dados Real: *Wild Rock Store 2025*")