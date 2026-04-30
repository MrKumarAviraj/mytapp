"""
Pattern Engine Module
Detects technical chart patterns using a 3-layer scoring system.
"""

import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from scipy.stats import pearsonr
from typing import Optional, Dict, List, Tuple
import ta


class PatternDetector:
    """
    Detects and scores technical chart patterns.
    
    Scoring System:
    1. Structural Rule Filter (Pass/Fail)
    2. Template Correlation (0-100)
    3. Confirmation Filters (+/- modifiers)
    """
    
    # Pattern templates (idealized shapes normalized to 0-1)
    PATTERN_TEMPLATES = {
        "head_and_shoulders": np.array([0.3, 0.5, 0.9, 0.5, 0.3]),
        "inverse_head_shoulders": np.array([0.7, 0.5, 0.1, 0.5, 0.7]),
        "double_top": np.array([0.3, 0.5, 0.85, 0.5, 0.85, 0.5, 0.3]),
        "double_bottom": np.array([0.7, 0.5, 0.15, 0.5, 0.15, 0.5, 0.7]),
        "ascending_triangle": np.array([0.3, 0.4, 0.5, 0.6, 0.7, 0.7, 0.7, 0.7]),
        "descending_triangle": np.array([0.7, 0.6, 0.5, 0.4, 0.3, 0.3, 0.3, 0.3]),
        "symmetrical_triangle": np.array([0.3, 0.4, 0.5, 0.6, 0.5, 0.4, 0.3]),
        "bull_flag": np.array([0.7, 0.3, 0.4, 0.35, 0.3, 0.25, 0.2]),
        "bear_flag": np.array([0.3, 0.7, 0.6, 0.65, 0.7, 0.75, 0.8]),
        "bullish_engulfing": np.array([0.6, 0.4, 0.2, 0.8]),
        "bearish_engulfing": np.array([0.4, 0.6, 0.8, 0.2]),
    }
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with OHLCV DataFrame.
        
        Args:
            df: DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
        """
        self.df = df.copy()
        self.df = self._add_technical_indicators(self.df)
        
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add EMA, ATR, and other indicators for confirmation filters."""
        df = df.copy()
        
        # EMA 50 for trend detection
        if len(df) >= 50:
            df['EMA50'] = ta.trend.ema_indicator(df['Close'], window=50)
        else:
            df['EMA50'] = df['Close']
        
        # ATR for volatility
        df['ATR'] = ta.volatility.average_true_range(
            df['High'], df['Low'], df['Close'], window=14
        )
        
        # Bollinger Bands for volatility regime
        bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
        df['BB_upper'] = bb.bollinger_hband()
        df['BB_lower'] = bb.bollinger_lband()
        df['BB_width'] = (df['BB_upper'] - df['BB_lower']) / df['Close']
        
        return df
    
    def _find_swing_points(self, prices: np.ndarray, order: int = 5) -> Tuple[List[int], List[int]]:
        """
        Find swing highs and lows in price data.
        
        Args:
            prices: Array of prices (typically High or Low)
            order: Number of points on each side to compare
        
        Returns:
            Tuple of (swing_high_indices, swing_low_indices)
        """
        # Use scipy's find_peaks for swing detection
        swing_highs, _ = find_peaks(prices, distance=order)
        swing_lows, _ = find_peaks(-prices, distance=order)
        
        return list(swing_highs), list(swing_lows)
    
    def _normalize_prices(self, prices: np.ndarray) -> np.ndarray:
        """Normalize prices to 0-1 range."""
        min_p, max_p = prices.min(), prices.max()
        if max_p - min_p == 0:
            return np.zeros_like(prices)
        return (prices - min_p) / (max_p - min_p)
    
    def _calculate_correlation(self, actual: np.ndarray, template: np.ndarray) -> float:
        """
        Calculate correlation between actual price pattern and template.
        Uses Pearson correlation or DTW-like alignment.
        """
        if len(actual) != len(template):
            # Resample actual to match template length
            from scipy.interpolate import interp1d
            x_old = np.linspace(0, 1, len(actual))
            x_new = np.linspace(0, 1, len(template))
            f = interp1d(x_old, actual, kind='linear')
            actual_resampled = f(x_new)
            actual = actual_resampled
        
        try:
            corr, _ = pearsonr(actual, template)
            return max(0, min(1, corr)) * 100
        except:
            return 0
    
    def _check_structural_rules(self, pattern_name: str, start_idx: int, end_idx: int) -> bool:
        """
        Check structural rules for a pattern.
        
        Returns True if pattern passes basic structural requirements.
        """
        subset = self.df.iloc[start_idx:end_idx+1]
        
        if len(subset) < 5:
            return False
        
        highs = subset['High'].values
        lows = subset['Low'].values
        closes = subset['Close'].values
        
        if pattern_name in ["head_and_shoulders", "inverse_head_shoulders"]:
            # Need at least 3 swing points
            swing_highs, swing_lows = self._find_swing_points(highs if pattern_name == "head_and_shoulders" else -lows)
            return len(swing_highs) >= 3 or len(swing_lows) >= 3
            
        elif pattern_name in ["double_top", "double_bottom"]:
            # Two peaks/troughs within 15% tolerance
            if pattern_name == "double_top":
                swing_highs, _ = self._find_swing_points(highs)
                if len(swing_highs) >= 2:
                    peak1, peak2 = highs[swing_highs[-2]], highs[swing_highs[-1]]
                    return abs(peak1 - peak2) / max(peak1, peak2) <= 0.15
            else:
                _, swing_lows = self._find_swing_points(-lows)
                if len(swing_lows) >= 2:
                    trough1, trough2 = lows[swing_lows[-2]], lows[swing_lows[-1]]
                    return abs(trough1 - trough2) / max(trough1, trough2) <= 0.15
            return False
            
        elif pattern_name in ["ascending_triangle", "descending_triangle", "symmetrical_triangle"]:
            # Check for converging trendlines
            if pattern_name == "ascending_triangle":
                # Higher lows, flat highs
                return lows[-1] > lows[len(lows)//2] and abs(highs[-1] - highs.max()) / highs.max() < 0.1
            elif pattern_name == "descending_triangle":
                # Lower highs, flat lows
                return highs[-1] < highs[len(highs)//2] and abs(lows[-1] - lows.min()) / lows.min() < 0.1
            else:
                # Converging highs and lows
                return (highs[-1] < highs[len(highs)//2]) and (lows[-1] > lows[len(lows)//2])
                
        elif pattern_name in ["bull_flag", "bear_flag"]:
            # Sharp move followed by consolidation
            if pattern_name == "bull_flag":
                pole = (closes[len(closes)//2] - closes[0]) / closes[0]
                flag = abs(closes[-1] - closes[len(closes)//2]) / closes[len(closes)//2]
                return pole > 0.05 and flag < 0.03
            else:
                pole = (closes[0] - closes[len(closes)//2]) / closes[0]
                flag = abs(closes[-1] - closes[len(closes)//2]) / closes[len(closes)//2]
                return pole > 0.05 and flag < 0.03
                
        elif pattern_name in ["bullish_engulfing", "bearish_engulfing"]:
            # 2-candle pattern
            if len(closes) >= 2:
                opens = subset['Open'].values
                if pattern_name == "bullish_engulfing":
                    return (closes[-2] < opens[-2]) and \
                           (closes[-1] > closes[-2] and closes[-1] > opens[-2])
                else:
                    return (len(closes) > 2 and closes[-2] > closes[-3]) and \
                           (closes[-1] < closes[-2] and closes[-1] < opens[-2])
            return False
        
        return True
    
    def _apply_confirmation_filters(self, pattern_name: str, start_idx: int, end_idx: int) -> int:
        """
        Apply confirmation filters for +/- score modifiers.
        
        Returns score adjustment (-15 to +15).
        """
        score = 0
        subset = self.df.iloc[start_idx:end_idx+1]
        
        if len(subset) < 2:
            return 0
        
        # Volume expansion on breakout (last candle vs average)
        if 'Volume' in subset.columns:
            avg_vol = subset['Volume'].iloc[:-1].mean()
            last_vol = subset['Volume'].iloc[-1]
            if last_vol > avg_vol * 1.5:
                score += 10
        
        # Trend alignment (EMA50 slope)
        if 'EMA50' in subset.columns and len(subset) >= 10:
            ema_start = subset['EMA50'].iloc[max(0, len(subset)-10)]
            ema_end = subset['EMA50'].iloc[-1]
            ema_slope = (ema_end - ema_start) / ema_start
            
            bullish_patterns = ["bull_flag", "ascending_triangle", "inverse_head_shoulders", "bullish_engulfing"]
            bearish_patterns = ["bear_flag", "descending_triangle", "head_and_shoulders", "bearish_engulfing"]
            
            if pattern_name in bullish_patterns and ema_slope > 0:
                score += 5
            elif pattern_name in bearish_patterns and ema_slope < 0:
                score += 5
        
        # Volatility penalty (choppy market)
        if 'BB_width' in subset.columns:
            avg_bb_width = subset['BB_width'].mean()
            if avg_bb_width < 0.02:  # Very low volatility
                score -= 15
        
        return score
    
    def detect_pattern(self, pattern_name: str, window_size: int = 60) -> Optional[Dict]:
        """
        Detect a specific pattern in recent data.
        
        Args:
            pattern_name: Name of pattern to detect
            window_size: Number of candles to analyze
        
        Returns:
            Dict with pattern details or None if not found
        """
        if pattern_name not in self.PATTERN_TEMPLATES:
            return None
        
        template = self.PATTERN_TEMPLATES[pattern_name]
        df_subset = self.df.tail(window_size)
        
        if len(df_subset) < len(template):
            return None
        
        # Get price series (use Close for simplicity, could use High/Low for some patterns)
        prices = df_subset['Close'].values
        normalized_prices = self._normalize_prices(prices)
        
        # Calculate correlation score
        correlation_score = self._calculate_correlation(normalized_prices, template)
        
        # Check structural rules
        start_idx = len(self.df) - window_size
        end_idx = len(self.df) - 1
        
        if not self._check_structural_rules(pattern_name, start_idx, end_idx):
            return None
        
        # Apply confirmation filters
        confirmation_score = self._apply_confirmation_filters(pattern_name, start_idx, end_idx)
        
        # Calculate final confidence score
        confidence = correlation_score * 0.7 + confirmation_score + 30  # Base score of 30
        
        # Only return if confidence >= 60
        if confidence < 60:
            return None
        
        return {
            "pattern_name": pattern_name,
            "confidence": round(confidence, 1),
            "correlation_score": round(correlation_score, 1),
            "confirmation_score": confirmation_score,
            "start_index": start_idx,
            "end_index": end_idx,
            "start_date": df_subset.index[0],
            "end_date": df_subset.index[-1],
            "price_range": (prices.min(), prices.max()),
        }
    
    def detect_all_patterns(self, window_size: int = 60) -> List[Dict]:
        """
        Detect all supported patterns in recent data.
        
        Args:
            window_size: Number of candles to analyze
        
        Returns:
            List of detected patterns sorted by confidence
        """
        detected = []
        
        for pattern_name in self.PATTERN_TEMPLATES.keys():
            result = self.detect_pattern(pattern_name, window_size)
            if result:
                detected.append(result)
        
        # Sort by confidence descending
        detected.sort(key=lambda x: x['confidence'], reverse=True)
        
        return detected
