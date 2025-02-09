import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import matplotlib.pyplot as plt
import requests
import os
from dotenv import load_dotenv
import datetime

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
      st.success("✅ Data Loaded Successfully")
    else:
      print("Error fetching data:", data)
      st.error(f"❌ Error loading data: {e}")

    # Column names
    # ['ID', 'Team', 'Title', 'Description', 'Status', 'Estimate', 'Priority',
    #   'Project ID', 'Project', 'Creator', 'Assignee', 'Labels',
    #   'Cycle Number', 'Cycle Name', 'Cycle Start', 'Cycle End', 'Created',
    #   'Updated', 'Started', 'Triaged', 'Completed', 'Canceled', 'Archived',
    #   'Due Date', 'Parent issue', 'Initiatives', 'Project Milestone ID',
    #   'Project Milestone', 'SLA Status', 'Roadmaps']

    # Filtering UI
    st.sidebar.header("🔍 Filters")

    if 'Team' in df.columns:
      categories = df['Team'].unique().tolist()
      selected_categories = st.sidebar.multiselect("Filter by Team", categories, default=["Engineering Support"])
      df = df[df['Team'].isin(selected_categories)]

    if 'Date' in df.columns:
      df['Date'] = pd.to_datetime(df['Date'])

    if 'Created' in df.columns:
      df['Created'] = pd.to_datetime(df['Created'])
      time_filter = st.sidebar.radio(
        "Filter by Date Range",
        ["Past Week", "Past Month", "All Time"],
        index=0
      )

    today = datetime.datetime.today()
    if time_filter == "Past Week":
      start_date = today - datetime.timedelta(days=7)
      df = df[df["Created"] >= start_date]
      st.caption(f"📅 Showing data from **{start_date.strftime('%B %d, %Y')}** to **{today.strftime('%B %d, %Y')}**")
    elif time_filter == "Past Month":
      start_date = today - datetime.timedelta(days=30)
      df = df[df["Created"] >= start_date]
      st.caption(f"📅 Showing data from **{start_date.strftime('%B %d, %Y')}** to **{today.strftime('%B %d, %Y')}**")

    st.sidebar.header("📊 Select Dashboard")
    dashboard_selection = st.sidebar.radio("Go to", ["Created Vs Completed"])

    # Dashboard: Overview
    if dashboard_selection == "Created Vs Completed":
      st.header("📊 Created vs Completed Issues by Priority")

    if 'Created' in df.columns and 'Completed' in df.columns:
      df['Created'] = pd.to_datetime(df['Created'], errors='coerce')
      df['Completed'] = pd.to_datetime(df['Completed'], errors='coerce')
      created_df = df[df['Created'].notna() & df['Completed'].isna()]
      completed_df = df[df['Created'].notna() & df['Completed'].notna()]

      if 'Priority' in df.columns:
        created_count = created_df.groupby('Priority').size()
        completed_count = completed_df.groupby('Priority').size()

        comparison_df = pd.DataFrame({
          'Created': created_count,
          'Completed': completed_count
        }).fillna(0)  # Fill missing values with 0

        fig, ax = plt.subplots(figsize=(8, 5))
        bars = comparison_df.plot(kind='bar', ax=ax)

        ax.set_ylabel("Count")
        ax.set_title("Created vs Completed Issues by Priority")
        ax.legend(["Created", "Completed"])

        # Add count labels on the bars
        for bar_container in bars.containers:
          ax.bar_label(bar_container, fmt="%d", label_type="edge", fontsize=10, padding=3)
        st.pyplot(fig)
        st.subheader("📋 Data Table")
        st.write(comparison_df)
      else:
        st.warning("⚠️ 'Priority' column not found in the dataset.")
    else:
      st.error("❌ 'Created' and 'Completed' columns are required.")


    # Display 
    st.subheader("📄 Data")
    st.write(df)
  except Exception as e:
      st.error(f"❌ Error loading data: {e}")
else:
  st.error(f"❌ Failed to load sheet - Invalid URL")

