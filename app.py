# app.py
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

from core import Inputs, compute

st.set_page_config(page_title="CPK Live Simulator", layout="wide")

st.title("Live Cpk Measurement Error Simulator")


with st.sidebar:
    st.header("Inputs")

    mu = st.number_input("μ (Process mean)", value=0.0, step=0.1, format="%.4f")
    sigma_p = st.number_input("σp (Process std)", value=1.0, min_value=1e-9, step=0.1, format="%.4f")

    lsl = st.number_input("LSL", value=-3.0, step=0.5, format="%.4f")
    usl = st.number_input("USL", value=3.0, step=0.5, format="%.4f")

    cpk_threshold = st.number_input("Cpk acceptance threshold", value=1.33, min_value=1e-9, step=0.01, format="%.4f")
    n = st.number_input("n (Sample size)", value=30, min_value=2, step=1)
    bias = st.number_input("Bias b (measurement offset)", value=0.0, step=0.05, format="%.4f")

    destructive = st.checkbox("Destructive measurement / enter σm directly", value=False)

    if destructive:
        sigma_m_override = st.number_input("σm (Direct input)", value=0.5, min_value=0.0, step=0.05, format="%.4f")
        sigma_tool = 0.0
        sigma_operator = 0.0
    else:
        sigma_tool = st.number_input("σtool", value=0.3, min_value=0.0, step=0.05, format="%.4f")
        sigma_operator = st.number_input("σoperator", value=0.4, min_value=0.0, step=0.05, format="%.4f")
        sigma_m_override = None

    st.divider()
    st.caption("Tip: adjust σtool/σoperator and watch Cpk_meas change in real time.")

inp = Inputs(

    mu=mu,
    sigma_p=sigma_p,
    sigma_tool=sigma_tool,
    sigma_operator=sigma_operator,
    lsl=lsl,
    usl=usl,
    n=int(n),
    cpk_threshold=cpk_threshold,
    destructive=destructive,
    sigma_m_override=sigma_m_override

)

try:
    res = compute(inp)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Variance")
        st.metric("σm", f"{res.sigma_m:.4f}")
        st.metric("σtotal", f"{res.sigma_total:.4f}")

    with col2:
        st.subheader("Capability")
        st.metric("Cp (True)", f"{res.cp_true:.4f}")
        st.metric("Cp (Measured)", f"{res.cp_meas:.4f}")

    with col3:
        st.subheader("Cpk + Decision")
        st.metric("Cpk (True)", f"{res.cpk_true:.4f}")
        st.metric("Cpk (Measured)", f"{res.cpk_meas:.4f}")

        verdict = "PASS ✅" if res.pass_meas else "FAIL ❌"
        st.write(f"**Decision based on Cpk_meas:** {verdict}")

        if res.error_type == "α":
            st.warning("α: False rejection (true process meets the threshold, but measured Cpk fails).")
        elif res.error_type == "β":
            st.error("β: False acceptance (true process fails the threshold, but measured Cpk passes).")
        else:
            st.success("OK: No decision error relative to the true Cpk.")

    st.divider()

    # גרף 1: התפלגות True מול Measured
    st.subheader("Illustration: True (σp) vs Measured (σtotal) distributions")

    x = np.linspace(mu - 5*res.sigma_total, mu + 5*res.sigma_total, 400)
    true_pdf = (1/(sigma_p*np.sqrt(2*np.pi))) * np.exp(-0.5*((x-mu)/sigma_p)**2)
    meas_pdf = (1/(res.sigma_total*np.sqrt(2*np.pi))) * np.exp(-0.5*((x-mu)/res.sigma_total)**2)

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(x, true_pdf, label="True (σp)")
    ax.plot(x, meas_pdf, label="Measured (σtotal)")
    ax.axvline(lsl, linestyle="--")
    ax.axvline(usl, linestyle="--")
    ax.legend(fontsize=9)

    st.pyplot(fig, clear_figure=True)

    st.subheader("Sensitivity: Cpk_meas as a function of σm")

    sigma_m_grid = np.linspace(0, max(3.0*res.sigma_m, 1.0), 60)
    cpk_meas_grid = []
    for sm in sigma_m_grid:
        tmp = Inputs(**{**inp.__dict__, "sigma_m_override": sm, "sigma_tool": 0.0, "sigma_operator": 0.0})
        tmp_res = compute(tmp)
        cpk_meas_grid.append(tmp_res.cpk_meas)

    fig2, ax2 = plt.subplots(figsize=(6, 2.5))
    ax2.plot(sigma_m_grid, cpk_meas_grid)
    ax2.axhline(cpk_threshold, linestyle="--")
    ax2.set_xlabel("σm", fontsize=9)
    ax2.set_ylabel("Cpk_meas", fontsize=9)

    st.pyplot(fig2, clear_figure=True)

except Exception as e:
    st.error(f"Input/calculation error: {e}")
