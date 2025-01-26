import streamlit as st
from utils import plot_map, ec_con_lines, ConsumptionModel

# Streamlit app layout
st.set_page_config(layout="wide")

def initialize_session_state():
    if "selected_region" not in st.session_state:
        st.session_state["selected_region"] = 'Central Europe'
    if "selected_commodity" not in st.session_state:
        st.session_state["selected_commodity"] = 'apples'
    if "selected_years" not in st.session_state:
        st.session_state["selected_years"] = (2018, 2021)
    if "model" not in st.session_state:
        st.session_state["model"] = ConsumptionModel(
            st.session_state["selected_commodity"], st.session_state["selected_years"]
        )

initialize_session_state()

# Title
st.markdown("<h2 style='text-align: center; font-size:36px'>EU-27 Food Consumption</h2>", unsafe_allow_html=True)

# Three-column layout
left_column, middle_column, right_column = st.columns([1, 1.2, 1.2])

# Left Column: Filter settings and map
with left_column:
    st.markdown("##### Filter Settings")
    years = st.slider("Select years", 2014, 2023, st.session_state["selected_years"], 1)
    regions_list = ['Central Europe', 'South Eastern Europe', 'Northern Europe', 'Southern Europe', 'Western Europe']
    region = st.selectbox("Select region", regions_list, index=regions_list.index(st.session_state["selected_region"]))
    commodities_list = ['apples', 'barley', 'oats', 'soy', 'sunflower', 'wine', 'butter', 'milk']
    commodity = st.selectbox("Select commodity", commodities_list, index=commodities_list.index(st.session_state["selected_commodity"]))

    # Update session state with the selected filters
    st.session_state["selected_years"] = years
    st.session_state["selected_region"] = region
    st.session_state["selected_commodity"] = commodity
    st.session_state["model"] = ConsumptionModel(commodity, years)

    # Map visualization
    st.markdown(f"##### Consumption of {commodity.capitalize()} in {years[1]}")
    fig_map = plot_map(years, commodity)
    st.plotly_chart(fig_map)

# Middle Column: Economic Indicators and Consumption Trends
with middle_column:
    st.markdown(f"##### Economic Indicators and Consumption for {region}")
    fig_ec_con = ec_con_lines(region, years, commodity)
    st.plotly_chart(fig_ec_con, use_container_width=True)

# Right Column: Predictive Model Insights
with right_column:
    st.markdown(f"##### Linear Model for {commodity.capitalize()}")
    scatter_fig = st.session_state["model"].plot_scatter()
    st.plotly_chart(scatter_fig, use_container_width=True)
    st.markdown("##### Model Coefficients")
    coeff_fig = st.session_state["model"].plot_coefficients()
    st.plotly_chart(coeff_fig, use_container_width=True)