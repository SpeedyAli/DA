
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Gas Temperature Data Analytics", layout="wide")

st.title("Gas Temperature Data Analytics Platform")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    data = pd.read_excel(uploaded_file)
    st.subheader("Raw Data")
    edited_data = st.data_editor(data, use_container_width=True)

    # Custom Constants
    st.sidebar.header("Enter Constants for Safamirzaei Equation")
    A = st.sidebar.number_input("A", value=194.681789)
    B = st.sidebar.number_input("B", value=0.044232)
    C = st.sidebar.number_input("C", value=0.189829)

    # Select Columns
    st.sidebar.header("Select Columns")
    pressure_col = st.sidebar.selectbox("Pressure Column", edited_data.columns)
    gamma_col = st.sidebar.selectbox("Gas Gravity or Molecular Weight Column", edited_data.columns)
    experimental_col = st.sidebar.selectbox("Experimental Temperature Column (Optional)", ["None"] + list(edited_data.columns))

    def calculate_temperature(P, gamma):
        return A * (gamma ** B) * (np.log(P) ** C)

    # Convert Molecular Weight to Gas Gravity if required
    if st.sidebar.checkbox("Convert Molecular Weight to Gas Gravity (MW/28.97)?"):
        edited_data['Gamma'] = edited_data[gamma_col] / 28.97
    else:
        edited_data['Gamma'] = edited_data[gamma_col]

    edited_data['Calculated_Temperature'] = calculate_temperature(edited_data[pressure_col], edited_data['Gamma'])

    # Difference Column
    if experimental_col != "None":
        edited_data['Difference'] = abs(edited_data['Calculated_Temperature'] - edited_data[experimental_col])

    st.subheader("Processed Data")
    st.dataframe(edited_data, use_container_width=True)

    # Interactive Plotly Graph
    st.subheader("Interactive Graph")
    fig = px.line(
        edited_data,
        x=pressure_col,
        y='Calculated_Temperature',
        color=edited_data['Gamma'].astype(str),
        markers=True,
        labels={'Gamma': 'Gas Gravity'}
    )
    if experimental_col != "None":
        fig.add_scatter(x=edited_data[pressure_col], y=edited_data[experimental_col], mode='markers', name='Experimental', marker=dict(color='black', symbol='x'))

    st.plotly_chart(fig, use_container_width=True)

    # Download Plot as PNG
    st.subheader("Export Graph as Image")
    fig_bytes = fig.to_image(format="png")
    st.download_button("Download Graph", data=fig_bytes, file_name="interactive_graph.png", mime="image/png")
