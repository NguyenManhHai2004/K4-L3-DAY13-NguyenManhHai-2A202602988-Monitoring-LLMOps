from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st
import yaml
from collections import defaultdict


def load_logs(log_path: Path) -> list[dict]:
    logs = []
    if not log_path.exists():
        return logs
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            logs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return logs


def parse_timestamp(ts_str: str) -> datetime:
    if "Z" in ts_str:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    return datetime.fromisoformat(ts_str)


def filter_by_time_range(logs: list[dict], minutes: int) -> list[dict]:
    if not logs:
        return logs
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=minutes)
    return [log for log in logs if parse_timestamp(log.get("ts", "")) >= cutoff]


def calculate_percentiles(values: list[float]) -> dict[str, float]:
    if not values:
        return {"p50": 0, "p95": 0, "p99": 0}
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    return {
        "p50": sorted_vals[int(n * 0.50)],
        "p95": sorted_vals[int(n * 0.95)],
        "p99": sorted_vals[int(n * 0.99)],
    }


def render_dashboard():
    st.set_page_config(page_title="Day 13 Monitoring Dashboard", layout="wide")
    st.title("📊 Day 13 Monitoring & LLMOps Dashboard")

    config_path = Path("config/dashboard.yaml")
    config = yaml.safe_load(config_path.read_text())
    time_range = config["dashboard"]["time_range_minutes"]

    logs = load_logs(Path("data/logs.jsonl"))
    filtered_logs = filter_by_time_range(logs, time_range)

    if not filtered_logs:
        st.warning(f"No logs found in last {time_range} minutes")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Requests", sum(1 for l in filtered_logs if l.get("event") == "request_received"))
    with col2:
        errors = sum(1 for l in filtered_logs if l.get("event") == "request_failed")
        st.metric("Errors", errors)
    with col3:
        total_cost = sum(l.get("cost_usd", 0) for l in filtered_logs if l.get("event") == "response_sent")
        st.metric("Total Cost", f"${total_cost:.2f}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1️⃣ Latency Percentiles & TTFT")
        latencies = [l.get("latency_ms", 0) for l in filtered_logs if l.get("event") == "response_sent" and l.get("latency_ms")]
        ttfts = [l.get("ttft_ms", 0) for l in filtered_logs if l.get("event") == "response_sent" and l.get("ttft_ms")]

        lat_pct = calculate_percentiles(latencies)
        ttft_pct = calculate_percentiles(ttfts)

        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        with metric_col1:
            st.metric("P50 Latency", f"{lat_pct['p50']:.0f}ms")
        with metric_col2:
            st.metric("P95 Latency", f"{lat_pct['p95']:.0f}ms", delta="3000ms threshold")
        with metric_col3:
            st.metric("P99 Latency", f"{lat_pct['p99']:.0f}ms")
        with metric_col4:
            st.metric("TTFT P95", f"{ttft_pct['p95']:.0f}ms")

    with col2:
        st.subheader("2️⃣ Request Traffic")
        request_count = sum(1 for l in filtered_logs if l.get("event") == "request_received")
        rate_per_min = request_count / (time_range if time_range > 0 else 1)

        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric("Total Requests", request_count)
        with metric_col2:
            st.metric("Rate (req/min)", f"{rate_per_min:.1f}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("3️⃣ Error Rate & Retrieval Success")
        total_requests = sum(1 for l in filtered_logs if l.get("event") == "request_received")
        total_failures = sum(1 for l in filtered_logs if l.get("event") == "request_failed")
        error_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0

        tool_success = sum(1 for l in filtered_logs if l.get("tool_success") == True)
        tool_tracked = sum(1 for l in filtered_logs if l.get("tool_success") is not None)
        retrieval_success = (tool_success / tool_tracked * 100) if tool_tracked > 0 else 0

        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric("Error Rate", f"{error_rate:.1f}%", delta="2% threshold")
        with metric_col2:
            st.metric("Retrieval Success", f"{retrieval_success:.1f}%", delta="90% min")

    with col2:
        st.subheader("4️⃣ Cost Over Time")
        total_cost = sum(l.get("cost_usd", 0) for l in filtered_logs if l.get("event") == "response_sent")
        daily_cost = (total_cost / (time_range / 1440)) if time_range > 0 else 0

        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric("Total Cost", f"${total_cost:.3f}")
        with metric_col2:
            st.metric("Est. Daily Cost", f"${daily_cost:.2f}", delta="$2.50 max")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("5️⃣ Input/Output Tokens")
        total_in = sum(l.get("tokens_in", 0) for l in filtered_logs if l.get("event") == "response_sent")
        total_out = sum(l.get("tokens_out", 0) for l in filtered_logs if l.get("event") == "response_sent")
        total_tokens = total_in + total_out

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("Input Tokens", total_in)
        with metric_col2:
            st.metric("Output Tokens", total_out)
        with metric_col3:
            st.metric("Total Tokens", total_tokens, delta="50k threshold")

    with col2:
        st.subheader("6️⃣ Quality Proxy")
        quality_scores = [l.get("quality_score", 0) for l in filtered_logs if l.get("event") == "response_sent" and l.get("quality_score") is not None]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric("Avg Quality Score", f"{avg_quality:.2f}", delta="0.75 min")
        with metric_col2:
            st.metric("Quality Samples", len(quality_scores))

    st.markdown("---")
    st.caption(f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} | Time range: {time_range} minutes")


if __name__ == "__main__":
    render_dashboard()
