# ============================================================================
# TASK 5: STREAMLIT DASHBOARD – FINANCIAL INCLUSION FORECASTING
# ============================================================================
# This dashboard visualizes Ethiopia's financial inclusion data,
# event impacts, and forecasts for 2025-2027.
# ============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Ethiopia Financial Inclusion Dashboard",
    page_icon="🇪🇹",
    layout="wide"
)

# ============================================================================
# 1. LOAD DATA
# ============================================================================
@st.cache_data
def load_data():
    """Load all processed data files"""
    # Load enriched dataset
    df = pd.read_csv('../data/processed/ethiopia_fi_enriched.csv')
    df['observation_date'] = pd.to_datetime(df['observation_date'], errors='coerce')
    
    # Load forecasts
    try:
        forecasts = pd.read_csv('../data/processed/forecasts.csv')
    except:
        forecasts = None
    
    # Load impact matrix
    try:
        impact_matrix = pd.read_csv('../data/processed/manual_impact_matrix.csv', index_col='category')
    except:
        impact_matrix = None
    
    # Load EDA insights
    try:
        insights = pd.read_csv('../data/processed/eda_insights.csv')
    except:
        insights = None
    
    return df, forecasts, impact_matrix, insights

df, forecasts, impact_matrix, insights = load_data()

# Filter observations
observations = df[df['record_type'] == 'observation'].copy()
events = df[df['record_type'] == 'event'].copy()

# ============================================================================
# 2. SIDEBAR
# ============================================================================
st.sidebar.title("🇪🇹 Financial Inclusion Dashboard")
st.sidebar.markdown("---")

# Year range selector
years = observations['observation_date'].dt.year.dropna().unique()
if len(years) > 0:
    min_year = int(min(years))
    max_year = int(max(years))
    year_range = st.sidebar.slider(
        "Select Year Range",
        min_value=min_year,
        max_value=max_year + 3,
        value=(min_year, max_year)
    )

# Indicator selector
indicator_codes = observations['indicator_code'].dropna().unique()
selected_indicator = st.sidebar.selectbox(
    "Select Indicator",
    options=sorted(indicator_codes),
    index=0 if len(indicator_codes) > 0 else None
)

st.sidebar.markdown("---")
st.sidebar.info(
    "Data sources: Global Findex, GSMA, Ethio Telecom, NBE\n\n"
    "Forecast methodology: Trend extrapolation + event impact modeling"
)

# ============================================================================
# 3. MAIN HEADER
# ============================================================================
st.title("🇪🇹 Ethiopia Financial Inclusion Dashboard")
st.markdown("**Tracking Access and Usage through 2027**")
st.markdown("---")

# ============================================================================
# 4. KEY METRICS
# ============================================================================
col1, col2, col3, col4 = st.columns(4)

# Get latest account ownership
acc_data = observations[observations['indicator_code'] == 'ACC_OWNERSHIP']
if not acc_data.empty:
    latest_acc = acc_data.iloc[-1]['value_numeric']
    latest_acc_year = acc_data.iloc[-1]['observation_date'].year
    col1.metric("Account Ownership (Access)", f"{latest_acc:.1f}%", f"as of {latest_acc_year}")

# Get latest mobile money
mm_data = observations[observations['indicator_code'] == 'ACC_MM_ACCOUNT']
if not mm_data.empty:
    latest_mm = mm_data.iloc[-1]['value_numeric']
    latest_mm_year = mm_data.iloc[-1]['observation_date'].year
    col2.metric("Mobile Money Accounts", f"{latest_mm:.1f}%", f"as of {latest_mm_year}")

# Get latest P2P count (if available)
p2p_data = observations[observations['indicator_code'] == 'USG_P2P_COUNT']
if not p2p_data.empty:
    latest_p2p = p2p_data.iloc[-1]['value_numeric']
    latest_p2p_year = p2p_data.iloc[-1]['observation_date'].year
    col3.metric("P2P Transfer Count", f"{latest_p2p:.1f}M", f"as of {latest_p2p_year}")

# Get forecast for 2027 (if available)
if forecasts is not None:
    acc_forecast = forecasts[(forecasts['Indicator'] == 'ACC_OWNERSHIP') & 
                              (forecasts['Year'] == 2027) & 
                              (forecasts['Scenario'] == 'Base')]
    if not acc_forecast.empty:
        forecast_val = acc_forecast['Forecast'].values[0]
        change = forecast_val - latest_acc
        col4.metric("2027 Forecast (Access)", f"{forecast_val:.1f}%", f"{change:+.1f}pp from 2024")

st.markdown("---")

# ============================================================================
# 5. MAIN VISUALIZATION – SELECTED INDICATOR TREND
# ============================================================================
st.subheader(f"📈 {selected_indicator} Trend")

# Filter data for selected indicator
indicator_data = observations[observations['indicator_code'] == selected_indicator].copy()
indicator_data = indicator_data.sort_values('observation_date')

# Filter by year range
indicator_data = indicator_data[
    (indicator_data['observation_date'].dt.year >= year_range[0]) &
    (indicator_data['observation_date'].dt.year <= year_range[1])
]

if not indicator_data.empty:
    # Create plotly chart
    fig = px.line(
        indicator_data,
        x='observation_date',
        y='value_numeric',
        title=f'{selected_indicator} Over Time',
        labels={'value_numeric': 'Value', 'observation_date': 'Year'},
        markers=True
    )
    
    # Add confidence bands if available
    fig.update_layout(
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning(f"No data available for {selected_indicator} in the selected range.")

# ============================================================================
# 6. EVENT TIMELINE
# ============================================================================
st.subheader("📅 Key Events Timeline")

# Display events as a timeline
if not events.empty:
    events_display = events[['indicator', 'observation_date', 'category', 'source_name']].copy()
    events_display = events_display.dropna(subset=['observation_date'])
    events_display['observation_date'] = pd.to_datetime(events_display['observation_date'])
    events_display = events_display.sort_values('observation_date')
    
    # Filter by year range
    events_display = events_display[
        (events_display['observation_date'].dt.year >= year_range[0]) &
        (events_display['observation_date'].dt.year <= year_range[1])
    ]
    
    if not events_display.empty:
        # Create timeline
        fig = px.timeline(
            events_display,
            x_start='observation_date',
            x_end='observation_date',
            y='category',
            text='indicator',
            color='category',
            title='Major Events Timeline'
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No events in selected date range.")
else:
    st.info("No events cataloged.")

# ============================================================================
# 7. FORECAST SECTION
# ============================================================================
if forecasts is not None:
    st.subheader("🔮 Forecasts for 2025-2027")
    
    # Filter for Access and Usage
    acc_forecast = forecasts[forecasts['Indicator'] == 'ACC_OWNERSHIP']
    mm_forecast = forecasts[forecasts['Indicator'] == 'ACC_MM_ACCOUNT']
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not acc_forecast.empty:
            st.write("**Account Ownership Forecast**")
            fig = px.line(
                acc_forecast,
                x='Year',
                y='Forecast',
                color='Scenario',
                title='Account Ownership 2025-2027'
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if not mm_forecast.empty:
            st.write("**Mobile Money Forecast**")
            fig = px.line(
                mm_forecast,
                x='Year',
                y='Forecast',
                color='Scenario',
                title='Mobile Money Accounts 2025-2027'
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    # Forecast table
    with st.expander("📊 View Forecast Table"):
        st.dataframe(forecasts)
else:
    st.info("Forecast data not available. Complete Task 4 first.")

# ============================================================================
# 8. IMPACT MATRIX
# ============================================================================
if impact_matrix is not None:
    st.subheader("📊 Event Impact Matrix")
    st.write("Estimated impact of different event categories on key indicators")
    
    # Heatmap
    fig = px.imshow(
        impact_matrix,
        text_auto=True,
        title='Event Category Impact Matrix',
        labels=dict(x="Indicator", y="Event Category", color="Impact (pp)"),
        color_continuous_scale='RdYlGn',
        aspect='auto'
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Impact matrix not available.")

# ============================================================================
# 9. DATA QUALITY
# ============================================================================
with st.expander("📋 Data Quality Summary"):
    st.write("**Data Coverage by Record Type:**")
    st.dataframe(df['record_type'].value_counts().reset_index().rename(
        columns={'record_type': 'Record Type', 'count': 'Count'}
    ))
    
    st.write("**Confidence Distribution:**")
    st.dataframe(df['confidence'].value_counts().reset_index().rename(
        columns={'confidence': 'Confidence', 'count': 'Count'}
    ))

# ============================================================================
# 10. FOOTER
# ============================================================================
st.markdown("---")
st.caption(
    "Data: Global Findex, GSMA, Ethio Telecom, National Bank of Ethiopia | "
    "Forecast: Selam Analytics | "
    "Dashboard: Streamlit"
)