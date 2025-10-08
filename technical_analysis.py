"""
AIPS - Technical Analysis Module
Performs technical analysis with indicators and trend detection
"""

import logging
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
import ta
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator, VolumeWeightedAveragePrice

from utils import (
    get_indian_stock_symbol,
    calculate_percentage_change,
    get_date_range
)


class TechnicalAnalyzer:
    """Performs technical analysis on stock price data"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("AIPS.Technical")
    
    def analyze(self, symbol: str) -> Dict[str, Any]:
        """
        Perform comprehensive technical analysis
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Dictionary containing technical analysis results
        """
        self.logger.info(f"Starting technical analysis for {symbol}")
        
        symbol = get_indian_stock_symbol(
            symbol,
            self.config.get('market', {}).get('exchange', 'NSE')
        )
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Get historical data (1 year)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            hist_data = ticker.history(start=start_date, end=end_date)
            
            if hist_data.empty:
                raise ValueError("No historical data available")
            
            # Initialize analysis results
            analysis = {
                'symbol': symbol,
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                'data_points': len(hist_data),
            }
            
            # Calculate technical indicators
            indicators = self._calculate_indicators(hist_data)
            analysis.update(indicators)
            
            # Analyze trends
            trends = self._analyze_trends(hist_data)
            analysis.update(trends)
            
            # Identify support and resistance
            support_resistance = self._find_support_resistance(hist_data)
            analysis.update(support_resistance)
            
            # Analyze volume
            volume_analysis = self._analyze_volume(hist_data)
            analysis.update(volume_analysis)
            
            # Analyze volatility
            volatility = self._analyze_volatility(hist_data)
            analysis.update(volatility)
            
            # Generate trading signals
            signals = self._generate_signals(hist_data, indicators)
            analysis.update(signals)
            
            # Calculate technical score
            technical_score = self._calculate_technical_score(analysis)
            analysis['technical_score'] = technical_score
            
            # Generate technical insights
            insights = self._generate_insights(analysis, hist_data)
            analysis['insights'] = insights
            
            self.logger.info(f"Technical analysis complete for {symbol}: Score {technical_score:.2f}/10")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in technical analysis for {symbol}: {e}")
            return self._create_error_analysis(symbol, str(e))
    
    def _calculate_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all technical indicators"""
        indicators = {}
        
        try:
            close = data['Close']
            high = data['High']
            low = data['Low']
            volume = data['Volume']
            
            # Moving Averages
            ma_periods = self.config.get('technical_indicators', {}).get('moving_averages', [20, 50, 200])
            for period in ma_periods:
                if len(data) >= period:
                    sma = SMAIndicator(close=close, window=period)
                    indicators[f'sma_{period}'] = sma.sma_indicator().iloc[-1]
                    
                    ema = EMAIndicator(close=close, window=period)
                    indicators[f'ema_{period}'] = ema.ema_indicator().iloc[-1]
            
            # RSI
            rsi_period = self.config.get('technical_indicators', {}).get('rsi_period', 14)
            if len(data) >= rsi_period:
                rsi = RSIIndicator(close=close, window=rsi_period)
                indicators['rsi'] = rsi.rsi().iloc[-1]
                indicators['rsi_signal'] = self._interpret_rsi(indicators['rsi'])
            
            # MACD
            macd_fast = self.config.get('technical_indicators', {}).get('macd_fast', 12)
            macd_slow = self.config.get('technical_indicators', {}).get('macd_slow', 26)
            macd_signal = self.config.get('technical_indicators', {}).get('macd_signal', 9)
            
            if len(data) >= max(macd_fast, macd_slow, macd_signal):
                macd = MACD(close=close, window_slow=macd_slow, window_fast=macd_fast, window_sign=macd_signal)
                indicators['macd'] = macd.macd().iloc[-1]
                indicators['macd_signal_line'] = macd.macd_signal().iloc[-1]
                indicators['macd_histogram'] = macd.macd_diff().iloc[-1]
                indicators['macd_trend'] = 'Bullish' if indicators['macd_histogram'] > 0 else 'Bearish'
            
            # Bollinger Bands
            bb_period = self.config.get('technical_indicators', {}).get('bollinger_period', 20)
            bb_std = self.config.get('technical_indicators', {}).get('bollinger_std', 2)
            
            if len(data) >= bb_period:
                bb = BollingerBands(close=close, window=bb_period, window_dev=bb_std)
                indicators['bb_upper'] = bb.bollinger_hband().iloc[-1]
                indicators['bb_middle'] = bb.bollinger_mavg().iloc[-1]
                indicators['bb_lower'] = bb.bollinger_lband().iloc[-1]
                indicators['bb_width'] = bb.bollinger_wband().iloc[-1]
                
                current_price = close.iloc[-1]
                indicators['bb_position'] = self._interpret_bb_position(
                    current_price,
                    indicators['bb_upper'],
                    indicators['bb_middle'],
                    indicators['bb_lower']
                )
            
            # Stochastic Oscillator
            if len(data) >= 14:
                stoch = StochasticOscillator(high=high, low=low, close=close, window=14, smooth_window=3)
                indicators['stoch_k'] = stoch.stoch().iloc[-1]
                indicators['stoch_d'] = stoch.stoch_signal().iloc[-1]
                indicators['stoch_signal'] = self._interpret_stochastic(indicators['stoch_k'])
            
            # ATR (Average True Range)
            if len(data) >= 14:
                atr = AverageTrueRange(high=high, low=low, close=close, window=14)
                indicators['atr'] = atr.average_true_range().iloc[-1]
            
            # On-Balance Volume
            obv = OnBalanceVolumeIndicator(close=close, volume=volume)
            indicators['obv'] = obv.on_balance_volume().iloc[-1]
            
            # Current price info
            indicators['current_price'] = close.iloc[-1]
            indicators['previous_close'] = close.iloc[-2] if len(close) > 1 else close.iloc[-1]
            indicators['price_change'] = calculate_percentage_change(indicators['previous_close'], indicators['current_price'])
            
        except Exception as e:
            self.logger.warning(f"Error calculating indicators: {e}")
        
        return indicators
    
    def _analyze_trends(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price trends"""
        trends = {}
        
        try:
            close = data['Close']
            
            # Short-term trend (30 days)
            if len(data) >= 30:
                short_term_start = close.iloc[-30]
                short_term_end = close.iloc[-1]
                trends['short_term_trend'] = calculate_percentage_change(short_term_start, short_term_end)
                trends['short_term_direction'] = 'Uptrend' if trends['short_term_trend'] > 5 else ('Downtrend' if trends['short_term_trend'] < -5 else 'Sideways')
            
            # Medium-term trend (90 days)
            if len(data) >= 90:
                medium_term_start = close.iloc[-90]
                medium_term_end = close.iloc[-1]
                trends['medium_term_trend'] = calculate_percentage_change(medium_term_start, medium_term_end)
                trends['medium_term_direction'] = 'Uptrend' if trends['medium_term_trend'] > 10 else ('Downtrend' if trends['medium_term_trend'] < -10 else 'Sideways')
            
            # Long-term trend (365 days)
            if len(data) >= 365:
                long_term_start = close.iloc[0]
                long_term_end = close.iloc[-1]
                trends['long_term_trend'] = calculate_percentage_change(long_term_start, long_term_end)
                trends['long_term_direction'] = 'Uptrend' if trends['long_term_trend'] > 15 else ('Downtrend' if trends['long_term_trend'] < -15 else 'Sideways')
            
            # 52-week high/low analysis
            trends['52_week_high'] = close.max()
            trends['52_week_low'] = close.min()
            current_price = close.iloc[-1]
            trends['distance_from_high'] = ((current_price - trends['52_week_high']) / trends['52_week_high']) * 100
            trends['distance_from_low'] = ((current_price - trends['52_week_low']) / trends['52_week_low']) * 100
            
        except Exception as e:
            self.logger.warning(f"Error analyzing trends: {e}")
        
        return trends
    
    def _find_support_resistance(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Identify support and resistance levels"""
        support_resistance = {}
        
        try:
            close = data['Close']
            high = data['High']
            low = data['Low']
            
            # Use recent 6 months for support/resistance
            recent_data = data.tail(180) if len(data) > 180 else data
            
            # Find local minima (support) and maxima (resistance)
            window = 10
            supports = []
            resistances = []
            
            for i in range(window, len(recent_data) - window):
                # Support: local minimum
                if recent_data['Low'].iloc[i] == recent_data['Low'].iloc[i-window:i+window].min():
                    supports.append(recent_data['Low'].iloc[i])
                
                # Resistance: local maximum
                if recent_data['High'].iloc[i] == recent_data['High'].iloc[i-window:i+window].max():
                    resistances.append(recent_data['High'].iloc[i])
            
            # Get strongest levels (most tested)
            if supports:
                support_resistance['support_levels'] = sorted(set([round(s, 2) for s in supports]))[-3:]  # Top 3
                support_resistance['nearest_support'] = max([s for s in supports if s < close.iloc[-1]], default=np.nan)
            
            if resistances:
                support_resistance['resistance_levels'] = sorted(set([round(r, 2) for r in resistances]))[-3:]  # Top 3
                support_resistance['nearest_resistance'] = min([r for r in resistances if r > close.iloc[-1]], default=np.nan)
            
            # Calculate support/resistance strength
            current_price = close.iloc[-1]
            if 'nearest_support' in support_resistance and not pd.isna(support_resistance['nearest_support']):
                distance_to_support = ((current_price - support_resistance['nearest_support']) / current_price) * 100
                support_resistance['distance_to_support_%'] = round(distance_to_support, 2)
            
            if 'nearest_resistance' in support_resistance and not pd.isna(support_resistance['nearest_resistance']):
                distance_to_resistance = ((support_resistance['nearest_resistance'] - current_price) / current_price) * 100
                support_resistance['distance_to_resistance_%'] = round(distance_to_resistance, 2)
            
        except Exception as e:
            self.logger.warning(f"Error finding support/resistance: {e}")
        
        return support_resistance
    
    def _analyze_volume(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trading volume patterns"""
        volume_analysis = {}
        
        try:
            volume = data['Volume']
            close = data['Close']
            
            # Average volumes
            volume_analysis['avg_volume_30d'] = volume.tail(30).mean()
            volume_analysis['avg_volume_90d'] = volume.tail(90).mean() if len(data) >= 90 else volume.mean()
            
            # Current volume vs average
            current_volume = volume.iloc[-1]
            volume_analysis['current_volume'] = current_volume
            volume_analysis['volume_ratio'] = current_volume / volume_analysis['avg_volume_30d'] if volume_analysis['avg_volume_30d'] > 0 else np.nan
            
            # Volume trend
            if not pd.isna(volume_analysis['volume_ratio']):
                if volume_analysis['volume_ratio'] > 1.5:
                    volume_analysis['volume_signal'] = 'High Volume'
                elif volume_analysis['volume_ratio'] < 0.5:
                    volume_analysis['volume_signal'] = 'Low Volume'
                else:
                    volume_analysis['volume_signal'] = 'Normal Volume'
            
            # Liquidity check
            min_volume = self.config.get('risk_flags', {}).get('min_trading_volume', 10000)
            volume_analysis['is_liquid'] = volume_analysis['avg_volume_30d'] >= min_volume
            
            # Volume-Price correlation
            recent_data = data.tail(30)
            if len(recent_data) >= 10:
                volume_changes = recent_data['Volume'].pct_change()
                price_changes = recent_data['Close'].pct_change()
                correlation = volume_changes.corr(price_changes)
                volume_analysis['volume_price_correlation'] = correlation
            
        except Exception as e:
            self.logger.warning(f"Error analyzing volume: {e}")
        
        return volume_analysis
    
    def _analyze_volatility(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price volatility"""
        volatility = {}
        
        try:
            close = data['Close']
            returns = close.pct_change().dropna()
            
            # Historical volatility
            volatility['daily_volatility'] = returns.std() * 100
            volatility['annualized_volatility'] = returns.std() * np.sqrt(252) * 100
            
            # Recent vs historical volatility
            recent_volatility = returns.tail(30).std() * 100 if len(returns) >= 30 else volatility['daily_volatility']
            volatility['recent_volatility'] = recent_volatility
            
            # Volatility trend
            if volatility['daily_volatility'] > 0:
                vol_ratio = recent_volatility / volatility['daily_volatility']
                if vol_ratio > 1.2:
                    volatility['volatility_trend'] = 'Increasing'
                elif vol_ratio < 0.8:
                    volatility['volatility_trend'] = 'Decreasing'
                else:
                    volatility['volatility_trend'] = 'Stable'
            
            # ATR-based volatility categorization
            atr = data['High'] - data['Low']
            avg_atr = atr.mean()
            current_price = close.iloc[-1]
            volatility['atr_percentage'] = (avg_atr / current_price) * 100 if current_price > 0 else np.nan
            
        except Exception as e:
            self.logger.warning(f"Error analyzing volatility: {e}")
        
        return volatility
    
    def _generate_signals(self, data: pd.DataFrame, indicators: Dict) -> Dict[str, Any]:
        """Generate buy/sell/hold signals"""
        signals = {}
        
        try:
            signals_list = []
            
            # RSI signal
            rsi = indicators.get('rsi', np.nan)
            if not pd.isna(rsi):
                if rsi < 30:
                    signals_list.append('RSI: Oversold - Potential Buy')
                elif rsi > 70:
                    signals_list.append('RSI: Overbought - Potential Sell')
            
            # MACD signal
            macd_hist = indicators.get('macd_histogram', np.nan)
            if not pd.isna(macd_hist):
                if macd_hist > 0:
                    signals_list.append('MACD: Bullish')
                else:
                    signals_list.append('MACD: Bearish')
            
            # Moving average crossover
            current_price = indicators.get('current_price', np.nan)
            sma_50 = indicators.get('sma_50', np.nan)
            sma_200 = indicators.get('sma_200', np.nan)
            
            if not pd.isna(current_price) and not pd.isna(sma_50):
                if current_price > sma_50:
                    signals_list.append('Price above SMA50: Bullish')
                else:
                    signals_list.append('Price below SMA50: Bearish')
            
            if not pd.isna(sma_50) and not pd.isna(sma_200):
                if sma_50 > sma_200:
                    signals_list.append('Golden Cross: Strong Bullish')
                elif sma_50 < sma_200:
                    signals_list.append('Death Cross: Strong Bearish')
            
            # Volume signal
            volume_signal = indicators.get('volume_signal', '')
            if 'High Volume' in volume_signal:
                signals_list.append(f'Volume: {volume_signal}')
            
            signals['signals'] = signals_list
            
            # Overall signal
            bullish_count = sum(1 for s in signals_list if 'Bullish' in s or 'Buy' in s or 'Oversold' in s)
            bearish_count = sum(1 for s in signals_list if 'Bearish' in s or 'Sell' in s or 'Overbought' in s)
            
            if bullish_count > bearish_count + 1:
                signals['overall_signal'] = 'BUY'
            elif bearish_count > bullish_count + 1:
                signals['overall_signal'] = 'SELL'
            else:
                signals['overall_signal'] = 'HOLD'
            
        except Exception as e:
            self.logger.warning(f"Error generating signals: {e}")
        
        return signals
    
    def _calculate_technical_score(self, analysis: Dict) -> float:
        """Calculate technical score (0-10)"""
        score = 5.0  # Start with neutral
        
        try:
            # Trend score (max +3.0)
            short_trend = analysis.get('short_term_trend', 0)
            if short_trend > 10:
                score += 1.5
            elif short_trend > 5:
                score += 1.0
            elif short_trend < -10:
                score -= 1.5
            elif short_trend < -5:
                score -= 1.0
            
            medium_trend = analysis.get('medium_term_trend', 0)
            if medium_trend > 15:
                score += 1.5
            elif medium_trend > 10:
                score += 0.5
            elif medium_trend < -15:
                score -= 1.5
            elif medium_trend < -10:
                score -= 0.5
            
            # Momentum score (max +2.0)
            rsi = analysis.get('rsi', 50)
            if 40 <= rsi <= 60:
                score += 1.0
            elif rsi < 30:
                score += 0.5  # Oversold can be opportunity
            elif rsi > 70:
                score -= 1.0  # Overbought is risky
            
            macd_hist = analysis.get('macd_histogram', 0)
            if macd_hist > 0:
                score += 1.0
            else:
                score -= 0.5
            
            # Volume score (max +2.0)
            if analysis.get('is_liquid', False):
                score += 1.0
            else:
                score -= 2.0  # Illiquid stocks are very risky
            
            volume_ratio = analysis.get('volume_ratio', 1.0)
            if not pd.isna(volume_ratio):
                if 0.8 <= volume_ratio <= 1.5:
                    score += 0.5
                elif volume_ratio < 0.3:
                    score -= 1.0
            
            # Volatility score (max +1.5)
            volatility = analysis.get('annualized_volatility', 50)
            if not pd.isna(volatility):
                if 20 <= volatility <= 50:  # Moderate volatility
                    score += 1.0
                elif volatility < 15:  # Too low - might lack momentum
                    score += 0.5
                elif volatility > 80:  # Too high - risky
                    score -= 1.5
            
            # Position relative to 52-week range (max +1.5)
            distance_from_low = analysis.get('distance_from_low', 0)
            if not pd.isna(distance_from_low):
                if distance_from_low > 20:  # Not at bottom
                    score += 0.5
                if 30 <= distance_from_low <= 70:  # Mid-range
                    score += 0.5
                elif distance_from_low < 10:  # Near low - risky but potential
                    score += 0.5
            
            # Overall signal alignment
            overall_signal = analysis.get('overall_signal', 'HOLD')
            if overall_signal == 'BUY':
                score += 1.0
            elif overall_signal == 'SELL':
                score -= 1.0
            
        except Exception as e:
            self.logger.warning(f"Error calculating technical score: {e}")
        
        # Ensure score is within 0-10 range
        score = max(0.0, min(10.0, score))
        
        return round(score, 2)
    
    def _generate_insights(self, analysis: Dict, data: pd.DataFrame) -> List[str]:
        """Generate human-readable technical insights"""
        insights = []
        
        try:
            # Trend insights
            short_direction = analysis.get('short_term_direction', '')
            if short_direction:
                insights.append(f"Short-term: {short_direction}")
            
            # RSI insights
            rsi = analysis.get('rsi', np.nan)
            if not pd.isna(rsi):
                if rsi < 30:
                    insights.append(f"⚠ RSI at {rsi:.1f} - Oversold territory")
                elif rsi > 70:
                    insights.append(f"⚠ RSI at {rsi:.1f} - Overbought territory")
            
            # Volume insights
            if not analysis.get('is_liquid', False):
                insights.append("⚠ Low liquidity - Higher risk")
            
            volume_signal = analysis.get('volume_signal', '')
            if volume_signal == 'High Volume':
                insights.append("✓ High trading volume - Good liquidity")
            
            # Volatility insights
            vol_trend = analysis.get('volatility_trend', '')
            if vol_trend == 'Increasing':
                insights.append("⚠ Increasing volatility - Higher risk")
            
            # Signal insights
            overall_signal = analysis.get('overall_signal', 'HOLD')
            insights.append(f"Technical Signal: {overall_signal}")
            
            # Support/Resistance
            if 'distance_to_support_%' in analysis:
                dist = analysis['distance_to_support_%']
                if dist < 3:
                    insights.append(f"✓ Near support level ({dist:.1f}% away)")
            
            if 'distance_to_resistance_%' in analysis:
                dist = analysis['distance_to_resistance_%']
                if dist < 5:
                    insights.append(f"⚠ Approaching resistance ({dist:.1f}% away)")
            
        except Exception as e:
            self.logger.warning(f"Error generating insights: {e}")
        
        return insights
    
    def _interpret_rsi(self, rsi: float) -> str:
        """Interpret RSI value"""
        if pd.isna(rsi):
            return 'N/A'
        elif rsi > 70:
            return 'Overbought'
        elif rsi < 30:
            return 'Oversold'
        else:
            return 'Neutral'
    
    def _interpret_stochastic(self, stoch_k: float) -> str:
        """Interpret Stochastic value"""
        if pd.isna(stoch_k):
            return 'N/A'
        elif stoch_k > 80:
            return 'Overbought'
        elif stoch_k < 20:
            return 'Oversold'
        else:
            return 'Neutral'
    
    def _interpret_bb_position(self, price: float, upper: float, middle: float, lower: float) -> str:
        """Interpret Bollinger Band position"""
        try:
            if price > upper:
                return 'Above Upper Band - Overbought'
            elif price < lower:
                return 'Below Lower Band - Oversold'
            elif price > middle:
                return 'Above Middle - Bullish Zone'
            else:
                return 'Below Middle - Bearish Zone'
        except:
            return 'N/A'
    
    def _create_error_analysis(self, symbol: str, error: str) -> Dict[str, Any]:
        """Create error analysis when analysis fails"""
        return {
            'symbol': symbol,
            'error': error,
            'technical_score': 0.0,
            'insights': ['Data unavailable - technical analysis failed'],
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
        }
