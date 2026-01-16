
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def render_summary_from_stats(stats_df: pd.DataFrame):
    # Locust stats CSV has an "Aggregated" row with overall metrics
    agg = None
    if "Name" in stats_df.columns:
        agg_rows = stats_df[stats_df["Name"].astype(str).str.lower() == "aggregated"]
        if not agg_rows.empty:
            agg = agg_rows.iloc[0]

    cols = st.columns(4)
    if agg is not None:
        cols[0].metric("Requests", f"{int(agg.get('Request Count', 0))}")
        cols[1].metric("Failures", f"{int(agg.get('Failure Count', 0))}")
        cols[2].metric(
            "Median (ms)",
            f"{int(agg.get('50%ile', agg.get('Median Response Time', 0)))}",
        )
        p95 = agg.get("95%ile", agg.get("95%", None))
        if pd.notna(p95):
            cols[3].metric("p95 (ms)", f"{int(p95)}")
    else:
        cols[0].metric("Requests", "-")
        cols[1].metric("Failures", "-")
        cols[2].metric("Median (ms)", "-")
        cols[3].metric("p95 (ms)", "-")


def render_time_series(history_df: pd.DataFrame):
    """Render improved, readable time series charts."""
    if history_df is None or history_df.empty:
        st.info("Zaman serisi verisi bulunamadı.")
        return

    df = history_df.copy()

    # Normalize timestamp
    ts_col = None
    for c in ["Timestamp", "Time", "timestamp", "time"]:
        if c in df.columns:
            ts_col = c
            break
    if ts_col is None:
        st.info("Zaman sütunu bulunamadı.")
        return
    df[ts_col] = pd.to_datetime(df[ts_col])

    # Calculate elapsed time in seconds for better readability
    df["Süre (saniye)"] = (df[ts_col] - df[ts_col].min()).dt.total_seconds()

    # ===== CHART 1: RPS & Users (dual axis effect with area) =====
    st.markdown("### 📈 Request Rate and User Count")

    rps_col = None
    for c in ["Requests/s", "RPS", "requests/s"]:
        if c in df.columns:
            rps_col = c
            break

    users_col = None
    for c in ["Users", "User Count", "users"]:
        if c in df.columns:
            users_col = c
            break

    if rps_col or users_col:
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])

        if rps_col and rps_col in df.columns:
            fig1.add_trace(
                go.Scatter(
                    x=df["Süre (saniye)"],
                    y=df[rps_col],
                    name="Requests/second",
                    line=dict(color="#2ecc71", width=2),
                    fill="tozeroy",
                    fillcolor="rgba(46, 204, 113, 0.1)",
                ),
                secondary_y=False,
            )

        if users_col and users_col in df.columns:
            fig1.add_trace(
                go.Scatter(
                    x=df["Süre (saniye)"],
                    y=df[users_col],
                    name="Active Users",
                    line=dict(color="#3498db", width=2, dash="dot"),
                ),
                secondary_y=True,
            )

        # Add failures if exists
        fail_col = None
        for c in ["Fails/s", "Failures/s"]:
            if c in df.columns:
                fail_col = c
                break

        if fail_col and df[fail_col].sum() > 0:
            fig1.add_trace(
                go.Scatter(
                    x=df["Süre (saniye)"],
                    y=df[fail_col],
                    name="Failures/second",
                    line=dict(color="#e74c3c", width=2),
                    fill="tozeroy",
                    fillcolor="rgba(231, 76, 60, 0.2)",
                ),
                secondary_y=False,
            )

        fig1.update_layout(
            height=400,
            hovermode="x unified",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            margin=dict(l=20, r=20, t=40, b=20),
        )
        fig1.update_xaxes(title_text="Time (seconds)", gridcolor="rgba(128,128,128,0.2)")
        fig1.update_yaxes(
            title_text="Requests/second",
            secondary_y=False,
            gridcolor="rgba(128,128,128,0.2)",
        )
        fig1.update_yaxes(title_text="User Count", secondary_y=True)

        st.plotly_chart(fig1, use_container_width=True)

    # ===== CHART 2: Response Times =====
    st.markdown("### ⏱️ Response Times (Latency)")

    # Map column names to Turkish labels
    latency_mapping = {
        "50%": "Medyan (p50)",
        "95%": "p95",
        "99%": "p99",
        "99.9%": "p99.9",
        "Median Response Time": "Medyan",
        "95%ile": "p95",
        "Average Response Time": "Ortalama",
    }

    p_cols = [c for c in latency_mapping.keys() if c in df.columns]

    if p_cols:
        fig2 = go.Figure()

        colors = {
            "50%": "#27ae60",
            "Median Response Time": "#27ae60",
            "Medyan": "#27ae60",
            "95%": "#f39c12",
            "95%ile": "#f39c12",
            "99%": "#e67e22",
            "99.9%": "#e74c3c",
            "Average Response Time": "#3498db",
        }

        for col in p_cols:
            label = latency_mapping.get(col, col)
            color = colors.get(col, "#95a5a6")
            fig2.add_trace(
                go.Scatter(
                    x=df["Süre (saniye)"],
                    y=df[col],
                    name=label,
                    line=dict(color=color, width=2),
                    mode="lines",
                )
            )

        fig2.update_layout(
            height=350,
            hovermode="x unified",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            margin=dict(l=20, r=20, t=40, b=20),
            yaxis_title="Yanıt Süresi (ms)",
        )
        fig2.update_xaxes(title_text="Süre (saniye)", gridcolor="rgba(128,128,128,0.2)")
        fig2.update_yaxes(gridcolor="rgba(128,128,128,0.2)")

        st.plotly_chart(fig2, use_container_width=True)

        st.caption(
            "💡 **p50 (Median):** Half of the requests are faster than this | **p95:** 95% of requests are faster than this | **p99:** Slowest 1% of requests"
        )
