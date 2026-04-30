"""
Main Streamlit Application
Technical Pattern Analysis Educational App
"""

import streamlit as st
import pandas as pd
from data_fetcher import fetch_ohlcv_data, get_timeframe_params
from pattern_engine import PatternDetector
from validation import PatternValidator
from charting import create_candlestick_chart, draw_pattern_overlay, draw_manual_pattern


# Page configuration
st.set_page_config(
    page_title="Technical Pattern Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
<style>
    .disclaimer-banner {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application function."""
    
    # Header with disclaimer
    st.title("📊 Technical Pattern Analyzer")
    st.markdown("""
    **Educational Tool for Chart Pattern Recognition & Analysis**
    
    <div class="disclaimer-banner">
    ⚠️ <strong>Educational Purposes Only - Not Financial Advice</strong><br>
    This tool is for educational and analytical purposes only. Pattern recognition is a 
    probabilistic context tool, not a crystal ball. Past performance does not guarantee 
    future results. Always do your own research and consult with a qualified financial 
    advisor before making any trading decisions.
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar controls
    st.sidebar.header("🔍 Search Settings")
    
    # Ticker input
    ticker = st.sidebar.text_input(
        "Ticker Symbol",
        value="AAPL",
        help="Enter stock symbol (e.g., AAPL, MSFT, SPY)"
    )
    
    # Timeframe selection
    timeframe = st.sidebar.selectbox(
        "Timeframe",
        options=["1D", "4H", "1H", "15M"],
        index=0,
        help="Select chart timeframe"
    )
    
    # Advanced options
    st.sidebar.subheader("Chart Options")
    show_ema50 = st.sidebar.checkbox("Show EMA(50)", value=True)
    show_volume = st.sidebar.checkbox("Show Volume", value=True)
    
    # Manual pattern overlay
    st.sidebar.subheader("Manual Pattern Overlay")
    manual_pattern_options = [
        "None",
        "Head & Shoulders",
        "Inverse Head & Shoulders",
        "Double Top",
        "Double Bottom",
        "Ascending Triangle",
        "Descending Triangle",
        "Symmetrical Triangle",
        "Bull Flag",
        "Bear Flag",
        "Bullish Engulfing",
        "Bearish Engulfing",
    ]
    manual_pattern = st.sidebar.selectbox(
        "Apply Manual Pattern",
        options=manual_pattern_options,
        index=0,
        help="Overlay an idealized pattern shape for comparison"
    )
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Main content area
    if ticker:
        try:
            # Fetch data
            period, interval = get_timeframe_params(timeframe)
            
            with st.spinner(f"Fetching data for {ticker}..."):
                df, is_cached = fetch_ohlcv_data(ticker, period=period, interval=interval)
            
            # Show cache warning if applicable
            if is_cached:
                st.info("📦 Showing cached data (live data temporarily unavailable)")
            
            if df.empty or len(df) < 30:
                st.error(f"Insufficient data for {ticker}. Please try a different ticker or timeframe.")
                return
            
            # Initialize pattern detector and validator
            detector = PatternDetector(df)
            validator = PatternValidator(df)
            
            # Detect patterns
            with st.spinner("🔍 Scanning for patterns..."):
                detected_patterns = detector.detect_all_patterns(window_size=60)
            
            # Two-column layout for chart and results
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📈 Price Chart")
                
                # Create base chart
                fig = create_candlestick_chart(
                    df,
                    title=f"{ticker} ({timeframe})",
                    show_ema50=show_ema50,
                    show_volume=show_volume,
                )
                
                # Draw manual pattern if selected
                if manual_pattern != "None":
                    pattern_name_map = {
                        "Head & Shoulders": "head_and_shoulders",
                        "Inverse Head & Shoulders": "inverse_head_shoulders",
                        "Double Top": "double_top",
                        "Double Bottom": "double_bottom",
                        "Ascending Triangle": "ascending_triangle",
                        "Descending Triangle": "descending_triangle",
                        "Symmetrical Triangle": "symmetrical_triangle",
                        "Bull Flag": "bull_flag",
                        "Bear Flag": "bear_flag",
                        "Bullish Engulfing": "bullish_engulfing",
                        "Bearish Engulfing": "bearish_engulfing",
                    }
                    internal_name = pattern_name_map.get(manual_pattern, "")
                    if internal_name:
                        fig = draw_manual_pattern(fig, df, internal_name, window_size=60)
                
                # Draw detected pattern if one is selected
                if detected_patterns:
                    # Store selected pattern in session state
                    if 'selected_pattern' not in st.session_state:
                        st.session_state.selected_pattern = detected_patterns[0]
                    
                    # Let user select which pattern to display
                    pattern_options = [p['pattern_name'].replace('_', ' ').title() for p in detected_patterns]
                    selected_display = st.selectbox(
                        "Display Pattern on Chart",
                        options=pattern_options,
                        index=0,
                        key="pattern_selector"
                    )
                    
                    # Find the corresponding pattern data
                    selected_internal = selected_display.lower().replace(' ', '_')
                    selected_pattern_data = next(
                        (p for p in detected_patterns if p['pattern_name'] == selected_internal),
                        None
                    )
                    
                    if selected_pattern_data:
                        fig = draw_pattern_overlay(fig, df, selected_pattern_data)
                        st.session_state.selected_pattern = selected_pattern_data
                
                # Display chart
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("🎯 Detected Patterns")
                
                if detected_patterns:
                    # Create results table
                    results_data = []
                    for pattern in detected_patterns:
                        pattern_name = pattern['pattern_name'].replace('_', ' ').title()
                        confidence = pattern['confidence']
                        
                        # Get win rate stats
                        stats = validator.get_pattern_stats(pattern['pattern_name'])
                        win_rate = stats.get('win_rate', 'N/A')
                        sample_size = stats.get('sample_size', 0)
                        
                        # Format win rate display
                        if win_rate is not None:
                            win_rate_str = f"{win_rate}%"
                            tooltip = f"Based on {sample_size} historical occurrences"
                        else:
                            win_rate_str = "N/A"
                            tooltip = stats.get('note', 'Insufficient data')
                        
                        results_data.append({
                            "Pattern": pattern_name,
                            "Confidence": confidence,
                            "Win Rate": win_rate_str,
                            "Sample Size": sample_size,
                        })
                    
                    # Display as table
                    results_df = pd.DataFrame(results_data)
                    st.dataframe(
                        results_df,
                        use_container_width=True,
                        hide_index=True,
                    )
                    
                    # Show detailed stats for top pattern
                    if detected_patterns:
                        top_pattern = detected_patterns[0]
                        st.divider()
                        st.markdown("### 📊 Pattern Details")
                        
                        pattern_name_readable = top_pattern['pattern_name'].replace('_', ' ').title()
                        st.markdown(f"**{pattern_name_readable}**")
                        
                        # Confidence breakdown
                        st.metric(
                            "Confidence Score",
                            f"{top_pattern['confidence']}/100",
                            help="Algorithmic match quality + volume/trend confirmation"
                        )
                        
                        # Win rate info
                        stats = validator.get_pattern_stats(top_pattern['pattern_name'])
                        if stats.get('win_rate'):
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric(
                                    "Historical Win Rate",
                                    f"{stats['win_rate']}%",
                                    help=f"Based on {stats['sample_size']} occurrences since 2019"
                                )
                            with col_b:
                                if stats.get('avg_return'):
                                    st.metric(
                                        "Avg Expected Move",
                                        f"±{abs(stats['avg_return']):.2f}%",
                                        help="Average price movement after pattern completion"
                                    )
                        
                        # Pattern context
                        if stats.get('pattern_context'):
                            ctx = stats['pattern_context']
                            st.info(
                                f"**Type:** {ctx.get('type', 'N/A').title()}  \n"
                                f"**Direction:** {ctx.get('direction', 'N/A').title()}  \n"
                                f"**Typical Reliability:** {ctx.get('typical_reliability', 'N/A').title()}"
                            )
                else:
                    st.info("No high-confidence patterns detected (threshold: 60/100).")
                    st.markdown("""
                    **What does this mean?**
                    
                    The algorithm scans for recognizable chart patterns but requires:
                    - Clear structural formation (swing points, trendlines)
                    - Minimum correlation with idealized templates
                    - Confirmation from volume/trend indicators
                    
                    No patterns meeting these criteria were found in recent data.
                    Try adjusting the timeframe or checking a different ticker.
                    """)
            
            # Historical validation section
            st.divider()
            st.subheader("📚 Historical Pattern Statistics")
            
            # Show stats for all supported patterns
            pattern_list = [
                "head_and_shoulders", "inverse_head_shoulders", "double_top",
                "double_bottom", "ascending_triangle", "descending_triangle",
                "symmetrical_triangle", "bull_flag", "bear_flag",
                "bullish_engulfing", "bearish_engulfing"
            ]
            
            stats_cols = st.columns(3)
            for i, pattern_name in enumerate(pattern_list[:6]):  # Show first 6
                with stats_cols[i % 3]:
                    stats = validator.get_pattern_stats(pattern_name)
                    pattern_readable = pattern_name.replace('_', ' ').title()
                    
                    win_rate = stats.get('win_rate', 'N/A')
                    sample_size = stats.get('sample_size', 0)
                    
                    if win_rate is not None:
                        st.metric(
                            pattern_readable,
                            f"{win_rate}%",
                            help=f"Sample: {sample_size} occurrences"
                        )
                    else:
                        st.write(f"**{pattern_readable}**: Insufficient data")
            
            # Footer with disclaimers
            st.divider()
            st.markdown("""
            <div style="text-align: center; color: #666; font-size: 0.9em;">
            <p>
            <strong>⚠️ Important Disclaimers:</strong><br>
            • Patterns are identified algorithmically and may not match manual analyst drawings.<br>
            • Win rates are historical tendencies, not future guarantees.<br>
            • This tool does not predict future prices or provide trading signals.<br>
            • Price data via Yahoo Finance. Pattern logic inspired by Bulkowski, Murphy, & standard TA literature.<br>
            • For educational purposes only. Not financial advice.
            </p>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error loading data for {ticker}: {str(e)}")
            st.info("Please check the ticker symbol and try again.")
    else:
        st.info("👈 Enter a ticker symbol in the sidebar to begin analysis")
    
    # About section in expandable box
    with st.expander("ℹ️ About This Tool"):
        st.markdown("""
        ### Technical Pattern Analyzer - Educational Tool
        
        **Purpose:** Help users visualize, study, and understand classic technical chart patterns.
        
        **How It Works:**
        1. **Data Fetching:** Retrieves historical OHLCV data from Yahoo Finance
        2. **Pattern Detection:** Uses algorithmic scanning with 3-layer scoring:
           - Structural rule filters (pass/fail)
           - Template correlation (0-100 score)
           - Confirmation filters (volume, trend alignment)
        3. **Validation:** Calculates historical win rates from past occurrences
        4. **Visualization:** Interactive charts with pattern overlays
        
        **Supported Patterns:**
        - Reversal: Head & Shoulders, Double Top/Bottom, Engulfing candles
        - Continuation: Triangles, Flags
        
        **Methodology:**
        - Minimum confidence threshold: 60/100
        - Minimum sample size for win rates: 30 occurrences
        - Walk-forward validation approach
        
        **Built with:** Python, Streamlit, yfinance, pandas, scipy, plotly, ta
        
        ---
        *This is an educational tool only. Trading involves substantial risk of loss.*
        """)


if __name__ == "__main__":
    main()
