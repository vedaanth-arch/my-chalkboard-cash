"""
AIPS - Investment Scoring Module
Combines all analyses to produce final investment score and recommendation
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from datetime import datetime


class InvestmentScorer:
    """Calculates overall investment validity score and generates recommendations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("AIPS.Scorer")
        
        # Get scoring weights from config
        weights = self.config.get('scoring_weights', {})
        self.weight_profile = weights.get('company_profile', 15) / 100
        self.weight_fundamental = weights.get('fundamental_analysis', 40) / 100
        self.weight_technical = weights.get('technical_analysis', 30) / 100
        self.weight_risk = weights.get('risk_factors', 15) / 100
    
    def calculate_investment_score(
        self,
        profile: Dict[str, Any],
        fundamental: Dict[str, Any],
        technical: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive investment validity score
        
        Args:
            profile: Company profile analysis results
            fundamental: Fundamental analysis results
            technical: Technical analysis results
        
        Returns:
            Dictionary with final score, recommendation, and details
        """
        self.logger.info(f"Calculating investment score for {profile.get('symbol', 'Unknown')}")
        
        try:
            # Get individual scores
            profile_score = profile.get('profile_score', 0.0)
            fundamental_score = fundamental.get('fundamental_score', 0.0)
            technical_score = technical.get('technical_score', 0.0)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(profile, fundamental, technical)
            
            # Calculate weighted overall score
            overall_score = (
                profile_score * self.weight_profile +
                fundamental_score * self.weight_fundamental +
                technical_score * self.weight_technical +
                risk_score * self.weight_risk
            )
            
            # Normalize to 0-10 range
            overall_score = max(0.0, min(10.0, overall_score))
            
            # Generate recommendation
            recommendation = self._generate_recommendation(overall_score, profile, fundamental, technical)
            
            # Calculate confidence level
            confidence = self._calculate_confidence(profile, fundamental, technical)
            
            # Determine investment category
            category = self._categorize_investment(overall_score)
            
            # Assess risk level
            risk_level = self._assess_risk_level(risk_score, profile, fundamental, technical)
            
            # Expected return potential
            return_potential = self._estimate_return_potential(fundamental, technical, overall_score)
            
            # Compile final results
            result = {
                'symbol': profile.get('symbol', 'Unknown'),
                'company_name': profile.get('company_name', 'Unknown'),
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                
                # Individual scores
                'profile_score': round(profile_score, 2),
                'fundamental_score': round(fundamental_score, 2),
                'technical_score': round(technical_score, 2),
                'risk_score': round(risk_score, 2),
                
                # Overall assessment
                'overall_score': round(overall_score, 2),
                'investment_validity_score': round(overall_score, 2),  # Alias
                'category': category,
                'recommendation': recommendation,
                'confidence_level': confidence,
                'risk_level': risk_level,
                'return_potential': return_potential,
                
                # Key metrics
                'current_price': profile.get('current_price', fundamental.get('current_price', technical.get('current_price', np.nan))),
                'market_cap': profile.get('market_cap', np.nan),
                'market_cap_category': profile.get('market_cap_category', 'Unknown'),
                
                # Decision factors
                'key_strengths': self._identify_strengths(profile, fundamental, technical),
                'key_weaknesses': self._identify_weaknesses(profile, fundamental, technical),
                'decision_rationale': self._generate_rationale(overall_score, profile, fundamental, technical),
                
                # Scoring breakdown
                'score_breakdown': {
                    'company_profile': f"{profile_score:.1f}/10 ({self.weight_profile*100:.0f}%)",
                    'fundamental_analysis': f"{fundamental_score:.1f}/10 ({self.weight_fundamental*100:.0f}%)",
                    'technical_analysis': f"{technical_score:.1f}/10 ({self.weight_technical*100:.0f}%)",
                    'risk_factors': f"{risk_score:.1f}/10 ({self.weight_risk*100:.0f}%)",
                },
                
                # Flags
                'within_price_range': profile.get('within_price_range', False),
                'is_liquid': technical.get('is_liquid', False),
                'has_red_flags': len(profile.get('red_flags', [])) > 0,
            }
            
            self.logger.info(f"Investment score calculated: {overall_score:.2f}/10 - {recommendation}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating investment score: {e}")
            return self._create_error_result(profile.get('symbol', 'Unknown'), str(e))
    
    def _calculate_risk_score(
        self,
        profile: Dict[str, Any],
        fundamental: Dict[str, Any],
        technical: Dict[str, Any]
    ) -> float:
        """
        Calculate risk score (0-10, higher is lower risk)
        """
        risk_score = 10.0  # Start with low risk
        
        # Red flags penalty
        red_flags = profile.get('red_flags', [])
        risk_score -= len(red_flags) * 1.5
        
        # Liquidity risk
        if not technical.get('is_liquid', False):
            risk_score -= 2.0
        
        # Debt risk
        debt_to_equity = fundamental.get('debt_to_equity', np.nan)
        if not pd.isna(debt_to_equity):
            if debt_to_equity > 2.0:
                risk_score -= 2.0
            elif debt_to_equity > 1.5:
                risk_score -= 1.0
        
        # Volatility risk
        volatility = technical.get('annualized_volatility', np.nan)
        if not pd.isna(volatility):
            if volatility > 80:
                risk_score -= 2.0
            elif volatility > 60:
                risk_score -= 1.0
        
        # Profitability risk
        net_margin = fundamental.get('profit_margin', fundamental.get('net_margin', np.nan))
        if not pd.isna(net_margin) and net_margin < 0:
            risk_score -= 2.0
        
        # Market cap risk
        market_cap_category = profile.get('market_cap_category', 'Unknown')
        if market_cap_category == 'Micro Cap':
            risk_score -= 1.0
        
        # Governance risk
        board_risk = profile.get('board_risk', np.nan)
        if not pd.isna(board_risk) and board_risk > 7:
            risk_score -= 1.5
        
        # Current ratio (liquidity) risk
        current_ratio = fundamental.get('current_ratio', np.nan)
        if not pd.isna(current_ratio) and current_ratio < 1.0:
            risk_score -= 1.5
        
        # Promoter holding risk
        promoter_holding = profile.get('promoter_holding', np.nan)
        if not pd.isna(promoter_holding):
            if promoter_holding < 20:
                risk_score -= 1.5
            elif promoter_holding > 80:
                risk_score -= 0.5  # Too high can be risky too
        
        # Ensure score is within 0-10 range
        risk_score = max(0.0, min(10.0, risk_score))
        
        return risk_score
    
    def _generate_recommendation(
        self,
        overall_score: float,
        profile: Dict[str, Any],
        fundamental: Dict[str, Any],
        technical: Dict[str, Any]
    ) -> str:
        """Generate investment recommendation"""
        
        # Check if within price range
        if not profile.get('within_price_range', False):
            return 'Out of Price Range - Not Applicable'
        
        # Check for critical issues
        if not technical.get('is_liquid', False):
            return 'Risky/Not Recommended - Low Liquidity'
        
        # Check data availability
        if profile.get('error') or fundamental.get('error') or technical.get('error'):
            return 'Insufficient Data - Cannot Recommend'
        
        # Score-based recommendation
        if overall_score >= 7.5:
            return 'Suitable for Investment - Strong Buy'
        elif overall_score >= 6.5:
            return 'Suitable for Investment - Buy'
        elif overall_score >= 5.5:
            return 'Suitable for Investment - Moderate Buy'
        elif overall_score >= 4.5:
            return 'Hold - Monitor Closely'
        elif overall_score >= 3.5:
            return 'Risky/Not Recommended - Consider Selling'
        else:
            return 'Risky/Not Recommended - Avoid'
    
    def _calculate_confidence(
        self,
        profile: Dict[str, Any],
        fundamental: Dict[str, Any],
        technical: Dict[str, Any]
    ) -> str:
        """Calculate confidence level in the analysis"""
        
        # Check data completeness
        data_issues = 0
        
        if profile.get('error') or profile.get('company_name') in ['Error', 'N/A']:
            data_issues += 1
        
        if fundamental.get('error') or pd.isna(fundamental.get('total_revenue')):
            data_issues += 1
        
        if technical.get('error') or technical.get('data_points', 0) < 30:
            data_issues += 1
        
        # Check consistency of signals
        consistency_score = 0
        
        # Profile vs Fundamental consistency
        if profile.get('profile_score', 0) >= 6 and fundamental.get('fundamental_score', 0) >= 6:
            consistency_score += 1
        elif profile.get('profile_score', 0) <= 4 and fundamental.get('fundamental_score', 0) <= 4:
            consistency_score += 1
        
        # Fundamental vs Technical consistency
        if fundamental.get('fundamental_score', 0) >= 6 and technical.get('technical_score', 0) >= 6:
            consistency_score += 1
        elif fundamental.get('fundamental_score', 0) <= 4 and technical.get('technical_score', 0) <= 4:
            consistency_score += 1
        
        # Determine confidence level
        if data_issues == 0 and consistency_score >= 2:
            return 'High'
        elif data_issues <= 1 and consistency_score >= 1:
            return 'Medium'
        else:
            return 'Low'
    
    def _categorize_investment(self, overall_score: float) -> str:
        """Categorize investment based on score"""
        if overall_score >= 8.0:
            return 'Excellent'
        elif overall_score >= 7.0:
            return 'Very Good'
        elif overall_score >= 6.0:
            return 'Good'
        elif overall_score >= 5.0:
            return 'Fair'
        elif overall_score >= 4.0:
            return 'Below Average'
        elif overall_score >= 3.0:
            return 'Poor'
        else:
            return 'Very Poor'
    
    def _assess_risk_level(
        self,
        risk_score: float,
        profile: Dict[str, Any],
        fundamental: Dict[str, Any],
        technical: Dict[str, Any]
    ) -> str:
        """Assess overall risk level"""
        
        # Risk score based (inverted - lower risk score means higher risk)
        if risk_score >= 7.5:
            base_risk = 'Low'
        elif risk_score >= 5.5:
            base_risk = 'Medium'
        elif risk_score >= 3.5:
            base_risk = 'High'
        else:
            base_risk = 'Very High'
        
        # Adjust for specific factors
        adjustments = []
        
        if not technical.get('is_liquid', False):
            adjustments.append('Illiquid')
        
        if len(profile.get('red_flags', [])) > 3:
            adjustments.append('Multiple Red Flags')
        
        volatility = technical.get('annualized_volatility', 0)
        if volatility > 80:
            adjustments.append('High Volatility')
        
        if adjustments:
            return f"{base_risk} Risk ({', '.join(adjustments)})"
        else:
            return f"{base_risk} Risk"
    
    def _estimate_return_potential(
        self,
        fundamental: Dict[str, Any],
        technical: Dict[str, Any],
        overall_score: float
    ) -> str:
        """Estimate expected return potential"""
        
        # Base potential on score
        if overall_score >= 8.0:
            base_potential = 'High (20%+ potential)'
        elif overall_score >= 6.5:
            base_potential = 'Medium-High (15-25% potential)'
        elif overall_score >= 5.0:
            base_potential = 'Medium (10-20% potential)'
        elif overall_score >= 4.0:
            base_potential = 'Low-Medium (5-15% potential)'
        else:
            base_potential = 'Low (0-10% potential, high risk)'
        
        # Consider growth trends
        revenue_growth = fundamental.get('revenue_growth_yoy', 0)
        price_trend = technical.get('short_term_trend', 0)
        
        if revenue_growth > 20 and price_trend > 10:
            base_potential += ' - Strong momentum'
        elif revenue_growth < 0 or price_trend < -10:
            base_potential += ' - Declining momentum'
        
        return base_potential
    
    def _identify_strengths(
        self,
        profile: Dict[str, Any],
        fundamental: Dict[str, Any],
        technical: Dict[str, Any]
    ) -> List[str]:
        """Identify key strengths"""
        strengths = []
        
        # Profile strengths
        if profile.get('profile_score', 0) >= 7:
            strengths.append("Strong company profile")
        
        promoter_holding = profile.get('promoter_holding', 0)
        if 30 <= promoter_holding <= 75:
            strengths.append(f"Healthy promoter holding ({promoter_holding:.1f}%)")
        
        # Fundamental strengths
        roe = fundamental.get('return_on_equity', 0)
        if roe >= 15:
            strengths.append(f"Excellent ROE ({roe:.1f}%)")
        
        revenue_growth = fundamental.get('revenue_growth_yoy', 0)
        if revenue_growth >= 15:
            strengths.append(f"Strong revenue growth ({revenue_growth:.1f}%)")
        
        debt_to_equity = fundamental.get('debt_to_equity', np.nan)
        if not pd.isna(debt_to_equity) and debt_to_equity < 0.5:
            strengths.append("Low debt levels")
        
        # Technical strengths
        if technical.get('is_liquid', False):
            strengths.append("Good liquidity")
        
        if technical.get('overall_signal') == 'BUY':
            strengths.append("Bullish technical signals")
        
        short_trend = technical.get('short_term_trend', 0)
        if short_trend > 10:
            strengths.append("Positive price momentum")
        
        return strengths[:5]  # Top 5 strengths
    
    def _identify_weaknesses(
        self,
        profile: Dict[str, Any],
        fundamental: Dict[str, Any],
        technical: Dict[str, Any]
    ) -> List[str]:
        """Identify key weaknesses"""
        weaknesses = []
        
        # Profile weaknesses
        red_flags = profile.get('red_flags', [])
        if red_flags:
            weaknesses.extend(red_flags[:2])  # Top 2 red flags
        
        # Fundamental weaknesses
        roe = fundamental.get('return_on_equity', 0)
        if roe < 5:
            weaknesses.append(f"Low ROE ({roe:.1f}%)")
        
        debt_to_equity = fundamental.get('debt_to_equity', np.nan)
        if not pd.isna(debt_to_equity) and debt_to_equity > 2.0:
            weaknesses.append(f"High debt-to-equity ({debt_to_equity:.2f})")
        
        current_ratio = fundamental.get('current_ratio', np.nan)
        if not pd.isna(current_ratio) and current_ratio < 1.0:
            weaknesses.append(f"Weak liquidity ratio ({current_ratio:.2f})")
        
        # Technical weaknesses
        if not technical.get('is_liquid', False):
            weaknesses.append("Low trading volume")
        
        volatility = technical.get('annualized_volatility', 0)
        if volatility > 80:
            weaknesses.append(f"High volatility ({volatility:.1f}%)")
        
        if technical.get('overall_signal') == 'SELL':
            weaknesses.append("Bearish technical signals")
        
        return weaknesses[:5]  # Top 5 weaknesses
    
    def _generate_rationale(
        self,
        overall_score: float,
        profile: Dict[str, Any],
        fundamental: Dict[str, Any],
        technical: Dict[str, Any]
    ) -> str:
        """Generate human-readable decision rationale"""
        
        score_category = self._categorize_investment(overall_score)
        
        rationale_parts = []
        
        # Overall assessment
        rationale_parts.append(f"Overall score of {overall_score:.1f}/10 indicates a {score_category.lower()} investment opportunity.")
        
        # Key factor
        max_score = max(
            profile.get('profile_score', 0),
            fundamental.get('fundamental_score', 0),
            technical.get('technical_score', 0)
        )
        
        if max_score == fundamental.get('fundamental_score', 0):
            rationale_parts.append("Fundamentals are the strongest factor.")
        elif max_score == technical.get('technical_score', 0):
            rationale_parts.append("Technical indicators are the strongest factor.")
        elif max_score == profile.get('profile_score', 0):
            rationale_parts.append("Company profile is the strongest factor.")
        
        # Critical issues
        if not technical.get('is_liquid', False):
            rationale_parts.append("⚠ Low liquidity is a significant concern.")
        
        if len(profile.get('red_flags', [])) > 2:
            rationale_parts.append(f"⚠ Multiple red flags identified ({len(profile['red_flags'])}).")
        
        # Positive factors
        strengths = self._identify_strengths(profile, fundamental, technical)
        if len(strengths) >= 3:
            rationale_parts.append(f"✓ Multiple strengths: {', '.join(strengths[:2])}.")
        
        return " ".join(rationale_parts)
    
    def _create_error_result(self, symbol: str, error: str) -> Dict[str, Any]:
        """Create error result when scoring fails"""
        return {
            'symbol': symbol,
            'error': error,
            'overall_score': 0.0,
            'investment_validity_score': 0.0,
            'recommendation': 'Insufficient Data - Cannot Recommend',
            'confidence_level': 'None',
            'risk_level': 'Unknown',
            'category': 'Error',
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
        }
    
    def batch_score(
        self,
        profiles: pd.DataFrame,
        fundamentals: pd.DataFrame,
        technicals: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Score multiple stocks in batch
        
        Args:
            profiles: DataFrame of company profiles
            fundamentals: DataFrame of fundamental analyses
            technicals: DataFrame of technical analyses
        
        Returns:
            DataFrame with investment scores
        """
        self.logger.info("Starting batch scoring")
        
        results = []
        
        # Merge dataframes on symbol
        merged = profiles.merge(fundamentals, on='symbol', how='outer', suffixes=('_profile', '_fundamental'))
        merged = merged.merge(technicals, on='symbol', how='outer')
        
        for _, row in merged.iterrows():
            try:
                profile_dict = {k: v for k, v in row.items() if k.endswith('_profile') or k in ['symbol', 'company_name', 'profile_score', 'red_flags', 'within_price_range', 'market_cap', 'market_cap_category', 'current_price', 'promoter_holding', 'board_risk']}
                profile_dict = {k.replace('_profile', ''): v for k, v in profile_dict.items()}
                
                fundamental_dict = {k: v for k, v in row.items() if k.endswith('_fundamental') or k in ['fundamental_score', 'return_on_equity', 'debt_to_equity', 'current_ratio', 'profit_margin', 'revenue_growth_yoy', 'total_revenue']}
                fundamental_dict = {k.replace('_fundamental', ''): v for k, v in fundamental_dict.items()}
                
                technical_dict = {k: v for k, v in row.items() if k in ['technical_score', 'is_liquid', 'overall_signal', 'short_term_trend', 'annualized_volatility', 'rsi', 'current_price', 'data_points']}
                
                score_result = self.calculate_investment_score(profile_dict, fundamental_dict, technical_dict)
                results.append(score_result)
                
            except Exception as e:
                self.logger.error(f"Error scoring {row.get('symbol', 'Unknown')}: {e}")
        
        df = pd.DataFrame(results)
        self.logger.info(f"Batch scoring complete: {len(df)} stocks scored")
        
        return df
