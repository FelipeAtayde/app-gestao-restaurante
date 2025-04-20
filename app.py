import streamlit as st
import pandas as pd
import unidecode
from io import BytesIO

st.set_page_config(page_title="App de Vendas e Consumo", layout="wide")
st.title("📊 Análises do Restaurante")

# Função auxiliar de normalização de texto
def normalizar(texto):
    return unidecode.unidecode(str(texto)).lower().strip()

# ========================== ANALISADOR DE VENDAS ==========================
st.header("🍽️ Análise de Maiores Vendas")
file_vendas = st.file_uploader("Faça upload da planilha de VENDAS", type=["xlsx"], key="vendas")

if file_vendas:
    df_vendas = pd.read_excel(file_vendas, skiprows=3)
    df_vendas["Itens e Opções"] = df_vendas["Itens e Opções"].astype(str).apply(normalizar)

    mult = {
        "- 2 pequenos": 2, "- 3 pequenos": 3, "- 4 pequenos": 4,
        "- 2 grandes": 2, "- 3 grandes": 3, "- 4 grandes": 4
    }
    for k, m in mult.items():
        df_vendas.loc[df_vendas["Itens e Opções"].str.contains(k), "Quantidade"] *= m

    pequeno = df_vendas["Itens e Opções"].str.contains("pequeno") & ~df_vendas["Itens e Opções"].str.contains("combo")
    grande = df_vendas["Itens e Opções"].str.contains("grande") & ~df_vendas["Itens e Opções"].str.contains("combo")
    total_p, total_g = int(df_vendas.loc[pequeno, "Quantidade"].sum()), int(df_vendas.loc[grande, "Quantidade"].sum())
    total_geral = total_p + total_g

    pratos = {
        "Boi": lambda x: "boi" in x and "combo" not in x,
        "Parmegiana": lambda x: "parmegiana" in x and "combo" not in x,
        "Strogonoff": lambda x: "strogonoff" in x and "combo" not in x,
        "Feijoada": lambda x: "feijoada" in x and "2 feijoadas" not in x,
        "Tropeiro": lambda x: "tropeiro" in x and "tropeguete" not in x,
        "Tropeguete": lambda x: "tropeguete" in x,
        "Espaguete": lambda x: "espaguete" in x and "tropeguete" not in x,
        "Porco": lambda x: "porco" in x and "combo" not in x,
        "Frango": lambda x: "frango" in x and "parmegiana" not in x and "2 frangos + fritas" not in x
    }
    combos = {
        "Combo Todo Dia": lambda x: "combo todo dia" in x,
        "2 Pratos - À Sua Escolha": lambda x: "2 pratos" in x and "escolha" in x,
        "Combo Supremo": lambda x: "combo supremo" in x,
        "2 Feijoadas": lambda x: "2 feijoadas" in x,
        "2 Frangos + Fritas": lambda x: "2 frangos" in x and "fritas" in x
    }
    refrigerantes = {
        "Coca-Cola Original 350 ml": [["coca", "original", "350"]],
        "Coca-Cola Zero e Sem Açúcar 350 ml": [["coca", "zero", "350"], ["coca", "sem acucar", "350"]],
        "Coca-Cola Original 600 ml": [["coca", "original", "600"]],
        "Coca-Cola Zero 600 ml": [["coca", "zero", "600"], ["coca", "sem acucar", "600"]],
        "Coca-Cola 2 Litros": [["coca", "2l"], ["coca", "2 l"], ["coca", "2litro"]],
        "Guaraná Antarctica 350 ml": [["guarana", "350"]],
        "Guaraná Antarctica 1 Litro": [["guarana", "antarctica", "1l"], ["guarana", "antarctica", "1 l"], ["guarana", "antarctica", "1litro"]],
        "Guaraná Antarctica 2 Litros": [["guarana", "2l"], ["guarana", "2 l"], ["guarana", "2litro"]],
        "Suco": [["suco"]],
        "Refrigerante Mate Couro 1 Litro": [["mate couro", "1l"], ["guarana mate", "1l"], ["mate couro", "1 l"], ["guarana mate", "1 l"], ["mate couro", "1litro"], ["guarana mate", "1litro"]]
    }

    def contem_tags(texto, listas):
        return any(all(tag in texto for tag in tags) for tags in listas)

    resumo = []
    for nome, cond in pratos.items():
        f = df_vendas["Itens e Opções"].apply(cond)
        qtd = int(df_vendas.loc[f, "Quantidade"].sum())
        val = df_vendas.loc[f, "Valor Total"].sum()
        if qtd > 0:
            resumo.append({"Categoria": nome, "Quantidade": qtd, "Valor Total": f"R$ {val:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")})

    for nome, cond in combos.items():
        f = df_vendas["Itens e Opções"].apply(cond)
        qtd = int(df_vendas.loc[f, "Quantidade"].sum())
        val = df_vendas.loc[f, "Valor Total"].sum()
        if qtd > 0:
            resumo.append({"Categoria": nome, "Quantidade": qtd, "Valor Total": f"R$ {val:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")})

    for nome, tags in refrigerantes.items():
        f = df_vendas["Itens e Opções"].apply(lambda x: contem_tags(x, tags))
        qtd = int(df_vendas.loc[f, "Quantidade"].sum())
        val = df_vendas.loc[f, "Valor Total"].sum()
        if qtd > 0:
            resumo.append({"Categoria": nome, "Quantidade": qtd, "Valor Total": f"R$ {val:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")})

    resumo_df = pd.DataFrame(resumo)
    resumo_df["Valor Num"] = resumo_df["Valor Total"].str.replace("R\$ ", "", regex=True).str.replace(".", "", regex=False).str.replace(",", ".").astype(float)
    resumo_df = resumo_df.sort_values(by="Valor Num", ascending=False).drop(columns="Valor Num")

    st.subheader("Resumo de Pequenos e Grandes")
    st.write(f"Pequeno: {total_p}")
    st.write(f"Grande: {total_g}")
    st.write(f"Total: {total_geral}")

    st.subheader("📋 Resumo Final Agrupado")
    st.dataframe(resumo_df, use_container_width=True)

    excel_vendas = BytesIO()
    resumo_df.to_excel(excel_vendas, index=False, engine='openpyxl')
    st.download_button("📥 Baixar Análise de Vendas (.xlsx)", data=excel_vendas.getvalue(), file_name="analise_maiores_vendas.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ========================== ANALISADOR DE CONSUMO ==========================
st.divider()
st.header("📦 Análise de Consumo de Estoque")
file_consumo = st.file_uploader("Faça upload da planilha de CONSUMO", type=["xlsx"], key="consumo")

if file_consumo:
    df_consumo = pd.read_excel(file_consumo, sheet_name=None)
    abas = list(df_consumo.keys())

    if len(abas) >= 3:
        estoque_ini = df_consumo[abas[0]]
        compras = df_consumo[abas[1]]
        estoque_fim = df_consumo[abas[2]]

        def preparar(df):
            df.columns = [c.strip().lower() for c in df.columns]
            df = df.rename(columns={"valor unitario": "unit", "valor total": "total"})
            df["item"] = df["item"].astype(str).str.lower().str.strip()
            df = df.groupby("item")["quantidade", "total"].sum().reset_index()
            return df

        ini = preparar(estoque_ini)
        ent = preparar(compras)
        fim = preparar(estoque_fim)

        base = pd.merge(ini, ent, on="item", how="outer", suffixes=("_ini", "_ent"))
        base = pd.merge(base, fim, on="item", how="outer")
        base = base.rename(columns={"quantidade": "quant_fim", "total": "total_fim"})

        base = base.fillna(0)
        base["quant_consumo"] = base["quantidade_ini"] + base["quantidade_ent"] - base["quant_fim"]
        base["total_consumo"] = base["total_ini"] + base["total_ent"] - base["total_fim"]

        resultado = base[["item", "quant_consumo", "total_consumo"]]
        resultado = resultado[resultado["quant_consumo"] > 0]
        resultado = resultado.sort_values(by="total_consumo", ascending=False)

        st.subheader("📦 Relatório de Consumo de Insumos")
        st.dataframe(resultado, use_container_width=True)

        excel_consumo = BytesIO()
        resultado.to_excel(excel_consumo, index=False, engine='openpyxl')
        st.download_button("📥 Baixar Consumo de Estoque (.xlsx)", data=excel_consumo.getvalue(), file_name="analise_consumo_estoque.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.warning("⚠️ Planilha de consumo deve conter 3 abas: estoque inicial, compras e estoque final.")
