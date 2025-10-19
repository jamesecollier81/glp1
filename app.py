import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import os
import gspread
from google.oauth2.service_account import Credentials
import numpy as np

st.set_page_config(page_title="GLP-1 Injection Tracker", page_icon="💉", layout="wide")

# Google Sheets configuration
SHEET_URL = st.secrets.get("SHEET_URL", "")
SERVICE_ACCOUNT_INFO = st.secrets.get("SERVICE_ACCOUNT_INFO", {})

def get_gsheet_client():
    """Initialize Google Sheets client"""
    if not SERVICE_ACCOUNT_INFO:
        return None

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scopes)
    return gspread.authorize(credentials)

@st.cache_data(ttl=60)  # Cache for 1 minute
def load_data():
    """Load data from Google Sheets"""
    try:
        # Connect to Google Sheets
        if SERVICE_ACCOUNT_INFO and SHEET_URL:
            client = get_gsheet_client()
            if client:
                # Extract sheet ID from URL
                sheet_id = SHEET_URL.split('/d/')[1].split('/')[0]
                sheet = client.open_by_key(sheet_id)

                # Load injections data
                try:
                    injections_worksheet = sheet.worksheet("injections")
                    injections_data = injections_worksheet.get_all_records()
                    injections_df = pd.DataFrame(injections_data)
                    if not injections_df.empty:
                        # Handle both serial numbers and date strings
                        def parse_date(val):
                            try:
                                # If it's a number (serial date from Excel/Sheets)
                                if isinstance(val, (int, float)):
                                    # Excel/Google Sheets epoch: December 30, 1899
                                    return pd.Timestamp('1899-12-30') + pd.Timedelta(days=val)
                                # Otherwise try to parse as string
                                return pd.to_datetime(val)
                            except:
                                return pd.NaT
                        
                        injections_df['date'] = injections_df['date'].apply(parse_date)
                except Exception as e:
                    st.error(f"Error loading injections: {e}")
                    injections_df = pd.DataFrame(columns=['date', 'time', 'dosage', 'weight', 'site', 'notes', 'user'])

                # Load side effects data
                try:
                    side_effects_worksheet = sheet.worksheet("side_effects")
                    side_effects_data = side_effects_worksheet.get_all_records()
                    side_effects_df = pd.DataFrame(side_effects_data)
                    if not side_effects_df.empty:
                        # Handle both serial numbers and date strings
                        def parse_date(val):
                            try:
                                # If it's a number (serial date from Excel/Sheets)
                                if isinstance(val, (int, float)):
                                    # Excel/Google Sheets epoch: December 30, 1899
                                    return pd.Timestamp('1899-12-30') + pd.Timedelta(days=val)
                                # Otherwise try to parse as string
                                return pd.to_datetime(val)
                            except:
                                return pd.NaT
                        
                        side_effects_df['date'] = side_effects_df['date'].apply(parse_date)
                except Exception as e:
                    st.error(f"Error loading side effects: {e}")
                    side_effects_df = pd.DataFrame(columns=['date', 'notes', 'user'])
            else:
                raise Exception("Could not authenticate with Google Sheets")
        else:
            # Fallback to CSV files for local development
            try:
                injections_df = pd.read_csv('injections.csv')
                injections_df['date'] = pd.to_datetime(injections_df['date'])
            except FileNotFoundError:
                injections_df = pd.DataFrame(columns=['date', 'time', 'dosage', 'weight', 'site', 'notes', 'user'])

            try:
                side_effects_df = pd.read_csv('side_effects.csv')
                side_effects_df['date'] = pd.to_datetime(side_effects_df['date'])
            except FileNotFoundError:
                side_effects_df = pd.DataFrame(columns=['date', 'notes', 'user'])

    except Exception as e:
        st.error(f"Error loading data: {e}")
        # Fallback to CSV files
        try:
            injections_df = pd.read_csv('injections.csv')
            injections_df['date'] = pd.to_datetime(injections_df['date'])
        except FileNotFoundError:
            injections_df = pd.DataFrame(columns=['date', 'time', 'dosage', 'weight', 'site', 'notes', 'user'])

        try:
            side_effects_df = pd.read_csv('side_effects.csv')
            side_effects_df['date'] = pd.to_datetime(side_effects_df['date'])
        except FileNotFoundError:
            side_effects_df = pd.DataFrame(columns=['date', 'notes', 'user'])

    return injections_df, side_effects_df

def append_to_sheet(new_row, sheet_name):
    """Append a single row to Google Sheets without clearing existing data"""
    try:
        if SERVICE_ACCOUNT_INFO and SHEET_URL:
            client = get_gsheet_client()
            if client:
                # Extract sheet ID from URL
                sheet_id = SHEET_URL.split('/d/')[1].split('/')[0]
                sheet = client.open_by_key(sheet_id)
                worksheet = sheet.worksheet(sheet_name)
                
                # Append the new row
                worksheet.append_row(new_row)
                return True
        return False
    except Exception as e:
        st.error(f"Error appending to sheet: {e}")
        return False

st.title("💉 GLP-1 Injection Tracker")

# User selection in sidebar
st.sidebar.title("User")
selected_user = st.sidebar.radio("Select User", ["James", "Shannon"], key="user_selector")

st.sidebar.markdown("---")
st.sidebar.title("Navigation")

# Add refresh button in sidebar
if st.sidebar.button("🔄 Refresh Data", help="Force reload data from Google Sheets"):
    # Clear the cache to force fresh data load
    load_data.clear()
    st.rerun()

# Load existing data
injections_df, side_effects_df = load_data()

# Filter data by selected user
if not injections_df.empty and 'user' in injections_df.columns:
    user_injections_df = injections_df[injections_df['user'] == selected_user].copy()
else:
    user_injections_df = injections_df.copy()

if not side_effects_df.empty and 'user' in side_effects_df.columns:
    user_side_effects_df = side_effects_df[side_effects_df['user'] == selected_user].copy()
else:
    user_side_effects_df = side_effects_df.copy()

# Navigation
page = st.sidebar.selectbox("Choose a page", ["Injection Tracking", "Side Effects", "Analytics"])

if page == "Injection Tracking":
    st.header(f"📝 Log Injection - {selected_user}")

    with st.form("injection_form"):
        col1, col2 = st.columns(2)

        with col1:
            injection_date = st.date_input("Date", value=date.today())
            injection_time = st.time_input("Time", value=datetime.now().time())

        with col2:
            dosage = st.number_input("Dosage (mg)", min_value=0.0, step=0.25, format="%.2f")
            weight = st.number_input("Weight (lbs)", min_value=0.0, step=0.1, format="%.1f")

        site = st.selectbox("Injection Site",
                           options=["", "Abdomen", "Thigh", "Upper Arm", "Other"],
                           help="Select the injection site")

        notes = st.text_area("Notes (optional)")

        if st.form_submit_button("Log Injection"):
            new_injection = {
                'date': injection_date,
                'time': injection_time,
                'dosage': dosage,
                'weight': weight,
                'site': site,
                'notes': notes,
                'user': selected_user
            }

            # Prepare row for Google Sheets (as strings)
            new_row = [
                str(injection_date),
                str(injection_time),
                str(dosage),
                str(weight),
                str(site),
                str(notes),
                selected_user
            ]
            
            # Append to Google Sheets
            if append_to_sheet(new_row, "injections"):
                st.success(f"Injection logged successfully for {selected_user}!")
                load_data.clear()
                st.rerun()
            else:
                st.error("Failed to log injection. Please try again.")

    # Display recent injections
    if not user_injections_df.empty:
        st.header(f"Recent Injections - {selected_user}")
        recent_injections = user_injections_df.sort_values('date', ascending=False).head(10)
        # Drop user column for display
        display_cols = [col for col in recent_injections.columns if col != 'user']
        st.dataframe(recent_injections[display_cols], use_container_width=True)

elif page == "Side Effects":
    st.header(f"🤢 Log Side Effects - {selected_user}")

    with st.form("side_effects_form"):
        effect_date = st.date_input("Date", value=date.today())
        effect_notes = st.text_area("Side Effects Description", placeholder="Describe any side effects experienced...")

        if st.form_submit_button("Log Side Effects"):
            if effect_notes.strip():
                # Prepare row for Google Sheets (as strings)
                new_row = [
                    str(effect_date),
                    str(effect_notes),
                    selected_user
                ]
                
                # Append to Google Sheets
                if append_to_sheet(new_row, "side_effects"):
                    st.success(f"Side effects logged successfully for {selected_user}!")
                    load_data.clear()
                    st.rerun()
                else:
                    st.error("Failed to log side effects. Please try again.")
            else:
                st.error("Please enter side effects description")

    # Display recent side effects
    if not user_side_effects_df.empty:
        st.header(f"Recent Side Effects - {selected_user}")
        recent_effects = user_side_effects_df.sort_values('date', ascending=False).head(10)
        # Drop user column for display
        display_cols = [col for col in recent_effects.columns if col != 'user']
        st.dataframe(recent_effects[display_cols], use_container_width=True)

elif page == "Analytics":
    st.header(f"📊 Analytics Dashboard - {selected_user}")

    if user_injections_df.empty:
        st.warning(f"No injection data available for {selected_user}. Please log some injections first.")
    else:
        # Weight tracking
        st.subheader("Weight Trends")
        if 'weight' in user_injections_df.columns and not user_injections_df['weight'].isna().all():
            weight_data = user_injections_df[user_injections_df['weight'] > 0].copy()
            if not weight_data.empty:
                # Sort by date to ensure proper rolling calculation
                weight_data = weight_data.sort_values('date')

                # Calculate 15-day rolling average
                weight_data['rolling_avg'] = weight_data['weight'].rolling(window=15, min_periods=1).mean()

                # Create figure with multiple traces
                fig_weight = go.Figure()

                # Add actual weight data
                fig_weight.add_trace(go.Scatter(
                    x=weight_data['date'],
                    y=weight_data['weight'],
                    mode='markers+lines',
                    name='Actual Weight',
                    line=dict(color='blue', width=1),
                    marker=dict(size=6)
                ))

                # Add 15-day rolling average
                fig_weight.add_trace(go.Scatter(
                    x=weight_data['date'],
                    y=weight_data['rolling_avg'],
                    mode='lines',
                    name='15-Day Rolling Average',
                    line=dict(color='orange', width=3)
                ))

                # Add linear trend line (only if we have enough data points)
                if len(weight_data) >= 2:
                    try:
                        x_numeric = np.arange(len(weight_data))
                        # Ensure we have valid weight data
                        valid_weights = weight_data['weight'].dropna()
                        if len(valid_weights) >= 2 and valid_weights.std() > 0:
                            z = np.polyfit(x_numeric, weight_data['weight'], 1)
                            trend_line = np.poly1d(z)(x_numeric)

                            fig_weight.add_trace(go.Scatter(
                                x=weight_data['date'],
                                y=trend_line,
                                mode='lines',
                                name='Linear Trend',
                                line=dict(color='red', width=2, dash='dash')
                            ))
                    except (np.linalg.LinAlgError, ValueError):
                        # Skip trend line if calculation fails
                        pass

                fig_weight.update_layout(
                    title='Weight Over Time with Trends',
                    xaxis_title="Date",
                    yaxis_title="Weight (lbs)",
                    showlegend=True,
                    xaxis=dict(tickformat='%Y-%m-%d')
                )
                st.plotly_chart(fig_weight, use_container_width=True)

        # Dosage tracking
        st.subheader("Dosage Trends")
        if 'dosage' in user_injections_df.columns and not user_injections_df['dosage'].isna().all():
            dosage_data = user_injections_df[user_injections_df['dosage'] > 0].copy()
            if not dosage_data.empty:
                fig_dosage = px.line(dosage_data, x='date', y='dosage',
                                   title='Dosage Over Time',
                                   markers=True)
                fig_dosage.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Dosage (mg)",
                    xaxis=dict(tickformat='%Y-%m-%d')
                )
                st.plotly_chart(fig_dosage, use_container_width=True)

        # Side effects correlation
        if not user_side_effects_df.empty:
            st.subheader("Side Effects Timeline")

            # Create a timeline showing injections and side effects
            fig_timeline = go.Figure()

            # Add injection dates
            if not user_injections_df.empty:
                fig_timeline.add_trace(go.Scatter(
                    x=user_injections_df['date'],
                    y=[1] * len(user_injections_df),
                    mode='markers',
                    name='Injections',
                    marker=dict(color='blue', size=10),
                    text=user_injections_df['dosage'].astype(str) + ' mg',
                    hovertemplate='<b>Injection</b><br>Date: %{x}<br>Dosage: %{text}<extra></extra>'
                ))

            # Add side effect dates
            fig_timeline.add_trace(go.Scatter(
                x=user_side_effects_df['date'],
                y=[2] * len(user_side_effects_df),
                mode='markers',
                name='Side Effects',
                marker=dict(color='red', size=10),
                text=user_side_effects_df['notes'],
                hovertemplate='<b>Side Effect</b><br>Date: %{x}<br>Notes: %{text}<extra></extra>'
            ))

            fig_timeline.update_layout(
                title="Injections vs Side Effects Timeline",
                xaxis_title="Date",
                yaxis=dict(
                    tickvals=[1, 2],
                    ticktext=['Injections', 'Side Effects'],
                    range=[0.5, 2.5]
                ),
                showlegend=True,
                xaxis=dict(tickformat='%Y-%m-%d')
            )
            st.plotly_chart(fig_timeline, use_container_width=True)

        # Summary statistics
        st.subheader("Summary Statistics")
        col1, col2, col3 = st.columns(3)

        with col1:
            total_injections = len(user_injections_df)
            st.metric("Total Injections", total_injections)

        with col2:
            if not user_injections_df.empty and 'weight' in user_injections_df.columns:
                weight_data = user_injections_df[user_injections_df['weight'] > 0]
                if len(weight_data) > 1:
                    weight_change = weight_data.iloc[-1]['weight'] - weight_data.iloc[0]['weight']
                    st.metric("Weight Change", f"{weight_change:.1f} lbs")

        with col3:
            total_side_effects = len(user_side_effects_df)
            st.metric("Total Side Effect Reports", total_side_effects)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("💡 **Tips:**")
st.sidebar.markdown("• 2mg = 16 units")
st.sidebar.markdown("• 3mg = 24 units")
st.sidebar.markdown("• 4mg = 32 units")
st.sidebar.markdown("• 5mg = 40 units")
st.sidebar.markdown("• Each addtl mg = 8 units")
