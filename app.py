import pandas as pd
import streamlit as st
import plotly.express as px
import pycountry as pc
import base64

st.set_page_config(page_title="Data Salary Dashboard", page_icon="📊", layout="wide")

df = pd.read_csv("data_salaries_database.csv")

df_clean = df.dropna()

df_clean = df_clean.assign(work_year=df_clean["work_year"].astype("Int64"))


def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


image_base64 = get_base64_image("public/support_me_on_kofi_blue.png")

senioridade = {
    "SE": "Senior",
    "MI": "Mid",
    "EN": "Junior",
    "EX": "Executive",
}
df["experience_level"] = df["experience_level"].replace(senioridade)
tipo_emprego = {
    "FT": "Full-time",
    "PT": "Part-time",
    "CT": "Contract",
    "FL": "Freelance",
}
df["employment_type"] = df["employment_type"].replace(tipo_emprego)

tamanho_empresa = {
    "S": "Small",
    "M": "Medium",
    "L": "Large",
}
df["company_size"] = df["company_size"].replace(tamanho_empresa)

remoto = {0: "Office", 50: "Hybrid", 100: "Remote"}

df["remote_ratio"] = df["remote_ratio"].replace(remoto)


st.sidebar.header("🔍 Filters")

# Filtro de Ano
anos_disponiveis = sorted(df_clean["work_year"].unique())
anos_selecionados = st.sidebar.multiselect(
    "Year", anos_disponiveis, default=anos_disponiveis
)

# Filtro de Senioridade
senioridades_disponiveis = sorted(df["experience_level"].unique())
senioridades_selecionadas = st.sidebar.multiselect(
    "Seniority", senioridades_disponiveis, default=senioridades_disponiveis
)

# Filtro por Tipo de Contrato
contratos_disponiveis = sorted(df["employment_type"].unique())
contratos_selecionados = st.sidebar.multiselect(
    "Contract Type", contratos_disponiveis, default=contratos_disponiveis
)

# Filtro por Tamanho da Empresa
tamanhos_disponiveis = sorted(df["company_size"].unique())
tamanhos_selecionados = st.sidebar.multiselect(
    "Company Size", tamanhos_disponiveis, default=tamanhos_disponiveis
)


def to_iso3(code):
    try:
        return pc.countries.get(alpha_2=code).alpha_3
    except:
        return None


df["residencia_iso3"] = df["employee_residence"].apply(to_iso3)

# --- Filtragem do DataFrame ---
# O dataframe principal é filtrado com base nas seleções feitas na barra lateral.
df_filtrado = df[
    (df["work_year"].isin(anos_selecionados))
    & (df["experience_level"].isin(senioridades_selecionadas))
    & (df["employment_type"].isin(contratos_selecionados))
    & (df["company_size"].isin(tamanhos_selecionados))
]


st.title("🎲 Data Salary Analysis Dashboard")
st.markdown(
    "#### Explore data salaries over recent years. Use the filters on the left to refine your analysis."
)

# --- Main Metrics (KPIs) ---
st.subheader("Main Metrics (Annual Salary in USD)")

if not df_clean.empty:
    average_salary = df["salary_in_usd"].mean()
    max_salary = df["salary_in_usd"].max()
    total_records = df.shape[0]
    most_frequent_job = df["job_title"].mode()[0]
else:
    (
        average_salary,
        median_salary,
        max_salary,
        total_records,
        most_frequent_job,
    ) = (0, 0, 0, "")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Average Salary", f"${average_salary:,.0f}")
col2.metric("Maximum Salary", f"${max_salary:,.0f}")
col3.metric("Total Records", f"{total_records:,}")
col4.metric("Most Frequent Job", most_frequent_job)

st.markdown("---")

# --- Análises Visuais com Plotly ---
st.subheader("Graphs")

col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    if not df_filtrado.empty:
        top_cargos = (
            df_filtrado.groupby("job_title")["salary_in_usd"]
            .mean()
            .nlargest(10)
            .sort_values(ascending=True)
            .reset_index()
        )
        grafico_cargos = px.bar(
            top_cargos,
            x="salary_in_usd",
            y="job_title",
            orientation="h",
            title="Top 10 Job Titles by Average Salary",
            labels={"salary_in_usd": "Average Annual Salary (USD)", "job_title": ""},
        )
        grafico_cargos.update_layout(
            title_x=0.1, yaxis={"categoryorder": "total ascending"}
        )
        st.plotly_chart(grafico_cargos, use_container_width=True)
    else:
        st.warning("No data available for the job titles chart.")

with col_graf2:
    if not df_clean.empty:
        grafico_hist = px.histogram(
            df_clean,
            x="salary_in_usd",
            nbins=30,
            title="Annual Salary Distribution",
            labels={"salary_in_usd": "Salary Average (USD)", "count": ""},
        )
        grafico_hist.update_layout(title_x=0.1)
        st.plotly_chart(grafico_hist, use_container_width=True)
    else:
        st.warning("No data available for the salary distribution chart.")

col_graf3, col_graf4 = st.columns(2)

with col_graf3:
    if not df_filtrado.empty:
        remoto_contagem = df_filtrado["remote_ratio"].value_counts().reset_index()
        remoto_contagem.columns = ["remote_ratio", "quantity"]
        grafico_remoto = px.pie(
            remoto_contagem,
            names="remote_ratio",
            values="quantity",
            title="Proportion of Employment Types",
            hole=0.5,
        )
        grafico_remoto.update_traces(textinfo="percent+label")
        grafico_remoto.update_layout(title_x=0.1)
        st.plotly_chart(grafico_remoto, use_container_width=True)
    else:
        st.warning("No data available for the employment types chart.")


with col_graf4:
    if not df_filtrado.empty:
        df_ds = df_filtrado[df_filtrado["job_title"] == "Data Scientist"]
        media_ds_pais = (
            df_ds.groupby("residencia_iso3")["salary_in_usd"].mean().reset_index()
        )
        grafico_paises = px.choropleth(
            media_ds_pais,
            locations="residencia_iso3",
            color="salary_in_usd",
            color_continuous_scale="rdylgn",
            title="Average Salary of Data Scientists by Country",
            labels={
                "salary_in_usd": "Average Salary (USD)",
                "employee_residence": "Country",
            },
        )
        grafico_paises.update_layout(title_x=0.1)
        st.plotly_chart(grafico_paises, use_container_width=True)
    else:
        st.warning("No data available for the countries chart.")
# --- Detailed Data Table ---
with st.expander(f"📋 Detailed Data ({len(df_filtrado):,} records)", expanded=False):
    st.dataframe(df_filtrado)

# --- Footer ---
st.markdown(
    f"""
    <p style='text-align: center;'>Created with ❤️ by IgorJFS</p>
    <div style="display: flex; justify-content: center; margin: 20px 0;">
        <a href="https://ko-fi.com/zackiewackie" target="_blank">
            <img src="data:image/png;base64,{image_base64}" alt="Support me on Ko-fi" style="height: 40px;">
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)
