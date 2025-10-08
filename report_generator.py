"""
AIPS - Reporting Module
Generates comprehensive reports and visualizations
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List
import os
from datetime import datetime
import json

from utils import format_indian_currency, ensure_directories


class ReportGenerator:
    """Generates reports and visualizations for stock analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("AIPS.Reporter")
        self.output_dir = config.get('output', {}).get('report_directory', 'reports')
        ensure_directories()
        
        # Set style for plots
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 8)
    
    def generate_stock_report(
        self,
        profile: Dict[str, Any],
        fundamental: Dict[str, Any],
        technical: Dict[str, Any],
        score_result: Dict[str, Any]
    ) -> str:
        """
        Generate comprehensive report for a single stock
        
        Returns:
            Path to generated report
        """
        symbol = score_result.get('symbol', 'Unknown').replace('.NS', '').replace('.BO', '')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.logger.info(f"Generating report for {symbol}")
        
        # Generate different format reports
        report_paths = []
        
        output_formats = self.config.get('output', {}).get('format', ['html'])
        
        if 'html' in output_formats:
            html_path = self._generate_html_report(symbol, timestamp, profile, fundamental, technical, score_result)
            report_paths.append(html_path)
        
        if 'excel' in output_formats:
            excel_path = self._generate_excel_report(symbol, timestamp, profile, fundamental, technical, score_result)
            report_paths.append(excel_path)
        
        if 'json' in output_formats:
            json_path = self._generate_json_report(symbol, timestamp, profile, fundamental, technical, score_result)
            report_paths.append(json_path)
        
        self.logger.info(f"Report generated: {', '.join(report_paths)}")
        return report_paths[0] if report_paths else None
    
    def _generate_html_report(
        self,
        symbol: str,
        timestamp: str,
        profile: Dict,
        fundamental: Dict,
        technical: Dict,
        score_result: Dict
    ) -> str:
        """Generate HTML report"""
        
        filename = f"{self.output_dir}/{symbol}_report_{timestamp}.html"
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIPS Stock Analysis Report - {symbol}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        .score-box {{
            display: inline-block;
            padding: 20px;
            margin: 10px;
            border-radius: 8px;
            text-align: center;
            min-width: 150px;
        }}
        .score-excellent {{ background-color: #2ecc71; color: white; }}
        .score-good {{ background-color: #27ae60; color: white; }}
        .score-fair {{ background-color: #f39c12; color: white; }}
        .score-poor {{ background-color: #e74c3c; color: white; }}
        .metric-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .metric-table th {{
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        .metric-table td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        .metric-table tr:hover {{
            background-color: #f5f5f5;
        }}
        .recommendation {{
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
        }}
        .rec-buy {{ background-color: #2ecc71; color: white; }}
        .rec-hold {{ background-color: #f39c12; color: white; }}
        .rec-sell {{ background-color: #e74c3c; color: white; }}
        .rec-avoid {{ background-color: #c0392b; color: white; }}
        .strengths {{
            background-color: #d5f4e6;
            padding: 15px;
            border-left: 4px solid #2ecc71;
            margin: 10px 0;
        }}
        .weaknesses {{
            background-color: #fadbd8;
            padding: 15px;
            border-left: 4px solid #e74c3c;
            margin: 10px 0;
        }}
        .red-flag {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .insight {{
            padding: 10px;
            margin: 5px 0;
            background-color: #ecf0f1;
            border-radius: 4px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 AI-Driven Stock Analysis Report</h1>
        <h2>📊 {score_result.get('company_name', 'Unknown Company')}</h2>
        <p><strong>Symbol:</strong> {symbol} | <strong>Date:</strong> {score_result.get('analysis_date', 'N/A')}</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <div class="score-box {self._get_score_class(score_result.get('overall_score', 0))}">
                <h3>Investment Validity Score</h3>
                <h1>{score_result.get('overall_score', 0):.1f}/10</h1>
                <p>{score_result.get('category', 'N/A')}</p>
            </div>
        </div>
        
        <div class="recommendation {self._get_recommendation_class(score_result.get('recommendation', ''))}">
            📌 RECOMMENDATION: {score_result.get('recommendation', 'N/A')}
        </div>
        
        <h2>💡 Executive Summary</h2>
        <table class="metric-table">
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Current Price</td>
                <td>₹{score_result.get('current_price', 0):.2f}</td>
            </tr>
            <tr>
                <td>Market Cap</td>
                <td>{format_indian_currency(score_result.get('market_cap', 0))} ({score_result.get('market_cap_category', 'N/A')})</td>
            </tr>
            <tr>
                <td>Sector</td>
                <td>{profile.get('sector', 'N/A')}</td>
            </tr>
            <tr>
                <td>Confidence Level</td>
                <td>{score_result.get('confidence_level', 'N/A')}</td>
            </tr>
            <tr>
                <td>Risk Level</td>
                <td>{score_result.get('risk_level', 'N/A')}</td>
            </tr>
            <tr>
                <td>Return Potential</td>
                <td>{score_result.get('return_potential', 'N/A')}</td>
            </tr>
        </table>
        
        <h2>📈 Score Breakdown</h2>
        <table class="metric-table">
            <tr>
                <th>Component</th>
                <th>Score</th>
                <th>Weight</th>
            </tr>
            <tr>
                <td>Company Profile</td>
                <td>{score_result.get('profile_score', 0):.1f}/10</td>
                <td>{score_result.get('score_breakdown', {}).get('company_profile', 'N/A')}</td>
            </tr>
            <tr>
                <td>Fundamental Analysis</td>
                <td>{score_result.get('fundamental_score', 0):.1f}/10</td>
                <td>{score_result.get('score_breakdown', {}).get('fundamental_analysis', 'N/A')}</td>
            </tr>
            <tr>
                <td>Technical Analysis</td>
                <td>{score_result.get('technical_score', 0):.1f}/10</td>
                <td>{score_result.get('score_breakdown', {}).get('technical_analysis', 'N/A')}</td>
            </tr>
            <tr>
                <td>Risk Factors</td>
                <td>{score_result.get('risk_score', 0):.1f}/10</td>
                <td>{score_result.get('score_breakdown', {}).get('risk_factors', 'N/A')}</td>
            </tr>
        </table>
        
        <h2>✅ Key Strengths</h2>
        <div class="strengths">
            <ul>
                {''.join([f'<li>{strength}</li>' for strength in score_result.get('key_strengths', ['None identified'])])}
            </ul>
        </div>
        
        <h2>⚠️ Key Weaknesses</h2>
        <div class="weaknesses">
            <ul>
                {''.join([f'<li>{weakness}</li>' for weakness in score_result.get('key_weaknesses', ['None identified'])])}
            </ul>
        </div>
        
        <h2>🏢 Company Profile</h2>
        <table class="metric-table">
            <tr>
                <td>Business Summary</td>
                <td>{profile.get('business_summary', 'N/A')[:300]}...</td>
            </tr>
            <tr>
                <td>Industry</td>
                <td>{profile.get('industry', 'N/A')}</td>
            </tr>
            <tr>
                <td>Promoter Holding</td>
                <td>{profile.get('promoter_holding', 0):.1f}%</td>
            </tr>
            <tr>
                <td>Institutional Holding</td>
                <td>{profile.get('institutional_holding', 0):.1f}%</td>
            </tr>
        </table>
        
        {self._format_red_flags(profile.get('red_flags', []))}
        
        <h2>💰 Fundamental Metrics</h2>
        <table class="metric-table">
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Return on Equity (ROE)</td>
                <td>{fundamental.get('return_on_equity', 0):.2f}%</td>
            </tr>
            <tr>
                <td>Profit Margin</td>
                <td>{fundamental.get('profit_margin', fundamental.get('net_margin', 0)):.2f}%</td>
            </tr>
            <tr>
                <td>Debt-to-Equity</td>
                <td>{fundamental.get('debt_to_equity', 0):.2f}</td>
            </tr>
            <tr>
                <td>Current Ratio</td>
                <td>{fundamental.get('current_ratio', 0):.2f}</td>
            </tr>
            <tr>
                <td>Revenue Growth (YoY)</td>
                <td>{fundamental.get('revenue_growth_yoy', 0):.2f}%</td>
            </tr>
            <tr>
                <td>P/E Ratio</td>
                <td>{fundamental.get('trailing_pe', 0):.2f}</td>
            </tr>
        </table>
        
        <h2>📊 Technical Indicators</h2>
        <table class="metric-table">
            <tr>
                <th>Indicator</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>RSI (14)</td>
                <td>{technical.get('rsi', 0):.2f} - {technical.get('rsi_signal', 'N/A')}</td>
            </tr>
            <tr>
                <td>MACD Signal</td>
                <td>{technical.get('macd_trend', 'N/A')}</td>
            </tr>
            <tr>
                <td>Overall Signal</td>
                <td><strong>{technical.get('overall_signal', 'N/A')}</strong></td>
            </tr>
            <tr>
                <td>Short-term Trend (30d)</td>
                <td>{technical.get('short_term_trend', 0):.2f}% - {technical.get('short_term_direction', 'N/A')}</td>
            </tr>
            <tr>
                <td>Volatility (Annualized)</td>
                <td>{technical.get('annualized_volatility', 0):.2f}%</td>
            </tr>
            <tr>
                <td>Average Volume (30d)</td>
                <td>{technical.get('avg_volume_30d', 0):,.0f} shares</td>
            </tr>
        </table>
        
        <h2>🎯 Decision Rationale</h2>
        <p>{score_result.get('decision_rationale', 'N/A')}</p>
        
        <div class="footer">
            <p>Generated by AIPS (AI-Driven Penny Stock Validation System)</p>
            <p><em>This report is for informational purposes only and should not be considered as investment advice.</em></p>
            <p><em>Always conduct your own research and consult with a qualified financial advisor before making investment decisions.</em></p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filename
    
    def _generate_excel_report(
        self,
        symbol: str,
        timestamp: str,
        profile: Dict,
        fundamental: Dict,
        technical: Dict,
        score_result: Dict
    ) -> str:
        """Generate Excel report"""
        
        filename = f"{self.output_dir}/{symbol}_report_{timestamp}.xlsx"
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                'Metric': ['Symbol', 'Company Name', 'Investment Score', 'Recommendation', 'Category', 
                           'Current Price', 'Market Cap', 'Risk Level', 'Confidence'],
                'Value': [
                    symbol,
                    score_result.get('company_name', 'N/A'),
                    f"{score_result.get('overall_score', 0):.2f}/10",
                    score_result.get('recommendation', 'N/A'),
                    score_result.get('category', 'N/A'),
                    f"₹{score_result.get('current_price', 0):.2f}",
                    format_indian_currency(score_result.get('market_cap', 0)),
                    score_result.get('risk_level', 'N/A'),
                    score_result.get('confidence_level', 'N/A')
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Profile sheet
            profile_df = pd.DataFrame([{k: v for k, v in profile.items() if not isinstance(v, (list, dict))}])
            profile_df.to_excel(writer, sheet_name='Company Profile', index=False)
            
            # Fundamental sheet
            fundamental_df = pd.DataFrame([{k: v for k, v in fundamental.items() if not isinstance(v, (list, dict))}])
            fundamental_df.to_excel(writer, sheet_name='Fundamentals', index=False)
            
            # Technical sheet
            technical_df = pd.DataFrame([{k: v for k, v in technical.items() if not isinstance(v, (list, dict))}])
            technical_df.to_excel(writer, sheet_name='Technical', index=False)
            
            # Score breakdown
            score_df = pd.DataFrame([score_result])
            score_df.to_excel(writer, sheet_name='Scores', index=False)
        
        return filename
    
    def _generate_json_report(
        self,
        symbol: str,
        timestamp: str,
        profile: Dict,
        fundamental: Dict,
        technical: Dict,
        score_result: Dict
    ) -> str:
        """Generate JSON report"""
        
        filename = f"{self.output_dir}/{symbol}_report_{timestamp}.json"
        
        report_data = {
            'symbol': symbol,
            'timestamp': timestamp,
            'profile': profile,
            'fundamental': fundamental,
            'technical': technical,
            'score_result': score_result
        }
        
        # Convert numpy types to native Python types
        report_data = json.loads(pd.DataFrame([report_data]).to_json(orient='records'))[0]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def generate_batch_summary(self, results_df: pd.DataFrame) -> str:
        """Generate summary report for multiple stocks"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/batch_summary_{timestamp}.xlsx"
        
        self.logger.info(f"Generating batch summary for {len(results_df)} stocks")
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Sort by overall score
            summary = results_df.sort_values('overall_score', ascending=False)
            
            # Select key columns for summary
            columns_to_include = [
                'symbol', 'company_name', 'overall_score', 'recommendation', 
                'category', 'current_price', 'market_cap_category', 'risk_level',
                'profile_score', 'fundamental_score', 'technical_score'
            ]
            
            summary = summary[[col for col in columns_to_include if col in summary.columns]]
            summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # Top recommendations
            top_stocks = results_df[results_df['recommendation'].str.contains('Suitable', na=False)]
            if not top_stocks.empty:
                top_stocks.to_excel(writer, sheet_name='Top Picks', index=False)
            
            # Risky stocks
            risky_stocks = results_df[results_df['recommendation'].str.contains('Risky|Not Recommended', na=False)]
            if not risky_stocks.empty:
                risky_stocks.to_excel(writer, sheet_name='Avoid', index=False)
        
        self.logger.info(f"Batch summary generated: {filename}")
        return filename
    
    def _get_score_class(self, score: float) -> str:
        """Get CSS class for score"""
        if score >= 7.5:
            return 'score-excellent'
        elif score >= 6.0:
            return 'score-good'
        elif score >= 4.5:
            return 'score-fair'
        else:
            return 'score-poor'
    
    def _get_recommendation_class(self, recommendation: str) -> str:
        """Get CSS class for recommendation"""
        if 'Suitable' in recommendation or 'Buy' in recommendation:
            return 'rec-buy'
        elif 'Hold' in recommendation:
            return 'rec-hold'
        elif 'Risky' in recommendation or 'Not Recommended' in recommendation:
            return 'rec-sell'
        else:
            return 'rec-avoid'
    
    def _format_red_flags(self, red_flags: List[str]) -> str:
        """Format red flags for HTML"""
        if not red_flags:
            return '<p style="color: green;">✓ No major red flags identified</p>'
        
        html = '<h2>🚩 Red Flags</h2><div class="weaknesses"><ul>'
        for flag in red_flags:
            html += f'<li class="red-flag">{flag}</li>'
        html += '</ul></div>'
        return html
