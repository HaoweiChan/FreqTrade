"""
Streamlit Dashboard for Backtest Results Visualization.

Run with: streamlit run strategy_tools/backtest_dashboard.py
"""

import os
import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtest_db import init_backtest_db

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Backtest Results Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .positive { color: #00c853; }
    .negative { color: #ff5252; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_db():
    """Get database connection (cached)."""
    # Check for remote API
    api_url = os.getenv("REMOTE_API_URL")
    if api_url:
        return None
    return init_backtest_db()


class RemoteAPIClient:
    """Client for Remote Backtest API."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
    
    def get_all_results(self):
        try:
            resp = requests.get(f"{self.base_url}/api/results?limit=1000")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            st.error(f"API Error: {e}")
            return []

    def get_summary_stats(self):
        try:
            resp = requests.get(f"{self.base_url}/api/stats")
            resp.raise_for_status()
            data = resp.json()
            # Remap keys to match DB format if necessary
            return {
                'total_runs': data['total_runs'],
                'successful': data['successful_runs'],
                'failed': data['failed_runs'],
                'success_rate': data['success_rate'],
                'best_strategy': data['best_strategy'],
                'best_return': data['best_return'],
                'avg_return': data['avg_return']
            }
        except Exception as e:
            st.error(f"API Error: {e}")
            return {}


@st.cache_data(ttl=60)
def load_results():
    """Load all results from database or API."""
    api_url = os.getenv("REMOTE_API_URL")
    if api_url:
        client = RemoteAPIClient(api_url)
        return client.get_all_results()
    
    db = get_db()
    return db.get_all_results()


@st.cache_data(ttl=60)
def load_summary():
    """Load summary statistics."""
    api_url = os.getenv("REMOTE_API_URL")
    if api_url:
        client = RemoteAPIClient(api_url)
        return client.get_summary_stats()
        
    db = get_db()
    return db.get_summary_stats()


def main():
    st.title("📊 Strategy Backtest Results Dashboard")
    
    # Sidebar
    st.sidebar.header("Filters")
    
    # Load data
    try:
        results = load_results()
        summary = load_summary()
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        st.info("Make sure DATABASE_URL is set in .env and PostgreSQL is running.")
        return
    
    if not results:
        st.warning("No backtest results found in database.")
        st.info("Run `python strategy_tools/migrate_to_db.py` to migrate existing results.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Sidebar filters
    status_filter = st.sidebar.multiselect(
        "Status",
        options=df['status'].unique().tolist(),
        default=['SUCCESS']
    )
    
    # Strategy name search
    search = st.sidebar.text_input("Search Strategy", "")
    
    # Return range filter
    if 'total_return' in df.columns:
        min_return = float(df['total_return'].min() or -100)
        max_return = float(df['total_return'].max() or 200)
        return_range = st.sidebar.slider(
            "Return Range (%)",
            min_value=min_return,
            max_value=max_return,
            value=(min_return, max_return)
        )
    
    # Apply filters
    filtered_df = df[df['status'].isin(status_filter)]
    
    if search:
        filtered_df = filtered_df[
            filtered_df['strategy_name'].str.contains(search, case=False, na=False)
        ]
    
    if 'total_return' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['total_return'] >= return_range[0]) &
            (filtered_df['total_return'] <= return_range[1])
        ]
    
    # Summary metrics
    st.header("📈 Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Strategies", summary['total_runs'])
    
    with col2:
        st.metric("Successful", summary['successful'], 
                  delta=f"{summary['success_rate']:.1f}%")
    
    with col3:
        st.metric("Failed", summary['failed'])
    
    with col4:
        st.metric("Best Return", 
                  f"{summary['best_return']:.2f}%" if summary['best_return'] else "N/A",
                  delta=summary['best_strategy'])
    
    with col5:
        st.metric("Avg Return", f"{summary['avg_return']:.2f}%")
    
    st.divider()
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Results Table", "📊 Charts", "❌ Failed Strategies", "🔍 Strategy Details"])
    
    with tab1:
        st.header("Strategy Results")
        
        # Display columns
        display_cols = [
            'strategy_name', 'status', 'total_return', 'total_trades',
            'win_rate', 'profit_factor', 'sharpe_ratio', 'max_drawdown',
            'avg_duration', 'detected_timeframe', 'created_at'
        ]
        available_cols = [c for c in display_cols if c in filtered_df.columns]
        
        # Sort options
        sort_col = st.selectbox("Sort by", available_cols, index=2 if 'total_return' in available_cols else 0)
        sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True)
        
        sorted_df = filtered_df.sort_values(
            by=sort_col, 
            ascending=(sort_order == "Ascending"),
            na_position='last'
        )
        
        # Style the dataframe
        def color_return(val):
            if pd.isna(val):
                return ''
            color = 'green' if val > 0 else 'red' if val < 0 else 'gray'
            return f'color: {color}'
        
        styled_df = sorted_df[available_cols].style.applymap(
            color_return, subset=['total_return'] if 'total_return' in available_cols else []
        )
        
        st.dataframe(styled_df, use_container_width=True, height=500)
        
        # Download button
        csv = sorted_df[available_cols].to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            csv,
            "backtest_results.csv",
            "text/csv"
        )
    
    with tab2:
        st.header("Performance Charts")
        
        # Filter to successful strategies for charts
        success_df = filtered_df[filtered_df['status'] == 'SUCCESS'].copy()
        
        if success_df.empty:
            st.warning("No successful backtests to display charts.")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                # Return distribution
                fig = px.histogram(
                    success_df,
                    x='total_return',
                    nbins=30,
                    title="Return Distribution",
                    labels={'total_return': 'Total Return (%)'}
                )
                fig.add_vline(x=0, line_dash="dash", line_color="red")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Win rate vs Return scatter
                fig = px.scatter(
                    success_df,
                    x='win_rate',
                    y='total_return',
                    size='total_trades',
                    hover_data=['strategy_name'],
                    title="Win Rate vs Return",
                    labels={
                        'win_rate': 'Win Rate (%)',
                        'total_return': 'Total Return (%)'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            
            col3, col4 = st.columns(2)
            
            with col3:
                # Top 20 strategies bar chart
                top_20 = success_df.nlargest(20, 'total_return')
                fig = px.bar(
                    top_20,
                    x='strategy_name',
                    y='total_return',
                    title="Top 20 Strategies by Return",
                    labels={'total_return': 'Return (%)', 'strategy_name': 'Strategy'},
                    color='total_return',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            
            with col4:
                # Drawdown vs Return scatter
                fig = px.scatter(
                    success_df,
                    x='max_drawdown',
                    y='total_return',
                    hover_data=['strategy_name'],
                    title="Risk vs Return (Drawdown)",
                    labels={
                        'max_drawdown': 'Max Drawdown (%)',
                        'total_return': 'Total Return (%)'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.header("Failed Strategies")
        
        failed_df = df[df['status'] == 'FAILED']
        
        if failed_df.empty:
            st.success("No failed strategies! 🎉")
        else:
            st.warning(f"{len(failed_df)} strategies failed to backtest")
            
            for idx, row in failed_df.iterrows():
                with st.expander(f"❌ {row['strategy_name']}"):
                    st.write(f"**Error:** {row.get('error_message', 'Unknown error')}")
                    if row.get('detected_timeframe'):
                        st.write(f"**Timeframe:** {row['detected_timeframe']}")
                    if row.get('created_at'):
                        st.write(f"**Timestamp:** {row['created_at']}")
    
    with tab4:
        st.header("Strategy Details")
        
        # Strategy selector
        strategy_names = sorted(df['strategy_name'].unique().tolist())
        selected_strategy = st.selectbox("Select Strategy", strategy_names)
        
        if selected_strategy:
            strategy_data = df[df['strategy_name'] == selected_strategy].iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Performance Metrics")
                st.metric("Total Return", f"{strategy_data.get('total_return', 0):.2f}%")
                st.metric("Total Trades", strategy_data.get('total_trades', 0))
                st.metric("Win Rate", f"{strategy_data.get('win_rate', 0):.1f}%")
                st.metric("Profit Factor", f"{strategy_data.get('profit_factor', 0):.2f}")
            
            with col2:
                st.subheader("Risk Metrics")
                st.metric("Sharpe Ratio", f"{strategy_data.get('sharpe_ratio', 0):.2f}")
                st.metric("Max Drawdown", f"{strategy_data.get('max_drawdown', 0):.2f}%")
                st.metric("Avg Duration", strategy_data.get('avg_duration', 'N/A'))
                st.metric("Timeframe", strategy_data.get('detected_timeframe', 'N/A'))
            
            st.subheader("Configuration")
            st.write(f"**Date Range:** {strategy_data.get('start_date', 'N/A')} - {strategy_data.get('end_date', 'N/A')}")
            st.write(f"**Status:** {strategy_data.get('status', 'N/A')}")
            
            if strategy_data.get('error_message'):
                st.error(f"**Error:** {strategy_data['error_message']}")


if __name__ == "__main__":
    main()
