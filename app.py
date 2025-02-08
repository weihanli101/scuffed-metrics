import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import matplotlib.pyplot as plt
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
SHEET_ID = os.getenv("SHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME")

st.title("📊 Scuffed Metrics")

# Construct the URL
url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{SHEET_NAME}?key={API_KEY}"

# Fetch Data from Google Sheets
response = requests.get(url)
data = response.json()

if url:
  try:
    if "values" in data:
        df = pd.DataFrame(data["values"])
        df.columns = df.iloc[0]  # Set first row as column names
        df = df[1:]  # Remove first row
        print(df)  # Display data
    else:
        print("Error fetching data:", data)
    st.success("✅ Data Loaded Successfully")

    # Display Data
    st.subheader("📄 Data Preview")
    st.write(df)

    # Convert 'Date' column to datetime (if exists)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])

    # Filtering UI
    st.sidebar.header("🔍 Filters")

    # Filter by Category (if exists)
    if 'Category' in df.columns:
        categories = df['Category'].unique().tolist()
        selected_categories = st.sidebar.multiselect("Filter by Category", categories, default=categories)
        df = df[df['Category'].isin(selected_categories)]

    # Filter by Date Range (if exists)
    if 'Date' in df.columns:
        min_date, max_date = df['Date'].min(), df['Date'].max()
        date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
        df = df[(df['Date'] >= pd.to_datetime(date_range[0])) & (df['Date'] <= pd.to_datetime(date_range[1]))]

    # Choose column for visualization
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

    if numeric_columns:
        selected_column = st.sidebar.selectbox("📊 Select a numerical column to visualize", numeric_columns)

        # Plot filtered data
        st.subheader("📈 Data Visualization")
        fig, ax = plt.subplots(figsize=(10, 5))
        df.plot(kind='line', x='Date', y=selected_column, ax=ax, marker='o')
        ax.set_title(f"{selected_column} Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel(selected_column)
        st.pyplot(fig)

    else:
      st.warning("⚠ No numerical columns found for visualization.")
    
  except Exception as e:
      st.error(f"❌ Error loading data: {e}")
else:
  st.error(f"❌ Failed to load sheet - Invalid URL")

