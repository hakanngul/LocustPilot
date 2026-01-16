
import json
import pandas as pd
import streamlit as st
from locust_app.core.data import list_runs, load_stats_cached, run_signature

def render_dashboard_tab():
    st.subheader("📊 Global Dashboard")
    st.markdown("""
    This dashboard provides collective analysis of all load tests.
    You can compare different hosts and test files, view performance trends.
    """)

    def _first_col(df: pd.DataFrame, candidates: list[str]):
        for c in candidates:
            if c in df.columns:
                return c
        return None

    def _try_number(val, default=None):
        try:
            if pd.isna(val):
                return default
            return float(val)
        except Exception:
            return default

    # Collect run summaries
    summaries = []
    for r in list_runs():
        meta = {}
        mp = r / "metadata.json"
        if mp.exists():
            try:
                meta = json.loads(mp.read_text(encoding="utf-8"))
            except Exception:
                meta = {}
        data = load_stats_cached(str(r), "stats", run_signature(r))
        agg = None
        if "stats" in data and not data["stats"].empty:
            sdf = data["stats"]
            name_col = _first_col(sdf, ["Name", "name"]) or "Name"
            agg_rows = (
                sdf[sdf[name_col].astype(str).str.lower() == "aggregated"]
                if name_col in sdf.columns
                else pd.DataFrame()
            )
            if not agg_rows.empty:
                agg = agg_rows.iloc[0]

        if agg is None:
            continue

        # Extract values with multiple possible column names
        req_count = _try_number(agg.get("Request Count", agg.get("Requests", 0)), 0)
        fail_count = _try_number(
            agg.get("Failure Count", agg.get("Failures", 0)), 0
        )
        median = _try_number(
            agg.get("50%ile", agg.get("Median Response Time", agg.get("50%", None)))
        )
        p95 = _try_number(agg.get("95%ile", agg.get("95%", None)))

        # Average RPS from history if available
        avg_rps = None
        if "history" in data and not data["history"].empty:
            hdf = data["history"]
            rps_col = _first_col(hdf, ["Requests/s", "RPS", "requests/s"])
            if rps_col:
                try:
                    avg_rps = float(hdf[rps_col].astype(float).mean())
                except Exception:
                    avg_rps = None

        summaries.append(
            {
                "run_id": r.name,
                "path": str(r),
                "locustfile": meta.get("locustfile"),
                "host": meta.get("effective_host")
                or meta.get("typed_host")
                or meta.get("file_host"),
                "started_at": meta.get("started_at"),
                "ended_at": meta.get("ended_at"),
                "users": meta.get("users"),
                "spawn_rate": meta.get("spawn_rate"),
                "run_time": meta.get("run_time"),
                "requests": req_count,
                "failures": fail_count,
                "success_rate": (1 - fail_count / req_count) * 100
                if req_count and req_count > 0
                else None,
                "median_ms": median,
                "p95_ms": p95,
                "avg_rps": avg_rps,
            }
        )

    if not summaries:
        st.info(
            "📭 Henüz metadata'lı bir çalışma bulunamadı. 'Test Çalıştır' sekmesinden yeni bir test başlatın."
        )
    else:
        df = pd.DataFrame(summaries)

        # Filters with help text
        st.markdown("### 🔍 Filters")
        c1, c2, c3 = st.columns([2, 2, 2])
        with c1:
            locust_opts = sorted(
                [x for x in df["locustfile"].dropna().unique().tolist()]
            )
            sel_locust = st.multiselect(
                "Test File",
                options=locust_opts,
                default=locust_opts,
                help="Which locustfile results do you want to see?",
            )
        with c2:
            host_opts = sorted([x for x in df["host"].dropna().unique().tolist()])
            sel_host = st.multiselect(
                "Target Server",
                options=host_opts,
                default=host_opts,
                help="Which server tests do you want to see?",
            )
        with c3:
            group_by = st.selectbox(
                "Grouping Criteria",
                options=["Host", "Locustfile", "Host+Locustfile"],
                index=0,
                help="How do you want to group the results?",
            )

        fdf = df.copy()
        if sel_locust:
            fdf = fdf[fdf["locustfile"].isin(sel_locust)]
        if sel_host:
            fdf = fdf[fdf["host"].isin(sel_host)]

        if fdf.empty:
            st.warning("⚠️ No runs match selected filters.")
        else:
            # Summary KPIs with explanations
            st.markdown("### 📈 Summary Metrics")
            total_runs = len(fdf)
            total_req = float(fdf["requests"].fillna(0).sum())
            total_fail = float(fdf["failures"].fillna(0).sum())
            overall_success = (
                (1 - total_fail / total_req) * 100 if total_req > 0 else None
            )

            # Weighted p95 by requests as an approximation
            def weighted_avg(series, weights):
                try:
                    s = series.astype(float)
                    w = weights.astype(float)
                    if w.sum() == 0:
                        return None
                    return float((s * w).sum() / w.sum())
                except Exception:
                    return None

            weighted_p95 = weighted_avg(
                fdf["p95_ms"].fillna(0), fdf["requests"].fillna(0)
            )

            k = st.columns(4)
            k[0].metric(
                "🔄 Test Count",
                str(total_runs),
                help="Total number of test runs matching selected filters",
            )
            k[1].metric(
                "📤 Total Requests",
                f"{int(total_req):,}".replace(",", "."),
                help="Total number of HTTP requests across all tests",
            )
            k[2].metric(
                "✅ Success Rate",
                f"{overall_success:.1f}%" if overall_success is not None else "-",
                delta=f"{int(total_fail)} failures" if total_fail > 0 else None,
                delta_color="inverse",
                help="Percentage of error-free completed requests (Target: %99+)",
            )
            k[3].metric(
                "⏱️ Avg p95 Latency",
                f"{weighted_p95:.0f} ms" if weighted_p95 is not None else "-",
                help="Response time at which 95% of requests are faster (lower is better)",
            )

            # Grouping
            if group_by == "Host":
                gkey = ["host"]
            elif group_by == "Locustfile":
                gkey = ["locustfile"]
            else:
                gkey = ["host", "locustfile"]

            g = (
                fdf.groupby(gkey)
                .agg(
                    requests=("requests", "sum"),
                    failures=("failures", "sum"),
                    avg_p95=("p95_ms", "mean"),
                    avg_median=("median_ms", "mean"),
                    avg_rps=("avg_rps", "mean"),
                    runs=("run_id", "count"),
                )
                .reset_index()
            )
            g["success_rate_%"] = (1 - g["failures"] / g["requests"]) * 100

            st.divider()
            st.markdown("### 📋 Grouped Results")
            st.caption(
                "Each row shows combined test results based on selected grouping criteria."
            )

            # Rename columns for better readability
            display_g = g.rename(
                columns={
                    "host": "Server",
                    "locustfile": "Test File",
                    "requests": "Total Requests",
                    "failures": "Failures",
                    "avg_p95": "Avg p95 (ms)",
                    "avg_median": "Avg Median (ms)",
                    "avg_rps": "Avg RPS",
                    "runs": "Test Count",
                    "success_rate_%": "Success %",
                }
            )
            st.dataframe(display_g, use_container_width=True)

            st.divider()
            st.markdown("### 📊 Visual Comparison")

            c1, c2 = st.columns(2)
            with c1:
                try:
                    import plotly.graph_objects as go

                    x_col = "host" if "host" in g.columns else "locustfile"
                    g_sorted = g.sort_values("avg_p95", ascending=True)

                    # Color based on success rate
                    colors = [
                        "#27ae60"
                        if sr >= 99
                        else "#f39c12"
                        if sr >= 95
                        else "#e74c3c"
                        for sr in g_sorted["success_rate_%"]
                    ]

                    fig = go.Figure()
                    fig.add_trace(
                        go.Bar(
                            x=g_sorted[x_col],
                            y=g_sorted["avg_p95"],
                            marker_color=colors,
                            text=[f"{v:.0f}ms" for v in g_sorted["avg_p95"]],
                            textposition="outside",
                            hovertemplate="<b>%{x}</b><br>p95: %{y:.0f}ms<br>Success: %{customdata:.1f}%<extra></extra>",
                            customdata=g_sorted["success_rate_%"],
                        )
                    )
                    fig.update_layout(
                        title="🏎️ Response Time Comparison (p95)",
                        yaxis_title="Average p95 (ms)",
                        xaxis_title="",
                        height=400,
                        showlegend=False,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption(
                        "🟢 Green: %99+ success | 🟡 Yellow: %95-99 | 🔴 Red: <%95"
                    )
                except Exception:
                    pass

            with c2:
                try:
                    import plotly.graph_objects as go

                    x_col = "host" if "host" in g.columns else "locustfile"
                    g_sorted = g.sort_values("requests", ascending=True)

                    fig2 = go.Figure()

                    # Stacked bar: successes and failures
                    successes = g_sorted["requests"] - g_sorted["failures"]

                    fig2.add_trace(
                        go.Bar(
                            x=g_sorted[x_col],
                            y=successes,
                            name="Successful",
                            marker_color="#27ae60",
                        )
                    )
                    fig2.add_trace(
                        go.Bar(
                            x=g_sorted[x_col],
                            y=g_sorted["failures"],
                            name="Failed",
                            marker_color="#e74c3c",
                        )
                    )

                    fig2.update_layout(
                        title="📊 Request Distribution",
                        yaxis_title="Request Count",
                        xaxis_title="",
                        height=400,
                        barmode="stack",
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1,
                        ),
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                except Exception:
                    pass
