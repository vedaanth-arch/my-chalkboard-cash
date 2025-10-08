"""
AIPS - Company Profile Validation Module
Gathers and validates company background information
"""

import logging
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from utils import (
    format_indian_currency,
    categorize_market_cap,
    get_indian_stock_symbol,
    clean_numeric_value
)


class CompanyProfileValidator:
    """Validates company profile and identifies red flags"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("AIPS.CompanyProfile")
    
    def validate_company(self, symbol: str) -> Dict[str, Any]:
        """
        Main method to validate company profile
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE' or 'RELIANCE.NS')
        
        Returns:
            Dictionary containing company profile and validation results
        """
        self.logger.info(f"Starting company profile validation for {symbol}")
        
        # Convert to proper format
        symbol = get_indian_stock_symbol(
            symbol, 
            self.config.get('market', {}).get('exchange', 'NSE')
        )
        
        try:
            # Fetch company data
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Build profile
            profile = {
                'symbol': symbol,
                'company_name': info.get('longName', info.get('shortName', 'N/A')),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', np.nan),
                'current_price': info.get('currentPrice', info.get('regularMarketPrice', np.nan)),
                'website': info.get('website', 'N/A'),
                'business_summary': info.get('longBusinessSummary', 'N/A'),
                'employees': info.get('fullTimeEmployees', np.nan),
                'founded_year': info.get('yearFounded', 'N/A'),
                'country': info.get('country', 'India'),
                'city': info.get('city', 'N/A'),
                'validation_date': datetime.now().strftime('%Y-%m-%d'),
            }
            
            # Get ownership data
            ownership = self._extract_ownership_data(info)
            profile.update(ownership)
            
            # Get governance data
            governance = self._extract_governance_data(ticker, info)
            profile.update(governance)
            
            # Identify red flags
            red_flags = self._identify_red_flags(profile, info)
            profile['red_flags'] = red_flags
            
            # Calculate profile score (0-10)
            profile_score = self._calculate_profile_score(profile, red_flags)
            profile['profile_score'] = profile_score
            
            # Add categorization
            profile['market_cap_category'] = categorize_market_cap(profile['market_cap'])
            profile['market_cap_formatted'] = format_indian_currency(profile['market_cap'])
            
            # Check if within price range
            price = profile['current_price']
            price_min = self.config.get('price_range', {}).get('min', 1)
            price_max = self.config.get('price_range', {}).get('max', 100)
            profile['within_price_range'] = (
                not pd.isna(price) and price_min <= price <= price_max
            )
            
            self.logger.info(f"Successfully validated {symbol}: Score {profile_score:.2f}/10")
            return profile
            
        except Exception as e:
            self.logger.error(f"Error validating company {symbol}: {e}")
            return self._create_error_profile(symbol, str(e))
    
    def _extract_ownership_data(self, info: Dict) -> Dict[str, Any]:
        """Extract ownership and shareholding data"""
        try:
            return {
                'promoter_holding': info.get('heldPercentInsiders', np.nan) * 100 if info.get('heldPercentInsiders') else np.nan,
                'institutional_holding': info.get('heldPercentInstitutions', np.nan) * 100 if info.get('heldPercentInstitutions') else np.nan,
                'public_holding': np.nan,  # Calculate if data available
                'shares_outstanding': info.get('sharesOutstanding', np.nan),
                'float_shares': info.get('floatShares', np.nan),
            }
        except Exception as e:
            self.logger.warning(f"Error extracting ownership data: {e}")
            return {}
    
    def _extract_governance_data(self, ticker, info: Dict) -> Dict[str, Any]:
        """Extract governance and management data"""
        try:
            governance = {
                'board_risk': info.get('overallRisk', np.nan),
                'audit_risk': info.get('auditRisk', np.nan),
                'compensation_risk': info.get('compensationRisk', np.nan),
                'shareholder_rights_risk': info.get('shareHolderRightsRisk', np.nan),
            }
            
            # Try to get major holders
            try:
                major_holders = ticker.major_holders
                if major_holders is not None and not major_holders.empty:
                    governance['has_major_holders_data'] = True
            except:
                governance['has_major_holders_data'] = False
            
            return governance
            
        except Exception as e:
            self.logger.warning(f"Error extracting governance data: {e}")
            return {}
    
    def _identify_red_flags(self, profile: Dict, info: Dict) -> List[str]:
        """Identify potential red flags in company profile"""
        red_flags = []
        
        # Check promoter holding
        promoter_holding = profile.get('promoter_holding', np.nan)
        min_promoter = self.config.get('risk_flags', {}).get('min_promoter_holding', 30)
        if not pd.isna(promoter_holding) and promoter_holding < min_promoter:
            red_flags.append(f"Low promoter holding ({promoter_holding:.1f}%)")
        
        # Check market cap
        market_cap = profile.get('market_cap', np.nan)
        min_market_cap = self.config.get('fundamental_thresholds', {}).get('min_market_cap', 50000000)
        if not pd.isna(market_cap) and market_cap < min_market_cap:
            red_flags.append(f"Very low market cap ({format_indian_currency(market_cap)})")
        
        # Check governance risks
        overall_risk = profile.get('board_risk', np.nan)
        if not pd.isna(overall_risk) and overall_risk > 7:
            red_flags.append(f"High governance risk score ({overall_risk})")
        
        # Check if company has business summary
        if profile.get('business_summary', 'N/A') in ['N/A', '', None]:
            red_flags.append("Limited company information available")
        
        # Check sector (some sectors are riskier for penny stocks)
        risky_sectors = ['Real Estate', 'Construction']
        if profile.get('sector') in risky_sectors:
            red_flags.append(f"High-risk sector: {profile.get('sector')}")
        
        # Check float shares (low float can mean manipulation risk)
        float_shares = profile.get('float_shares', np.nan)
        shares_outstanding = profile.get('shares_outstanding', np.nan)
        if not pd.isna(float_shares) and not pd.isna(shares_outstanding):
            if shares_outstanding > 0:
                float_ratio = (float_shares / shares_outstanding) * 100
                if float_ratio < 10:
                    red_flags.append(f"Very low public float ({float_ratio:.1f}%)")
        
        return red_flags
    
    def _calculate_profile_score(self, profile: Dict, red_flags: List[str]) -> float:
        """
        Calculate company profile score (0-10)
        Higher score = better profile
        """
        score = 10.0
        
        # Deduct points for red flags
        score -= len(red_flags) * 1.5
        
        # Reward good promoter holding (30-75% range is ideal)
        promoter_holding = profile.get('promoter_holding', np.nan)
        if not pd.isna(promoter_holding):
            if 30 <= promoter_holding <= 75:
                score += 1.0
            elif promoter_holding < 20:
                score -= 1.0
        
        # Reward adequate market cap
        market_cap = profile.get('market_cap', np.nan)
        min_market_cap = self.config.get('fundamental_thresholds', {}).get('min_market_cap', 50000000)
        if not pd.isna(market_cap) and market_cap >= min_market_cap * 2:
            score += 0.5
        
        # Reward presence of detailed business summary
        if profile.get('business_summary', 'N/A') not in ['N/A', '', None]:
            if len(profile['business_summary']) > 100:
                score += 0.5
        
        # Reward low governance risk
        overall_risk = profile.get('board_risk', np.nan)
        if not pd.isna(overall_risk):
            if overall_risk <= 5:
                score += 1.0
            elif overall_risk >= 8:
                score -= 1.0
        
        # Ensure score is within 0-10 range
        score = max(0.0, min(10.0, score))
        
        return round(score, 2)
    
    def _create_error_profile(self, symbol: str, error: str) -> Dict[str, Any]:
        """Create error profile when validation fails"""
        return {
            'symbol': symbol,
            'company_name': 'Error',
            'error': error,
            'profile_score': 0.0,
            'red_flags': ['Data unavailable - validation failed'],
            'within_price_range': False,
            'validation_date': datetime.now().strftime('%Y-%m-%d'),
        }
    
    def batch_validate(self, symbols: List[str]) -> pd.DataFrame:
        """
        Validate multiple companies
        
        Args:
            symbols: List of stock symbols
        
        Returns:
            DataFrame with validation results
        """
        self.logger.info(f"Starting batch validation for {len(symbols)} companies")
        
        results = []
        for symbol in symbols:
            try:
                profile = self.validate_company(symbol)
                results.append(profile)
            except Exception as e:
                self.logger.error(f"Error in batch validation for {symbol}: {e}")
                results.append(self._create_error_profile(symbol, str(e)))
        
        df = pd.DataFrame(results)
        self.logger.info(f"Batch validation complete: {len(df)} results")
        
        return df
