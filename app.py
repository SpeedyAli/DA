import streamlit as st 
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from io import BytesIO, StringIO
import base64

st.set_page_config(page_title="Gas Temperature Comparison & Analytics", layout="wide")
st.title("Gas Temperature Data Analytics & Comparison Tool")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if not uploaded_file:
 st.markdown("""  
---

### 📄 What This Tool Does  
This tool calculates and compares **gas condensate dew point temperatures** using 4 published equations.  
It helps identify which formula gives the most accurate results by comparing with your experimental data.

---

### 📅 What You Need to Upload (Excel File)

Your Excel file **must have these columns**:

- **Pressure**: in **kPa**  
- **Molecular_Weight**: used to calculate Gas Gravity (γ)  
- **Experimental_Temperature**: in **Kelvin (K)**

✅ Column names should be exactly like above (case-sensitive).  
✅ File should be in `.xlsx` format and on the **first sheet**.

---

### 📊 What You'll Get:

- Temperatures calculated by:
  - Safamirzaei (uses kPa)
  - Motiee (°C → K)
  - Towler & Mokhatab (°F → K)
  - Ghayyem (°F → K)
- A **graph** showing all calculated vs experimental temperatures  
- **Error metrics** like MAPE, MIPE, ARD, and Relative Error  
- Option to download:
  - The graph (PNG, HTML)
  - The error table (CSV)

---

### ⚙️ Behind The Scenes:

- Converts pressure from **kPa → psi** for equations that require it  
- Converts temperature outputs to **Kelvin** for fair comparison  
- Automatically calculates Gas Gravity:
  \[
  γ_g = Molecular Weight / 28.97
  \]

---

🌟 This is a **minor project tool** designed for engineers, students, or researchers working with gas condensate systems and needing temperature estimations under different models.

""", unsafe_allow_html=True)

if uploaded_file:
    data = pd.read_excel(uploaded_file)
    st.subheader("Raw Data")
    edited_data = st.data_editor(data, use_container_width=True)

    st.sidebar.header("Constants for Safamirzaei Equation")
    A = st.sidebar.number_input("A", value=194.681789)
    B = st.sidebar.number_input("B", value=0.044232)
    C = st.sidebar.number_input("C", value=0.189829)

    st.sidebar.header("Select Columns")
    pressure_col = st.sidebar.selectbox("Pressure Column (in kPa)", edited_data.columns, index=edited_data.columns.get_loc("Pressure") if "Pressure" in edited_data.columns else 0)
    gamma_col = st.sidebar.selectbox("Molecular Weight Column", edited_data.columns, index=edited_data.columns.get_loc("Molecular_Weight") if "Molecular_Weight" in edited_data.columns else 0)
    experimental_col = st.sidebar.selectbox("Experimental Temperature Column (in Kelvin)", edited_data.columns, index=edited_data.columns.get_loc("Experimental_Temperature") if "Experimental_Temperature" in edited_data.columns else 0)

    # Convert MW to Gas Gravity
    edited_data['Gamma'] = edited_data[gamma_col] / 28.97
    gamma = edited_data['Gamma']
    P_kPa = edited_data[pressure_col]
    P_psi = P_kPa / 6.89476

    # Equations
    edited_data['T_Safamirzaei'] = A * (gamma ** B) * (np.log(P_kPa) ** C)
    T_motiee_C = (-283.24469 + 78.99667 * np.log10(P_psi) - 5.352544 * (np.log10(P_psi) ** 2) + 349.473877 * gamma - 150.854675 * gamma ** 2 - 27.604065 * gamma * np.log10(P_psi))
    edited_data['T_Motiee'] = T_motiee_C + 273.15
    T_towler_F = (13.47 * np.log(P_psi) + 34.27 * np.log(gamma) - 1.675 * (np.log(P_psi) * np.log(gamma)) - 20.35)
    edited_data['T_Towler'] = (T_towler_F - 32) * 5 / 9 + 273.15
    lnP = np.log(P_psi)
    T_ghayyem_F = (-26.115 - 23.728 / gamma + 23.942 * lnP - 0.738 * np.exp(gamma ** -2.3) - 1.135 * (lnP ** 2) + 0.443 * lnP * np.exp(gamma ** -1.7))
    edited_data['T_Ghayyem'] = (T_ghayyem_F - 32) * 5 / 9 + 273.15

    exp_T = edited_data[experimental_col]

    def calc_errors(pred):
        rel_error = np.mean(np.abs((exp_T - pred) / exp_T)) * 100
        mape = np.max(np.abs((exp_T - pred) / exp_T)) * 100
        mipe = np.min(np.abs((exp_T - pred) / exp_T)) * 100
        ard = np.mean(np.abs((exp_T - pred) / exp_T)) * 100
        return mape, mipe, ard, rel_error

    errors = {col: calc_errors(edited_data[col]) for col in ['T_Safamirzaei', 'T_Motiee', 'T_Towler', 'T_Ghayyem']}
    st.sidebar.subheader("Error Metrics (%)")
    error_df = pd.DataFrame(errors, index=["MAPE", "MIPE", "ARD", "Relative Error"]).T
    st.sidebar.dataframe(error_df.style.format("{:.2f}"))
    st.sidebar.download_button("Download Error Metrics CSV", error_df.to_csv().encode(), "error_metrics.csv", "text/csv")

    st.subheader("Processed Data")
    st.dataframe(edited_data, use_container_width=True)

    # Graph Type
    graph_type = st.radio("Graph Style", ["lines", "markers", "lines+markers"], index=2, horizontal=True)

    # Main Comparison Graph
    with st.expander("Main Comparison Graph"):
        fig = go.Figure()
        method_names = {
            "T_Safamirzaei": "Safamirzaei",
            "T_Motiee": "Motiee",
            "T_Towler": "Towler & Mokhatab",
            "T_Ghayyem": "Ghayyem"
        }
        for method, label in method_names.items():
            fig.add_trace(go.Scatter(
                x=edited_data[pressure_col],
                y=edited_data[method],
                mode=graph_type,
                name=label,
                text=[f"γ: {g:.4f}" for g in edited_data['Gamma']],
                hovertemplate="Pressure: %{x}<br>Temperature: %{y}<br>%{text}<extra></extra>"
            ))

        fig.add_trace(go.Scatter(
            x=edited_data[pressure_col],
            y=edited_data[experimental_col],
            mode='markers',
            name='Experimental',
            marker=dict(color='black', symbol='x')
        ))

        fig.update_layout(xaxis_title="Pressure (kPa)", yaxis_title="Temperature (K)", height=600)
        st.plotly_chart(fig, use_container_width=True)

    # Per-Gamma Graphs
    with st.expander("Individual Graphs for Each Gas Gravity"):
        for g_val in sorted(edited_data['Gamma'].unique()):
            st.markdown(f"### γ = {g_val:.4f}")
            subset = edited_data[edited_data['Gamma'] == g_val]
            fig_individual = go.Figure()
            for method, label in method_names.items():
                fig_individual.add_trace(go.Scatter(
                    x=subset[pressure_col],
                    y=subset[method],
                    mode=graph_type,
                    name=label
                ))
            fig_individual.add_trace(go.Scatter(
                x=subset[pressure_col],
                y=subset[experimental_col],
                mode='markers',
                name='Experimental',
                marker=dict(color='black', symbol='x')
            ))
            fig_individual.update_layout(xaxis_title="Pressure (kPa)", yaxis_title="Temperature (K)", height=500)
            st.plotly_chart(fig_individual, use_container_width=True)

    st.subheader("Download Main Graph")
    html_buf = StringIO()
    fig.write_html(html_buf, include_plotlyjs='cdn')
    st.download_button("Download Graph as HTML", data=html_buf.getvalue(), file_name="comparison_graph.html", mime="text/html")

    st.subheader("Calculation Details & Units")
    st.markdown(r"""
    - **Pressure Input Unit**: Input is in **kPa**, internally converted to **psi** where needed.
    - **Temperature Output Unit**: All results are shown in **Kelvin (K)**.
    - **Gas Gravity**: Calculated from Molecular Weight as:
    \[\gamma_g = Molecular Weight / 28.97\]

    ---

    ### Equations Used

    #### 1. Safamirzaei:
    \[T_(K) = A * \gamma^B * (ln P_(kPa))^C\]

    #### 2. Motiee (converted from °C):
    \[T = -283.24469 + 78.99667 log P - 5.352544 (log P)^2 + 349.473877 \gamma_g - 150.854675 \gamma_g^2 - 27.604065 \gamma_g log P\]

    #### 3. Towler & Mokhatab (converted from °F):
    \[T = 13.47 ln P + 34.27 ln \gamma_g - 1.675 (ln P)(ln \gamma_g) - 20.35\]

    #### 4. Ghayyem (converted from °F):
    \[T = -26.115 - 23.728/\gamma_g + 23.942 ln(P) - 0.738 exp(\gamma_g^{-2.3}) - 1.135(ln(P))^2 + 0.443(ln(P))exp(\gamma_g^{-1.7})\]
    """, unsafe_allow_html=True)
