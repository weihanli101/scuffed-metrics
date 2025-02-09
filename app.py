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
PRODUCT_AREA_LABELS = [
  "Action Items",
  "Alert Grouping",
  "Alert Sources Configuration",
  "Alert Urgency",
  "Alerts",
  "Authentication/Authorization",
  "Catalog",
  "Environments",
  "Escalation Policies",
  "Form Fields",
  "Heartbeats",
  "Incidents",
  "Integrations",
  "LCR",
  "Metrics",
  "On-Call Shift Reminders",
  "On-Call User Group Updates",
  "Onboarding",
  "Paging",
  "Retrospectives",
  "Roles",
  "Schedules(Shifts/Calendar/Rotations...)",
  "Services",
  "Severities",
  "Smart Defaults",
  "Status Pages"
]


def extract_labels(label_str, prefix):
  if pd.isna(label_str):
    return []
  return [label.strip() for label in label_str.split(',') if label.strip().startswith(prefix)]

def extract_labels_by_exact_matches(label_str, match_list):
  if pd.isna(label_str):
    return []
  return [label.strip() for label in label_str.split(',') if label.strip() in match_list]

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
        ["Past Week", "Past Month", "All Time", "Custom"],
        index=0
      )

    min_date = df['Created'].min().date()
    max_date = df['Created'].max().date()
    today = datetime.datetime.today()

    if time_filter == "Past Week":
      start_date = today - datetime.timedelta(days=7)
      df = df[df["Created"] >= start_date]
      st.caption(f"📅 Showing data from **{start_date.strftime('%B %d, %Y')}** to **{today.strftime('%B %d, %Y')}**")
    elif time_filter == "Past Month":
      start_date = today - datetime.timedelta(days=30)
      df = df[df["Created"] >= start_date]
      st.caption(f"📅 Showing data from **{start_date.strftime('%B %d, %Y')}** to **{today.strftime('%B %d, %Y')}**")
    elif time_filter == "Custom":
      start_date, end_date = st.sidebar.date_input(
        "Select Custom Date Range",
        [min_date, max_date]
      )
      start_date = pd.Timestamp(start_date)
      end_date = pd.Timestamp(end_date)

      df = df[(df['Created'] >= start_date) & (df['Created'] <= end_date)]
      st.caption(f"📅 Showing data from **{start_date.strftime('%B %d, %Y')}** to **{end_date.strftime('%B %d, %Y')}**")

    st.sidebar.header("📊 Select Dashboard")
    dashboard_selection = st.sidebar.radio(
      "Go to", 
      [
        "Created/Completed By Urgency", 
        "Created/Completed By Customer",
        "Total Unable To Replicate",
        "# Of Tickets Grouped By Product Area"
      ]
    )

    # Dashboard: Overview
    if dashboard_selection == "Created/Completed By Urgency":
      st.header("🔔 Created/Completed By Urgency")
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
          }).fillna(0)

          fig, ax = plt.subplots(figsize=(8, 5))
          bars = comparison_df.plot(kind='bar', ax=ax)

          ax.set_ylabel("Count")
          ax.set_title("Created vs Completed Issues by Priority")
          ax.legend(["Created", "Completed"])

          for bar_container in bars.containers:
            ax.bar_label(bar_container, fmt="%d", label_type="edge", fontsize=10, padding=3)
          st.pyplot(fig)
          st.subheader("📋 Data Table")
          st.write(comparison_df)
        else:
          st.warning("⚠️ 'Priority' column not found in the dataset.")
      else:
        st.error("❌ 'Created' and 'Completed' columns are required.")

    elif dashboard_selection == "Created/Completed By Customer":
      st.subheader("👤 Created/Completed By Customer")
      df['Filtered_Labels'] = df['Labels'].apply(lambda label: extract_labels(label, "C -"))
      df_exploded = df.explode('Filtered_Labels')
      df_exploded = df_exploded[df_exploded['Filtered_Labels'].notna()]
      created_df = df_exploded[df_exploded['Created'].notna() & df_exploded['Completed'].isna()]
      completed_df = df_exploded[df_exploded['Created'].notna() & df_exploded['Completed'].notna()]
      created_count = created_df.groupby('Filtered_Labels').size()
      completed_count = completed_df.groupby('Filtered_Labels').size()

      label_comparison_df = pd.DataFrame({
        'Created': created_count,
        'Completed': completed_count
      }).fillna(0)

      fig, ax = plt.subplots(figsize=(8, 5))
      bars = label_comparison_df.plot(kind='bar', ax=ax)

      ax.set_ylabel("Count")
      ax.set_title("Created vs Completed Issues by Labels (Filtered: 'C -')")
      ax.legend(["Created", "Completed"])

      for bar_container in bars.containers:
        ax.bar_label(bar_container, fmt="%d", label_type="edge", fontsize=10, padding=3)

      st.pyplot(fig)
      st.subheader("📋 Data Table")
      st.write(label_comparison_df)
    elif dashboard_selection == "Total Unable To Replicate":
      st.subheader("🔍 Total Unable To Replicate Issues")
      df['Filtered_Labels'] = df['Labels'].apply(lambda label: extract_labels(label, "Unable To Replicate"))
      df_exploded = df.explode('Filtered_Labels')
      df_exploded = df_exploded[df_exploded['Filtered_Labels'].notna()]
      unable_to_replicate_df = df_exploded[df_exploded['Filtered_Labels'] == "Unable To Replicate"]
      total_unable_to_replicate = len(unable_to_replicate_df)
      st.metric(label="Total 'Unable To Replicate' Issues", value=total_unable_to_replicate)
      st.subheader("📋 Issues Marked as 'Unable To Replicate'")
      st.write(unable_to_replicate_df)
    elif dashboard_selection == "# Of Tickets Grouped By Product Area":
      st.subheader("📱 # Of Tickets Grouped By Product Area")
      df['Filtered_Labels'] = df['Labels'].apply(lambda label: extract_labels_by_exact_matches(label, PRODUCT_AREA_LABELS))
      df_exploded = df.explode('Filtered_Labels')
      df_exploded = df_exploded[df_exploded['Filtered_Labels'].notna()]
      label_summary = df_exploded['Filtered_Labels'].value_counts()
      fig, ax = plt.subplots(figsize=(10, len(label_summary) / 2))
      label_summary.plot(kind='barh', ax=ax)
      ax.set_xlabel("Count")
      ax.set_title("Total Rows per Label")
      for bar in ax.containers:
        ax.bar_label(bar, fmt="%d", label_type="edge", fontsize=10, padding=3)

      st.pyplot(fig)


    if dashboard_selection is None or dashboard_selection == "":
      st.subheader("📄 Data")
      st.write(df)
  except Exception as e:
      st.error(f"❌ Error loading data: {e}")
else:
  st.error(f"❌ Failed to load sheet - Invalid URL")

