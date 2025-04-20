import streamlit as st
import pandas as pd
import unidecode
from io import BytesIO

st.set_page_config(page_title="App de Vendas e Consumo", layout="wide")
st.title("\U0001F4CA Análises do Restaurante")

# Função auxiliar de normalização de texto
def normalizar(texto):
    return unidecode.unidecode(str(texto)).lower().strip()

# ========================== ANALISADOR DE VENDAS ==========================
# ... [NENHUMA ALTERAÇÃO NESTA PARTE] ...

# ========================== ANALISADOR DE CONSUMO CORRIGIDO ==========================
st.divider()
st.header("\U0001F4E6 Análise de Consumo de Estoque")
file_consumo = st.file_uploader("Faça upload da planilha de CONSUMO", type=["xlsx"], key="consumo")

if file_consumo:
    df = pd.read_excel(file_consumo)
    df = df.dropna(how="all")

    if df.shape[1] < 12:
        st.error("⚠️ A planilha precisa conter as 3 seções (Estoque Inicial, Compras e Estoque Final) lado a lado, cada uma com 4 colunas.")
    else:
        ini = df.iloc[:, :4].copy()
        compras = df.iloc[:, 4:8].copy()
        fim = df.iloc[:, 8:12].copy()

        ini.columns = compras.columns = fim.columns = ["item", "quantidade", "valor unitario", "valor total"]
        ini = ini.dropna(subset=["item"])
        compras = compras.dropna(subset=["item"])
        fim = fim.dropna(subset=["item"])

        def limpar(df):
            df = df.copy()
            df["item"] = df["item"].astype(str).str.lower().str.strip()
            df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce").fillna(0)
            df["valor total"] = df["valor total"].astype(str).str.replace("[^0-9,.-]", "", regex=True).str.replace(".", "", regex=False).str.replace(",", ".").astype(float)
            return df.groupby("item")["quantidade", "valor total"].sum().reset_index()

        ini = limpar(ini)
        compras = limpar(compras)
        fim = limpar(fim)

        base = pd.merge(ini, compras, on="item", how="outer", suffixes=("_ini", "_ent"))
        base = pd.merge(base, fim, on="item", how="outer")
        base = base.rename(columns={"quantidade": "quant_fim", "valor total": "total_fim"})

        base = base.fillna(0)
        base["quant_consumo"] = base["quantidade_ini"] + base["quantidade_ent"] - base["quant_fim"]
        base["total_consumo"] = base["valor total_ini"] + base["valor total_ent"] - base["total_fim"]

        resultado = base[["item", "quant_consumo", "total_consumo"]]
        resultado = resultado[resultado["quant_consumo"] > 0]
        resultado = resultado.sort_values(by="total_consumo", ascending=False).reset_index(drop=True)

        def destacar_top_5(val):
            cor = 'color: red; font-weight: bold' if val.name < 5 else ''
            return [cor] * len(val)

        st.subheader("\U0001F4E6 Relatório de Consumo de Insumos")
        st.dataframe(
            resultado.style
                .apply(destacar_top_5, axis=1)
                .format({"quant_consumo": "{:.2f}", "total_consumo": "R$ {:,.2f}"}),
            use_container_width=True
        )

        excel_consumo = BytesIO()
        resultado.to_excel(excel_consumo, index=False, engine='openpyxl')
        st.download_button("\U0001F4C5 Baixar Consumo de Estoque (.xlsx)", data=excel_consumo.getvalue(), file_name="analise_consumo_estoque.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
