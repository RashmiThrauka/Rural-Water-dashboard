import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Drinking Water Access Dashboard", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def load_data():
    df = pd.read_csv(os.path.join(BASE_DIR, "API_SH.H2O.SMDW.ZS_DS2_en_csv_v2_3203.csv"), skiprows=4)
    meta = pd.read_csv(os.path.join(BASE_DIR, "Metadata_Country_API_SH.H2O.SMDW.ZS_DS2_en_csv_v2_3203.csv"))

    df = df.merge(meta[["Country Code", "Region", "IncomeGroup"]], on="Country Code", how="left")
    df = df[df["Region"].notna()].copy()
    df = df.drop(columns=["Unnamed: 70", "Indicator Name", "Indicator Code"], errors="ignore")

    year_cols = [str(y) for y in range(2000, 2023)]
    long = df.melt(
        id_vars=["Country Name", "Country Code", "Region", "IncomeGroup"],
        value_vars=year_cols,
        var_name="Year",
        value_name="Access"
    )
    long = long.dropna(subset=["Access"])
    long["Year"] = long["Year"].astype(int)
    long["Access"] = long["Access"].astype(float)
    return long

data = load_data()

st.title("Safely Managed Drinking Water Access")
st.markdown("Percentage of population using safely managed drinking water services (2000–2022)")
st.markdown("Source: World Bank — WHO/UNICEF Joint Monitoring Programme")
st.divider()

st.sidebar.header("Filters")

all_regions = sorted(data["Region"].unique())
selected_regions = st.sidebar.multiselect("Region", all_regions, default=all_regions)

all_income = sorted(data["IncomeGroup"].unique())
selected_income = st.sidebar.multiselect("Income Group", all_income, default=all_income)

year_range = st.sidebar.slider("Year Range", 2000, 2022, (2000, 2022))

filtered = data[
    (data["Region"].isin(selected_regions)) &
    (data["IncomeGroup"].isin(selected_income)) &
    (data["Year"] >= year_range[0]) &
    (data["Year"] <= year_range[1])
]

col1, col2, col3, col4 = st.columns(4)

latest = filtered[filtered["Year"] == filtered["Year"].max()]
earliest = filtered[filtered["Year"] == filtered["Year"].min()]

with col1:
    st.metric("Countries", latest["Country Name"].nunique())
with col2:
    avg_latest = latest["Access"].mean()
    st.metric("Avg Access (Latest Year)", f"{avg_latest:.1f}%")
with col3:
    avg_earliest = earliest["Access"].mean()
    change = avg_latest - avg_earliest
    st.metric("Change Over Period", f"{change:+.1f}%")
with col4:
    below_50 = (latest["Access"] < 50).sum()
    st.metric("Countries Below 50%", below_50)

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["Trends", "Comparison", "Map", "Data"])

with tab1:
    st.subheader("Average Access by Region Over Time")
    region_avg = filtered.groupby(["Year", "Region"])["Access"].mean().reset_index()
    fig1 = px.line(
        region_avg, x="Year", y="Access", color="Region",
        labels={"Access": "Access (%)", "Year": "Year"}
    )
    fig1.update_layout(height=450, legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Average Access by Income Group Over Time")
    income_avg = filtered.groupby(["Year", "IncomeGroup"])["Access"].mean().reset_index()
    fig2 = px.line(
        income_avg, x="Year", y="Access", color="IncomeGroup",
        labels={"Access": "Access (%)", "IncomeGroup": "Income Group"}
    )
    fig2.update_layout(height=450, legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader("Country Comparison")
    available_countries = sorted(filtered["Country Name"].unique())
    selected_countries = st.multiselect(
        "Select countries to compare",
        available_countries,
        default=available_countries[:5] if len(available_countries) >= 5 else available_countries
    )

    if selected_countries:
        country_data = filtered[filtered["Country Name"].isin(selected_countries)]
        fig3 = px.line(
            country_data, x="Year", y="Access", color="Country Name",
            labels={"Access": "Access (%)", "Country Name": "Country"}
        )
        fig3.update_layout(height=450, legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Distribution of Access in Selected Year")
    dist_year = st.selectbox("Select year", sorted(filtered["Year"].unique(), reverse=True))
    year_data = filtered[filtered["Year"] == dist_year]
    fig4 = px.histogram(
        year_data, x="Access", nbins=20, color="Region",
        labels={"Access": "Access (%)"},
        barmode="overlay", opacity=0.7
    )
    fig4.update_layout(height=400)
    st.plotly_chart(fig4, use_container_width=True)

with tab3:
    st.subheader("Global Map of Access")
    map_year = st.selectbox("Select year for map", sorted(filtered["Year"].unique(), reverse=True), key="map_year")
    map_data = filtered[filtered["Year"] == map_year]
    fig5 = px.choropleth(
        map_data,
        locations="Country Code",
        color="Access",
        hover_name="Country Name",
        color_continuous_scale="RdYlGn",
        range_color=[0, 100],
        labels={"Access": "Access (%)"}
    )
    fig5.update_layout(height=500, geo=dict(showframe=False, projection_type="natural earth"))
    st.plotly_chart(fig5, use_container_width=True)

    top_col, bottom_col = st.columns(2)
    with top_col:
        st.markdown("**Top 10**")
        top10 = map_data.nlargest(10, "Access")[["Country Name", "Access", "Region"]].reset_index(drop=True)
        top10.index = top10.index + 1
        top10["Access"] = top10["Access"].round(1)
        st.dataframe(top10, use_container_width=True)
    with bottom_col:
        st.markdown("**Bottom 10**")
        bottom10 = map_data.nsmallest(10, "Access")[["Country Name", "Access", "Region"]].reset_index(drop=True)
        bottom10.index = bottom10.index + 1
        bottom10["Access"] = bottom10["Access"].round(1)
        st.dataframe(bottom10, use_container_width=True)

with tab4:
    st.subheader("Filtered Data")
    display_data = filtered[["Country Name", "Country Code", "Region", "IncomeGroup", "Year", "Access"]].copy()
    display_data["Access"] = display_data["Access"].round(2)
    st.dataframe(display_data, use_container_width=True, height=500)
    st.download_button(
        "Download filtered data as CSV",
        display_data.to_csv(index=False),
        "filtered_data.csv",
        "text/csv"
    )
