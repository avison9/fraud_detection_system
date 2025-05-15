import streamlit as st
import asyncio
import websockets
import json
import pandas as pd
import redis
import plotly.express as px
from collections import deque
import threading
import time
import queue


st.set_page_config(page_title="Fraud Detection Dashboard", layout="wide")
st.title("Real-Time Fraud Detection Dashboard")

redis_client = redis.Redis(host="redis", port=6379, db=0)


MAX_TX = 500
live_data_queue = queue.Queue()
live_data_buffer = deque(maxlen=MAX_TX)


if "tx_limit" not in st.session_state:
    st.session_state["tx_limit"] = 100
if "ws_started" not in st.session_state:
    st.session_state["ws_started"] = False


st.sidebar.header("Display Settings")
st.session_state["tx_limit"] = st.sidebar.selectbox(
    "Show last N transactions",
    options=[10, 50, 100, 500],
    index=[10, 50, 100, 500].index(st.session_state["tx_limit"])
)

st.sidebar.header("Filters")
fraud_only = st.sidebar.checkbox("Show Only Fraudulent", value=False)
min_amount = st.sidebar.slider("Minimum Amount", 0, 100000, 100)
account_id_filter = st.sidebar.text_input("Filter by Account ID")

def get_cached_transactions(limit):
    raw = redis_client.lrange("tx_cache", 0, limit - 1)
    return [json.loads(r) for r in raw]


def websocket_listener():
    async def listen():
        uri = "ws://fastapi:8000/ws"
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    await websocket.send("ping")
                    while True:
                        msg = await websocket.recv()
                        try:
                            data = json.loads(msg)
                            live_data_queue.put(data)
                        except json.JSONDecodeError as e:
                            print(f"Invalid message: {msg} — {e}")
            except Exception as e:
                print(f"[WebSocket Error] {e}")
                time.sleep(5)  

    asyncio.run(listen())

# Start listener once
if not st.session_state["ws_started"]:
    threading.Thread(target=websocket_listener, daemon=True).start()
    st.session_state["ws_started"] = True

while not live_data_queue.empty():
    try:
        tx = live_data_queue.get_nowait()
        live_data_buffer.append(tx)
    except queue.Empty:
        break


data_source = (
    list(live_data_buffer)[-st.session_state["tx_limit"]:]
    if live_data_buffer else get_cached_transactions(st.session_state["tx_limit"])
)


filtered = []
for tx in data_source:
    if fraud_only and not tx.get("is_fraud", False):
        continue
    if tx.get("amount", 0) < min_amount:
        continue
    if account_id_filter and tx.get("account_id") != account_id_filter:
        continue
    filtered.append(tx)


df = pd.DataFrame(filtered)
st.write(f"{len(df)} Transactions loaded")

if not df.empty:
    st.subheader("Transactions Table")
    st.dataframe(df, use_container_width=True)

    st.subheader("Fraudulent Transaction Count")
    fraud_count = df["is_fraud"].sum()
    st.metric("Fraudulent Tx Count", fraud_count)

    st.subheader("Histogram by Timestamp")
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        fig = px.histogram(df, x="timestamp", color="is_fraud", nbins=20)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No transactions match the selected filters.")

