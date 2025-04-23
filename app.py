import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(page_title="Gas Temperature Data Analytics", layout="wide")

st.title("Gas Temperature Data Analytics Platform")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    data = pd.read_excel(uploaded_file)

    st.subheader("Raw Data")
    edited_data = st.data_editor(data, use_container_width=True)

    st.sidebar.header("Enter Constants for Safamirzaei Equation")
    A = st.sidebar.number_input("A", value=194.681789)
    B = st.sidebar.number_input("B", value=0.044232)
    C = st.sidebar.number_input("C", value=0.189829)

    st.sidebar.header("Select Columns")

    # Column defaults
    default_pressure_col = 'Pressure' if 'Pressure' in edited_data.columns else edited_data.columns[0]
    default_gamma_col = 'Molecular_Weight' if 'Molecular_Weight' in edited_data.columns else edited_data.columns[0]
    default_exp_col = 'Experimental_Temperature' if 'Experimental_Temperature' in edited_data.columns else "None"

    pressure_col = st.sidebar.selectbox("Pressure Column", edited_data.columns, index=edited_data.columns.get_loc(default_pressure_col))
    gamma_col = st.sidebar.selectbox("Gas Gravity or Molecular Weight Column", edited_data.columns, index=edited_data.columns.get_loc(default_gamma_col))
    experimental_col = st.sidebar.selectbox("Experimental Temperature Column (Optional)", ["None"] + list(edited_data.columns), index=(["None"] + list(edited_data.columns)).index(default_exp_col))

    def calculate_temperature(P, gamma):
        return A * (gamma ** B) * (np.log(P) ** C)

    # Always convert MW to Gamma if column is MW
    convert_to_gamma = gamma_col.lower().strip() in ["molecular_weight", "mw"]
    if convert_to_gamma:
        edited_data['Gamma'] = edited_data[gamma_col] / 28.97
    else:
        edited_data['Gamma'] = edited_data[gamma_col]

    edited_data['Calculated_Temperature'] = calculate_temperature(edited_data[pressure_col], edited_data['Gamma'])

    if experimental_col != "None":
        edited_data['Difference'] = abs(edited_data['Calculated_Temperature'] - edited_data[experimental_col])

    st.subheader("Processed Data")
    st.dataframe(edited_data, use_container_width=True)

    st.subheader("Graphs")

    fig = go.Figure()

    for gamma_value in edited_data['Gamma'].unique():
        subset = edited_data[edited_data['Gamma'] == gamma_value]
        fig.add_trace(go.Scatter(
            x=subset[pressure_col],
            y=subset['Calculated_Temperature'],
            mode='lines+markers',
            name=f'Gamma: {round(gamma_value, 3)}'
        ))

    if experimental_col != "None":
        fig.add_trace(go.Scatter(
            x=edited_data[pressure_col],
            y=edited_data[experimental_col],
            mode='markers',
            name='Experimental',
            marker=dict(color='black', symbol='x')
        ))

    fig.update_layout(
        xaxis_title='Pressure',
        yaxis_title='Temperature',
        legend_title='Legend',
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Heatmap (Difference Detection)")
    if experimental_col != "None":
        heatmap_data = edited_data.pivot_table(index='Gamma', columns=pressure_col, values='Difference')
        heatmap_fig = px.imshow(heatmap_data, text_auto=True, color_continuous_scale='RdBu', aspect='auto')
        st.plotly_chart(heatmap_fig, use_container_width=True)

    st.subheader("Export Graph as Image")
    buf = BytesIO()
    fig.write_image(buf, format="png")
    st.download_button("Download Main Graph", data=buf.getvalue(), file_name="graph.png", mime="image/png")
