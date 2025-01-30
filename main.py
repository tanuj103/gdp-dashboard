import streamlit as st
import pandas as pd
from utils import (
    load_and_validate_csv,
    process_stock_data,
    create_return_distribution_chart,
    create_success_rate_chart
)

# Page configuration
st.set_page_config(
    page_title="NSE Stock Analysis Tool",
    page_icon="📈",
    layout="wide"
)

# Title and description
st.title("📈 NSE Stock Analysis Tool")
st.markdown("""
This tool analyzes when stocks hit a specified return target within a given date range.
Upload a CSV file containing stock symbols and dates to get started.
""")

# Parameters input
col1, col2, col3 = st.columns(3)
with col1:
    target_return = st.number_input("Target Return (%)", min_value=1.0, max_value=10.0, value=3.0, step=0.5)
with col2:
    min_days = st.number_input("Minimum Days", min_value=1, max_value=10, value=5)
with col3:
    max_days = st.number_input("Maximum Days", min_value=min_days, max_value=15, value=6)

# File upload
uploaded_file = st.file_uploader(
    "Upload your CSV file (must contain 'symbol' and 'date' columns)",
    type="csv"
)

if uploaded_file is not None:
    # Load and validate CSV
    df, error = load_and_validate_csv(uploaded_file)

    if error:
        st.error(error)
    else:
        with st.spinner('Processing stock data...'):
            # Process the data with parameters
            processed_df = process_stock_data(df, target_return, min_days, max_days)

            # Create two columns for the layout
            viz_col1, viz_col2 = st.columns(2)

            with viz_col1:
                # Display return distribution chart
                st.plotly_chart(
                    create_return_distribution_chart(processed_df, target_return),
                    use_container_width=True
                )

            with viz_col2:
                # Display success rate chart
                st.plotly_chart(
                    create_success_rate_chart(processed_df, target_return),
                    use_container_width=True
                )

            # Display statistics
            st.subheader("📊 Summary Statistics")
            stats_col1, stats_col2, stats_col3 = st.columns(3)

            with stats_col1:
                avg_return = processed_df[processed_df['target_met']]['return_pct'].mean()
                st.metric(
                    f"Average Return (When Hit {target_return}%)", 
                    f"{avg_return:.2f}%" if pd.notna(avg_return) else "N/A"
                )

            with stats_col2:
                success_rate = (
                    processed_df['target_met'].sum() /
                    len(processed_df['target_met'].dropna()) * 100
                )
                st.metric(f"Success Rate (Hit {target_return}%)", f"{success_rate:.2f}%")

            with stats_col3:
                avg_days = processed_df[processed_df['target_met']]['days_taken'].mean()
                st.metric("Avg Days to Hit Target", f"{avg_days:.1f}" if pd.notna(avg_days) else "N/A")

            # Display data table
            st.subheader("📋 Detailed Results")

            # Format the dataframe
            display_df = processed_df[['symbol', 'date', 'entry_price', 'target_price', 'return_pct', 'days_taken', 'target_met']].copy()
            # Fill NA values before formatting
            display_df['return_pct'] = display_df['return_pct'].fillna('N/A')
            display_df['days_taken'] = display_df['days_taken'].fillna('N/A')
            display_df['entry_price'] = display_df['entry_price'].fillna('N/A')
            display_df['target_price'] = display_df['target_price'].fillna('N/A')

            # Format numeric values
            display_df.loc[display_df['return_pct'] != 'N/A', 'return_pct'] = \
                display_df.loc[display_df['return_pct'] != 'N/A', 'return_pct'].map('{:.2f}%'.format)
            display_df.loc[display_df['entry_price'] != 'N/A', 'entry_price'] = \
                display_df.loc[display_df['entry_price'] != 'N/A', 'entry_price'].map('{:.2f}'.format)
            display_df.loc[display_df['target_price'] != 'N/A', 'target_price'] = \
                display_df.loc[display_df['target_price'] != 'N/A', 'target_price'].map('{:.2f}'.format)

            st.dataframe(
                display_df,
                use_container_width=True
            )

            # Add footer
            st.markdown("""
            ---
            Created with ❤️ using Streamlit | Data source: Yahoo Finance (NSE)
            """)

# Add footer when no file is uploaded
if uploaded_file is None:
    st.markdown("""
    ---
    Created with ❤️ using Streamlit | Data source: Yahoo Finance (NSE)
    """)