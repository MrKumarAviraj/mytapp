"""
Charting Module
Creates interactive Plotly charts with pattern overlays.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Optional, Dict, List


def create_candlestick_chart(
    df: pd.DataFrame,
    title: str = "Price Chart",
    show_ema50: bool = False,
    show_volume: bool = True,
) -> go.Figure:
    """
    Create an interactive candlestick chart with volume.
    
    Args:
        df: DataFrame with OHLCV data
        title: Chart title
        show_ema50: Whether to show 50-period EMA
        show_volume: Whether to show volume bars
    
    Returns:
        Plotly Figure object
    """
    # Create subplots: main chart + optional volume
    if show_volume:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(title, "Volume")
        )
    else:
        fig = make_subplots(
            rows=1, cols=1,
            subplot_titles=(title,)
        )
    
    # Candlestick chart
    candlestick = go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="OHLC",
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350',
    )
    fig.add_trace(candlestick, row=1, col=1)
    
    # Add EMA50 if requested
    if show_ema50 and 'EMA50' in df.columns:
        ema_trace = go.Scatter(
            x=df.index,
            y=df['EMA50'],
            mode='lines',
            name='EMA(50)',
            line=dict(color='#ff9800', width=1.5),
        )
        fig.add_trace(ema_trace, row=1, col=1)
    
    # Volume bars
    if show_volume and 'Volume' in df.columns:
        colors = ['#26a69a' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#ef5350' 
                  for i in range(len(df))]
        
        volume_trace = go.Bar(
            x=df.index,
            y=df['Volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.7,
        )
        fig.add_trace(volume_trace, row=2, col=1)
    
    # Update layout
    fig.update_layout(
        height=700 if show_volume else 500,
        margin=dict(l=50, r=50, t=50, b=50),
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
    )
    
    # Update y-axis labels
    fig.update_yaxes(title_text="Price", row=1, col=1)
    if show_volume:
        fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    return fig


def draw_pattern_overlay(
    fig: go.Figure,
    df: pd.DataFrame,
    pattern_info: Dict,
    row: int = 1,
    col: int = 1,
) -> go.Figure:
    """
    Draw pattern lines/annotations on the chart.
    
    Args:
        fig: Existing Plotly figure
        df: DataFrame with price data
        pattern_info: Dict from pattern detector with pattern details
        row: Subplot row number
        col: Subplot column number
    
    Returns:
        Updated Plotly figure
    """
    pattern_name = pattern_info.get("pattern_name", "")
    start_idx = pattern_info.get("start_index", 0)
    end_idx = pattern_info.get("end_index", len(df) - 1)
    
    # Get price data for the pattern period
    subset = df.iloc[start_idx:end_idx+1]
    
    if len(subset) == 0:
        return fig
    
    highs = subset['High'].values
    lows = subset['Low'].values
    closes = subset['Close'].values
    
    # Draw pattern-specific annotations
    if pattern_name in ["head_and_shoulders", "inverse_head_shoulders"]:
        # Draw neckline
        if pattern_name == "head_and_shoulders":
            neckline_y = lows[len(lows)//3:len(lows)*2//3].min()
        else:
            neckline_y = highs[len(highs)//3:len(highs)*2//3].max()
        
        fig.add_shape(
            type="line",
            x0=subset.index[0],
            x1=subset.index[-1],
            y0=neckline_y,
            y1=neckline_y,
            line=dict(color="#2196f3", width=2, dash="dash"),
            row=row, col=col,
        )
        
        # Label
        fig.add_annotation(
            text=f"{pattern_name.replace('_', ' ').title()}",
            x=subset.index[len(subset)//2],
            y=neckline_y,
            showarrow=False,
            bgcolor="rgba(33, 150, 243, 0.7)",
            font_color="white",
            row=row, col=col,
        )
        
    elif pattern_name in ["double_top", "double_bottom"]:
        # Draw resistance/support level
        if pattern_name == "double_top":
            level_y = highs.max()
            label = "Resistance"
        else:
            level_y = lows.min()
            label = "Support"
        
        fig.add_shape(
            type="line",
            x0=subset.index[0],
            x1=subset.index[-1],
            y0=level_y,
            y1=level_y,
            line=dict(color="#ff5722", width=2, dash="dot"),
            row=row, col=col,
        )
        
        fig.add_annotation(
            text=f"{label} @ {level_y:.2f}",
            x=subset.index[-1],
            y=level_y,
            showarrow=True,
            arrowhead=2,
            bgcolor="rgba(255, 87, 34, 0.7)",
            font_color="white",
            row=row, col=col,
        )
        
    elif pattern_name in ["ascending_triangle", "descending_triangle", "symmetrical_triangle"]:
        # Draw trendlines
        if pattern_name == "ascending_triangle":
            # Flat top, rising bottom
            top_y = highs.max()
            slope = (lows[-1] - lows[0]) / len(lows)
            
            fig.add_shape(
                type="line",
                x0=subset.index[0],
                x1=subset.index[-1],
                y0=top_y,
                y1=top_y,
                line=dict(color="#4caf50", width=2),
                row=row, col=col,
            )
            
            fig.add_shape(
                type="line",
                x0=subset.index[0],
                x1=subset.index[-1],
                y0=lows[0],
                y1=lows[-1],
                line=dict(color="#4caf50", width=2, dash="dash"),
                row=row, col=col,
            )
            
        elif pattern_name == "descending_triangle":
            # Flat bottom, falling top
            bottom_y = lows.min()
            
            fig.add_shape(
                type="line",
                x0=subset.index[0],
                x1=subset.index[-1],
                y0=bottom_y,
                y1=bottom_y,
                line=dict(color="#f44336", width=2),
                row=row, col=col,
            )
            
            fig.add_shape(
                type="line",
                x0=subset.index[0],
                x1=subset.index[-1],
                y0=highs[0],
                y1=highs[-1],
                line=dict(color="#f44336", width=2, dash="dash"),
                row=row, col=col,
            )
        else:
            # Symmetrical - converging lines
            fig.add_shape(
                type="line",
                x0=subset.index[0],
                x1=subset.index[-1],
                y0=highs[0],
                y1=highs[-1],
                line=dict(color="#9c27b0", width=2),
                row=row, col=col,
            )
            
            fig.add_shape(
                type="line",
                x0=subset.index[0],
                x1=subset.index[-1],
                y0=lows[0],
                y1=lows[-1],
                line=dict(color="#9c27b0", width=2, dash="dash"),
                row=row, col=col,
            )
        
        fig.add_annotation(
            text=pattern_name.replace('_', ' ').title(),
            x=subset.index[len(subset)//2],
            y=(highs.max() + lows.min()) / 2,
            showarrow=False,
            bgcolor="rgba(156, 39, 176, 0.7)",
            font_color="white",
            row=row, col=col,
        )
        
    elif pattern_name in ["bull_flag", "bear_flag"]:
        # Highlight flag consolidation area
        flag_start = len(subset) // 3
        flag_high = highs[:flag_start].max()
        flag_low = lows[:flag_start].min()
        
        fig.add_shape(
            type="rect",
            x0=subset.index[flag_start],
            x1=subset.index[-1],
            y0=flag_low,
            y1=flag_high,
            fillcolor="rgba(255, 235, 59, 0.2)",
            line=dict(width=0),
            row=row, col=col,
        )
        
        fig.add_annotation(
            text=pattern_name.replace('_', ' ').title(),
            x=subset.index[-1],
            y=(flag_high + flag_low) / 2,
            showarrow=False,
            bgcolor="rgba(255, 235, 59, 0.7)",
            font_color="black",
            row=row, col=col,
        )
        
    elif pattern_name in ["bullish_engulfing", "bearish_engulfing"]:
        # Highlight the two-candle pattern
        if len(subset) >= 2:
            last_two = subset.tail(2)
            fig.add_shape(
                type="rect",
                x0=last_two.index[0],
                x1=last_two.index[-1],
                y0=last_two['Low'].min(),
                y1=last_two['High'].max(),
                fillcolor="rgba(76, 175, 80, 0.2)" if pattern_name == "bullish_engulfing" else "rgba(244, 67, 54, 0.2)",
                line=dict(width=2, color="green" if pattern_name == "bullish_engulfing" else "red"),
                row=row, col=col,
            )
            
            fig.add_annotation(
                text=pattern_name.replace('_', ' ').title(),
                x=last_two.index[-1],
                y=last_two['High'].max(),
                showarrow=True,
                arrowhead=2,
                bgcolor="rgba(76, 175, 80, 0.7)" if pattern_name == "bullish_engulfing" else "rgba(244, 67, 54, 0.7)",
                font_color="white",
                row=row, col=col,
            )
    
    return fig


def draw_manual_pattern(
    fig: go.Figure,
    df: pd.DataFrame,
    pattern_name: str,
    window_size: int = 60,
    row: int = 1,
    col: int = 1,
) -> go.Figure:
    """
    Draw an idealized manual pattern overlay on recent price data.
    
    Args:
        fig: Existing Plotly figure
        df: DataFrame with price data
        pattern_name: Name of pattern to draw
        window_size: Number of candles to analyze
        row: Subplot row number
        col: Subplot column number
    
    Returns:
        Updated Plotly figure
    """
    subset = df.tail(window_size)
    
    if len(subset) < 10:
        return fig
    
    highs = subset['High'].values
    lows = subset['Low'].values
    closes = subset['Close'].values
    
    # Draw idealized pattern based on type
    if pattern_name == "head_and_shoulders":
        # Draw idealized H&S shape
        peak_idx = len(subset) // 2
        peak_price = highs.max()
        shoulder_price = peak_price * 0.85
        
        # Left shoulder
        fig.add_shape(
            type="line",
            x0=subset.index[0],
            x1=subset.index[peak_idx//2],
            y0=closes[0],
            y1=shoulder_price,
            line=dict(color="#2196f3", width=2, dash="dash"),
            row=row, col=col,
        )
        
        # Head
        fig.add_shape(
            type="line",
            x0=subset.index[peak_idx//2],
            x1=subset.index[peak_idx],
            y0=shoulder_price,
            y1=peak_price,
            line=dict(color="#2196f3", width=2),
            row=row, col=col,
        )
        
        # Right shoulder
        fig.add_shape(
            type="line",
            x0=subset.index[peak_idx],
            x1=subset.index[-1],
            y0=peak_price,
            y1=shoulder_price,
            line=dict(color="#2196f3", width=2, dash="dash"),
            row=row, col=col,
        )
        
    elif pattern_name == "double_bottom":
        # Draw W shape
        trough_price = lows.min()
        peak_price = highs.max()
        
        mid_idx = len(subset) // 2
        
        fig.add_shape(
            type="line",
            x0=subset.index[0],
            x1=subset.index[mid_idx//2],
            y0=closes[0],
            y1=trough_price,
            line=dict(color="#ff5722", width=2),
            row=row, col=col,
        )
        
        fig.add_shape(
            type="line",
            x0=subset.index[mid_idx//2],
            x1=subset.index[mid_idx],
            y0=trough_price,
            y1=peak_price,
            line=dict(color="#ff5722", width=2),
            row=row, col=col,
        )
        
        fig.add_shape(
            type="line",
            x0=subset.index[mid_idx],
            x1=subset.index[mid_idx + mid_idx//2],
            y0=peak_price,
            y1=trough_price,
            line=dict(color="#ff5722", width=2),
            row=row, col=col,
        )
        
        fig.add_shape(
            type="line",
            x0=subset.index[mid_idx + mid_idx//2],
            x1=subset.index[-1],
            y0=trough_price,
            y1=closes[-1],
            line=dict(color="#ff5722", width=2),
            row=row, col=col,
        )
    
    # Add label
    fig.add_annotation(
        text=f"Manual: {pattern_name.replace('_', ' ').title()}",
        x=subset.index[-1],
        y=closes[-1],
        showarrow=True,
        arrowhead=2,
        bgcolor="rgba(156, 39, 176, 0.8)",
        font_color="white",
        row=row, col=col,
    )
    
    return fig
