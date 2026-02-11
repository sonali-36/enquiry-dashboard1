import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Lean System Conversion Dashboard",
    layout="wide"
)

st.title("📊 Lean System Conversion Dashboard")

# -------------------------------------------------
# CREDENTIALS (STREAMLIT CLOUD VERSION)
# -------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
except Exception as e:
    st.error("❌ Failed to load Google credentials from Streamlit Secrets")
    st.code(str(e))
    st.stop()

# -------------------------------------------------
# CONNECT TO GOOGLE SHEET
# -------------------------------------------------
SHEET_ID = "1KS4PgGii9kcDMKxVtJdPKhaPCabdwsBSC3nkjuRRfvw"

try:
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet("System_Logic")
except Exception as e:
    st.error("❌ Failed to connect to Google Sheet")
    st.code(str(e))
    st.stop()

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# REMOVE EMPTY ROWS (Fixes 999 enquiry issue)
if "Week" in df.columns:
    df = df[df["Week"].astype(str).str.strip() != ""]

if df.empty:
    st.warning("⚠️ No valid enquiry data found")
    st.stop()

# -------------------------------------------------
# DATA CLEANING
# -------------------------------------------------
if "Expected_Value" in df.columns:
    df["Expected_Value"] = (
        df["Expected_Value"]
        .astype(str)
        .str.replace("₹", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    df["Expected_Value"] = pd.to_numeric(df["Expected_Value"], errors="coerce").fillna(0)

# -------------------------------------------------
# FINAL ORDER VALUE (AUTO DETECT COLUMN)
# -------------------------------------------------
FINAL_VALUE_COL = None

for col in df.columns:
    if "final" in col.lower() and "value" in col.lower():
        FINAL_VALUE_COL = col
        break

if FINAL_VALUE_COL:
    df[FINAL_VALUE_COL] = (
        df[FINAL_VALUE_COL]
        .astype(str)
        .str.replace("₹", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    df[FINAL_VALUE_COL] = pd.to_numeric(df[FINAL_VALUE_COL], errors="coerce").fillna(0)
    final_order_value = df[FINAL_VALUE_COL].sum()
else:
    final_order_value = 0

# -------------------------------------------------
# CONVERSION METRICS
# -------------------------------------------------
total_enquiries = len(df)

sample_approved = (
    df[df["Sample_Status"] == "Approved"].shape[0]
    if "Sample_Status" in df.columns else 0
)

orders_confirmed = (
    df[df["Order_Status"] == "Confirmed"].shape[0]
    if "Order_Status" in df.columns else 0
)

lead_to_sample = (sample_approved / total_enquiries * 100) if total_enquiries else 0
sample_to_order = (orders_confirmed / sample_approved * 100) if sample_approved else 0
overall_conversion = (orders_confirmed / total_enquiries * 100) if total_enquiries else 0

# -------------------------------------------------
# VALUE METRICS
# -------------------------------------------------
total_expected_value = df["Expected_Value"].sum() if "Expected_Value" in df.columns else 0

value_conversion = (
    final_order_value / total_expected_value * 100
    if total_expected_value else 0
)

# -------------------------------------------------
# DASHBOARD UI
# -------------------------------------------------
st.subheader("🔁 Conversion Funnel")

c1, c2, c3 = st.columns(3)
c1.metric("Total Enquiries", total_enquiries)
c2.metric("Sample Approved", sample_approved)
c3.metric("Orders Confirmed", orders_confirmed)

c4, c5, c6 = st.columns(3)
c4.metric("Overall Conversion %", f"{overall_conversion:.2f}%")
c5.metric("Lead → Sample Conversion %", f"{lead_to_sample:.2f}%")
c6.metric("Sample → Order Conversion %", f"{sample_to_order:.2f}%")

# -------------------------------------------------
st.subheader("💰 Value Conversion")

v1, v2, v3 = st.columns(3)
v1.metric("Total Expected Value", f"₹ {total_expected_value:,.0f}")
v2.metric("Final Order Value", f"₹ {final_order_value:,.0f}")
v3.metric("Value Conversion %", f"{value_conversion:.2f}%")

# -------------------------------------------------
# RAW DATA VIEW
# -------------------------------------------------
with st.expander("🔍 View System_Logic Data"):
    st.dataframe(df)
