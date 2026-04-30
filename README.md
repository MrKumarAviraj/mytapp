# 📊 Technical Pattern Analyzer

An educational web application for visualizing, studying, and backtesting classic technical chart patterns.

## ⚠️ Disclaimer

**This tool is for educational purposes only. Not financial advice.**

Pattern recognition is a probabilistic context tool, not a crystal ball. Past performance does not guarantee future results.

## Features

- **Pattern Detection**: Algorithmically scans for 10 classic chart patterns
- **Confidence Scoring**: 3-layer scoring system (structural rules, template correlation, confirmation filters)
- **Historical Validation**: Win rates based on historical occurrences
- **Interactive Charts**: Candlestick charts with pattern overlays
- **Manual Overlay**: Compare idealized patterns against actual price action
- **Multiple Timeframes**: Daily, 4-hour, 1-hour, 15-minute intervals

## Supported Patterns

### Reversal Patterns
- Head & Shoulders
- Inverse Head & Shoulders
- Double Top
- Double Bottom
- Bullish Engulfing
- Bearish Engulfing

### Continuation Patterns
- Ascending Triangle
- Descending Triangle
- Symmetrical Triangle
- Bull Flag
- Bear Flag

## Tech Stack

- **Language**: Python 3.10+
- **Frontend**: Streamlit
- **Data Source**: yfinance (Yahoo Finance)
- **Pattern Engine**: pandas, numpy, scipy, ta
- **Charting**: plotly

## Installation

### Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd ta-pattern-analyzer
