"""
AIPS - Fundamental Analysis Module
Analyzes financial statements and computes key financial metrics
"""

import logging
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from utils import (
    format_indian_currency,
    calculate_percentage_change,
    safe_divide,
    calculate_cagr,
    clean_numeric_value,
    get_indian_stock_symbol
)


class FundamentalAnalyzer:
    """Analyzes fundamental financial data for stocks"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("AIPS.Fundamental")
    
    def analyze(self, symbol: str) -> Dict[str, Any]:
        """
        Perform comprehensive fundamental analysis
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Dictionary containing fundamental analysis results
        """
        self.logger.info(f"Starting fundamental analysis for {symbol}")
        
        symbol = get_indian_stock_symbol(
            symbol,
            self.config.get('market', {}).get('exchange', 'NSE')
        )
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Initialize analysis results
            analysis = {
                'symbol': symbol,
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            }
            
            # Get key financial metrics
            metrics = self._extract_key_metrics(info)
            analysis.update(metrics)
            
            # Analyze financial statements
            financials = self._analyze_financials(ticker)
            analysis.update(financials)
            
            # Analyze profitability
            profitability = self._analyze_profitability(info)
            analysis.update(profitability)
            
            # Analyze financial health
            health = self._analyze_financial_health(info)
            analysis.update(health)
            
            # Analyze valuation
            valuation = self._analyze_valuation(info)
            analysis.update(valuation)
            
            # Analyze dividends
            dividends = self._analyze_dividends(ticker, info)
            analysis.update(dividends)
            
            # Calculate trends
            trends = self._analyze_trends(ticker)
            analysis.update(trends)
            
            # Calculate fundamental score
            fundamental_score = self._calculate_fundamental_score(analysis)
            analysis['fundamental_score'] = fundamental_score
            
            # Generate insights
            insights = self._generate_insights(analysis)
            analysis['insights'] = insights
            
            self.logger.info(f"Fundamental analysis complete for {symbol}: Score {fundamental_score:.2f}/10")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in fundamental analysis for {symbol}: {e}")
            return self._create_error_analysis(symbol, str(e))
    
    def _extract_key_metrics(self, info: Dict) -> Dict[str, Any]:
        """Extract key financial metrics"""
        return {
            'market_cap': info.get('marketCap', np.nan),
            'enterprise_value': info.get('enterpriseValue', np.nan),
            'trailing_pe': info.get('trailingPE', np.nan),
            'forward_pe': info.get('forwardPE', np.nan),
            'peg_ratio': info.get('pegRatio', np.nan),
            'price_to_book': info.get('priceToBook', np.nan),
            'price_to_sales': info.get('priceToSalesTrailing12Months', np.nan),
            'enterprise_to_revenue': info.get('enterpriseToRevenue', np.nan),
            'enterprise_to_ebitda': info.get('enterpriseToEbitda', np.nan),
            'book_value': info.get('bookValue', np.nan),
            'beta': info.get('beta', np.nan),
        }
    
    def _analyze_financials(self, ticker) -> Dict[str, Any]:
        """Analyze income statement, balance sheet, and cash flow"""
        financials = {}
        
        try:
            # Income Statement
            income_stmt = ticker.income_stmt
            if income_stmt is not None and not income_stmt.empty:
                latest_col = income_stmt.columns[0]
                
                financials['total_revenue'] = income_stmt.loc['Total Revenue', latest_col] if 'Total Revenue' in income_stmt.index else np.nan
                financials['gross_profit'] = income_stmt.loc['Gross Profit', latest_col] if 'Gross Profit' in income_stmt.index else np.nan
                financials['operating_income'] = income_stmt.loc['Operating Income', latest_col] if 'Operating Income' in income_stmt.index else np.nan
                financials['net_income'] = income_stmt.loc['Net Income', latest_col] if 'Net Income' in income_stmt.index else np.nan
                financials['ebitda'] = income_stmt.loc['EBITDA', latest_col] if 'EBITDA' in income_stmt.index else np.nan
                
                # Calculate margins
                revenue = financials.get('total_revenue', np.nan)
                if not pd.isna(revenue) and revenue != 0:
                    financials['gross_margin'] = safe_divide(financials.get('gross_profit', np.nan), revenue, np.nan) * 100
                    financials['operating_margin'] = safe_divide(financials.get('operating_income', np.nan), revenue, np.nan) * 100
                    financials['net_margin'] = safe_divide(financials.get('net_income', np.nan), revenue, np.nan) * 100
            
            # Balance Sheet
            balance_sheet = ticker.balance_sheet
            if balance_sheet is not None and not balance_sheet.empty:
                latest_col = balance_sheet.columns[0]
                
                financials['total_assets'] = balance_sheet.loc['Total Assets', latest_col] if 'Total Assets' in balance_sheet.index else np.nan
                financials['total_liabilities'] = balance_sheet.loc['Total Liabilities Net Minority Interest', latest_col] if 'Total Liabilities Net Minority Interest' in balance_sheet.index else np.nan
                financials['total_equity'] = balance_sheet.loc['Total Equity Gross Minority Interest', latest_col] if 'Total Equity Gross Minority Interest' in balance_sheet.index else np.nan
                financials['total_debt'] = balance_sheet.loc['Total Debt', latest_col] if 'Total Debt' in balance_sheet.index else np.nan
                financials['current_assets'] = balance_sheet.loc['Current Assets', latest_col] if 'Current Assets' in balance_sheet.index else np.nan
                financials['current_liabilities'] = balance_sheet.loc['Current Liabilities', latest_col] if 'Current Liabilities' in balance_sheet.index else np.nan
                financials['cash'] = balance_sheet.loc['Cash And Cash Equivalents', latest_col] if 'Cash And Cash Equivalents' in balance_sheet.index else np.nan
            
            # Cash Flow
            cash_flow = ticker.cashflow
            if cash_flow is not None and not cash_flow.empty:
                latest_col = cash_flow.columns[0]
                
                financials['operating_cash_flow'] = cash_flow.loc['Operating Cash Flow', latest_col] if 'Operating Cash Flow' in cash_flow.index else np.nan
                financials['free_cash_flow'] = cash_flow.loc['Free Cash Flow', latest_col] if 'Free Cash Flow' in cash_flow.index else np.nan
                financials['capital_expenditure'] = cash_flow.loc['Capital Expenditure', latest_col] if 'Capital Expenditure' in cash_flow.index else np.nan
                
        except Exception as e:
            self.logger.warning(f"Error analyzing financial statements: {e}")
        
        return financials
    
    def _analyze_profitability(self, info: Dict) -> Dict[str, Any]:
        """Analyze profitability metrics"""
        return {
            'return_on_equity': info.get('returnOnEquity', np.nan) * 100 if info.get('returnOnEquity') else np.nan,
            'return_on_assets': info.get('returnOnAssets', np.nan) * 100 if info.get('returnOnAssets') else np.nan,
            'profit_margin': info.get('profitMargins', np.nan) * 100 if info.get('profitMargins') else np.nan,
            'operating_margin_info': info.get('operatingMargins', np.nan) * 100 if info.get('operatingMargins') else np.nan,
            'ebitda_margin': info.get('ebitdaMargins', np.nan) * 100 if info.get('ebitdaMargins') else np.nan,
            'gross_margin_info': info.get('grossMargins', np.nan) * 100 if info.get('grossMargins') else np.nan,
        }
    
    def _analyze_financial_health(self, info: Dict) -> Dict[str, Any]:
        """Analyze financial health and liquidity"""
        return {
            'current_ratio': info.get('currentRatio', np.nan),
            'quick_ratio': info.get('quickRatio', np.nan),
            'debt_to_equity': info.get('debtToEquity', np.nan),
            'total_cash': info.get('totalCash', np.nan),
            'total_debt': info.get('totalDebt', np.nan),
            'total_cash_per_share': info.get('totalCashPerShare', np.nan),
        }
    
    def _analyze_valuation(self, info: Dict) -> Dict[str, Any]:
        """Analyze valuation metrics"""
        return {
            '52_week_high': info.get('fiftyTwoWeekHigh', np.nan),
            '52_week_low': info.get('fiftyTwoWeekLow', np.nan),
            'current_price': info.get('currentPrice', info.get('regularMarketPrice', np.nan)),
            'target_mean_price': info.get('targetMeanPrice', np.nan),
            'target_high_price': info.get('targetHighPrice', np.nan),
            'target_low_price': info.get('targetLowPrice', np.nan),
            'recommendation': info.get('recommendationKey', 'N/A'),
        }
    
    def _analyze_dividends(self, ticker, info: Dict) -> Dict[str, Any]:
        """Analyze dividend history and metrics"""
        dividends_data = {
            'dividend_rate': info.get('dividendRate', np.nan),
            'dividend_yield': info.get('dividendYield', np.nan) * 100 if info.get('dividendYield') else np.nan,
            'payout_ratio': info.get('payoutRatio', np.nan) * 100 if info.get('payoutRatio') else np.nan,
            'five_year_avg_dividend_yield': info.get('fiveYearAvgDividendYield', np.nan),
            'ex_dividend_date': info.get('exDividendDate', 'N/A'),
        }
        
        try:
            # Get dividend history
            dividends = ticker.dividends
            if dividends is not None and not dividends.empty and len(dividends) > 0:
                dividends_data['has_dividend_history'] = True
                dividends_data['latest_dividend'] = dividends.iloc[-1]
                dividends_data['dividend_count_5y'] = len(dividends[dividends.index > (datetime.now() - timedelta(days=1825))])
            else:
                dividends_data['has_dividend_history'] = False
        except:
            dividends_data['has_dividend_history'] = False
        
        return dividends_data
    
    def _analyze_trends(self, ticker) -> Dict[str, Any]:
        """Analyze historical financial trends"""
        trends = {}
        
        try:
            # Revenue growth
            income_stmt = ticker.income_stmt
            if income_stmt is not None and not income_stmt.empty and len(income_stmt.columns) >= 2:
                if 'Total Revenue' in income_stmt.index:
                    latest_revenue = income_stmt.loc['Total Revenue', income_stmt.columns[0]]
                    prev_revenue = income_stmt.loc['Total Revenue', income_stmt.columns[1]]
                    trends['revenue_growth_yoy'] = calculate_percentage_change(prev_revenue, latest_revenue)
                    
                    # Calculate CAGR if we have enough data
                    if len(income_stmt.columns) >= 5:
                        oldest_revenue = income_stmt.loc['Total Revenue', income_stmt.columns[-1]]
                        years = len(income_stmt.columns) - 1
                        trends['revenue_cagr'] = calculate_cagr(oldest_revenue, latest_revenue, years)
                
                # Earnings growth
                if 'Net Income' in income_stmt.index:
                    latest_earnings = income_stmt.loc['Net Income', income_stmt.columns[0]]
                    prev_earnings = income_stmt.loc['Net Income', income_stmt.columns[1]]
                    trends['earnings_growth_yoy'] = calculate_percentage_change(prev_earnings, latest_earnings)
            
            # Quarterly revenue growth
            quarterly = ticker.quarterly_income_stmt
            if quarterly is not None and not quarterly.empty and len(quarterly.columns) >= 2:
                if 'Total Revenue' in quarterly.index:
                    latest_q = quarterly.loc['Total Revenue', quarterly.columns[0]]
                    prev_q = quarterly.loc['Total Revenue', quarterly.columns[1]]
                    trends['revenue_growth_qoq'] = calculate_percentage_change(prev_q, latest_q)
                    
        except Exception as e:
            self.logger.warning(f"Error analyzing trends: {e}")
        
        return trends
    
    def _calculate_fundamental_score(self, analysis: Dict) -> float:
        """
        Calculate fundamental score (0-10)
        Based on profitability, financial health, growth, and valuation
        """
        score = 5.0  # Start with neutral score
        
        # Profitability Score (max +2.5)
        roe = analysis.get('return_on_equity', np.nan)
        if not pd.isna(roe):
            if roe >= 15:
                score += 1.5
            elif roe >= 10:
                score += 1.0
            elif roe >= 5:
                score += 0.5
            elif roe < 0:
                score -= 1.0
        
        profit_margin = analysis.get('profit_margin', np.nan)
        if not pd.isna(profit_margin):
            if profit_margin >= 10:
                score += 1.0
            elif profit_margin >= 5:
                score += 0.5
            elif profit_margin < 0:
                score -= 1.0
        
        # Financial Health Score (max +2.0)
        current_ratio = analysis.get('current_ratio', np.nan)
        if not pd.isna(current_ratio):
            if current_ratio >= 2.0:
                score += 1.0
            elif current_ratio >= 1.5:
                score += 0.5
            elif current_ratio < 1.0:
                score -= 0.5
        
        debt_to_equity = analysis.get('debt_to_equity', np.nan)
        if not pd.isna(debt_to_equity):
            if debt_to_equity <= 0.5:
                score += 1.0
            elif debt_to_equity <= 1.0:
                score += 0.5
            elif debt_to_equity >= 2.0:
                score -= 1.0
        
        # Growth Score (max +2.5)
        revenue_growth = analysis.get('revenue_growth_yoy', np.nan)
        if not pd.isna(revenue_growth):
            if revenue_growth >= 20:
                score += 1.5
            elif revenue_growth >= 10:
                score += 1.0
            elif revenue_growth >= 5:
                score += 0.5
            elif revenue_growth < -10:
                score -= 1.0
        
        earnings_growth = analysis.get('earnings_growth_yoy', np.nan)
        if not pd.isna(earnings_growth):
            if earnings_growth >= 20:
                score += 1.0
            elif earnings_growth >= 10:
                score += 0.5
            elif earnings_growth < -10:
                score -= 1.0
        
        # Valuation Score (max +1.0)
        pe_ratio = analysis.get('trailing_pe', np.nan)
        if not pd.isna(pe_ratio):
            if 5 <= pe_ratio <= 15:  # Good value range for penny stocks
                score += 0.5
            elif pe_ratio < 5:  # Too cheap - might be problematic
                score += 0.2
            elif pe_ratio > 30:  # Overvalued
                score -= 0.5
        
        pb_ratio = analysis.get('price_to_book', np.nan)
        if not pd.isna(pb_ratio):
            if pb_ratio < 1.0:
                score += 0.5
            elif pb_ratio > 3.0:
                score -= 0.5
        
        # Operating cash flow check (max +1.0)
        ocf = analysis.get('operating_cash_flow', np.nan)
        if not pd.isna(ocf) and ocf > 0:
            score += 0.5
            
            fcf = analysis.get('free_cash_flow', np.nan)
            if not pd.isna(fcf) and fcf > 0:
                score += 0.5
        
        # Ensure score is within 0-10 range
        score = max(0.0, min(10.0, score))
        
        return round(score, 2)
    
    def _generate_insights(self, analysis: Dict) -> List[str]:
        """Generate human-readable insights from analysis"""
        insights = []
        
        # Profitability insights
        roe = analysis.get('return_on_equity', np.nan)
        if not pd.isna(roe):
            if roe >= 15:
                insights.append(f"✓ Excellent ROE of {roe:.1f}%")
            elif roe < 5:
                insights.append(f"⚠ Low ROE of {roe:.1f}%")
        
        # Growth insights
        revenue_growth = analysis.get('revenue_growth_yoy', np.nan)
        if not pd.isna(revenue_growth):
            if revenue_growth >= 15:
                insights.append(f"✓ Strong revenue growth: {revenue_growth:.1f}% YoY")
            elif revenue_growth < 0:
                insights.append(f"⚠ Declining revenue: {revenue_growth:.1f}% YoY")
        
        # Debt insights
        debt_to_equity = analysis.get('debt_to_equity', np.nan)
        if not pd.isna(debt_to_equity):
            if debt_to_equity >= 2.0:
                insights.append(f"⚠ High debt-to-equity ratio: {debt_to_equity:.2f}")
            elif debt_to_equity < 0.5:
                insights.append(f"✓ Low debt levels: D/E = {debt_to_equity:.2f}")
        
        # Liquidity insights
        current_ratio = analysis.get('current_ratio', np.nan)
        if not pd.isna(current_ratio):
            if current_ratio >= 2.0:
                insights.append(f"✓ Strong liquidity: Current Ratio = {current_ratio:.2f}")
            elif current_ratio < 1.0:
                insights.append(f"⚠ Weak liquidity: Current Ratio = {current_ratio:.2f}")
        
        # Dividend insights
        if analysis.get('has_dividend_history', False):
            div_yield = analysis.get('dividend_yield', np.nan)
            if not pd.isna(div_yield) and div_yield > 0:
                insights.append(f"✓ Pays dividends: {div_yield:.2f}% yield")
        
        # Valuation insights
        pe_ratio = analysis.get('trailing_pe', np.nan)
        if not pd.isna(pe_ratio):
            if pe_ratio < 10:
                insights.append(f"✓ Attractive P/E ratio: {pe_ratio:.1f}")
            elif pe_ratio > 30:
                insights.append(f"⚠ High P/E ratio: {pe_ratio:.1f}")
        
        return insights
    
    def _create_error_analysis(self, symbol: str, error: str) -> Dict[str, Any]:
        """Create error analysis when analysis fails"""
        return {
            'symbol': symbol,
            'error': error,
            'fundamental_score': 0.0,
            'insights': ['Data unavailable - analysis failed'],
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
        }
