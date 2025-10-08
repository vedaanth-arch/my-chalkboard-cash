"""
AIPS Example Usage
Demonstrates various ways to use the AIPS system
"""

from aips_main import AIPSOrchestrator
import pandas as pd


def example_1_single_stock_analysis():
    """Example 1: Analyze a single stock with detailed report"""
    
    print("=" * 80)
    print("Example 1: Single Stock Analysis")
    print("=" * 80)
    
    # Initialize AIPS
    aips = AIPSOrchestrator('config.yaml')
    
    # Analyze a single stock
    symbol = 'RELIANCE'
    result = aips.validate_single_stock(symbol, generate_report=True)
    
    if result.get('success'):
        score = result['score_result']
        print(f"\n✓ Analysis Complete for {symbol}")
        print(f"Company: {score['company_name']}")
        print(f"Overall Score: {score['overall_score']:.2f}/10")
        print(f"Category: {score['category']}")
        print(f"Recommendation: {score['recommendation']}")
        print(f"Risk Level: {score['risk_level']}")
        print(f"Confidence: {score['confidence_level']}")
        
        print("\nScore Breakdown:")
        for component, value in score['score_breakdown'].items():
            print(f"  {component}: {value}")
        
        print("\nKey Strengths:")
        for strength in score['key_strengths']:
            print(f"  ✓ {strength}")
        
        print("\nKey Weaknesses:")
        for weakness in score['key_weaknesses']:
            print(f"  ⚠ {weakness}")
        
        if 'report_path' in score:
            print(f"\nDetailed report: {score['report_path']}")
    else:
        print(f"✗ Analysis failed: {result.get('error')}")


def example_2_batch_analysis():
    """Example 2: Analyze multiple stocks"""
    
    print("\n" + "=" * 80)
    print("Example 2: Batch Stock Analysis")
    print("=" * 80)
    
    aips = AIPSOrchestrator('config.yaml')
    
    # Define stocks to analyze
    symbols = [
        'RELIANCE',
        'TCS',
        'INFY',
        'HDFCBANK',
        'ICICIBANK',
        'TATAMOTORS',
        'WIPRO',
        'AXISBANK',
        'BHARTIARTL',
        'ITC'
    ]
    
    print(f"\nAnalyzing {len(symbols)} stocks...")
    
    # Run batch analysis
    results_df = aips.validate_multiple_stocks(
        symbols,
        generate_individual_reports=False,
        generate_summary=True
    )
    
    if not results_df.empty:
        print("\n" + "=" * 80)
        print("Results Summary")
        print("=" * 80)
        
        # Display top performers
        print("\n🏆 Top 5 Stocks by Score:")
        top_5 = results_df.nlargest(5, 'overall_score')
        for idx, row in top_5.iterrows():
            print(f"  {row['symbol']}: {row['overall_score']:.2f} - {row['recommendation']}")
        
        # Display suitable investments
        suitable = results_df[results_df['recommendation'].str.contains('Suitable', na=False)]
        print(f"\n✓ Suitable for Investment: {len(suitable)}/{len(results_df)}")
        
        # Save results
        results_df.to_csv('batch_results.csv', index=False)
        print("\nResults saved to: batch_results.csv")


def example_3_filtered_analysis():
    """Example 3: Filter and analyze stocks by criteria"""
    
    print("\n" + "=" * 80)
    print("Example 3: Filtered Analysis")
    print("=" * 80)
    
    aips = AIPSOrchestrator('config.yaml')
    
    # Analyze a larger set
    symbols = ['RELIANCE', 'TCS', 'INFY', 'WIPRO', 'HDFCBANK', 'ICICIBANK', 
               'TATAMOTORS', 'BHARTIARTL', 'ITC', 'AXISBANK']
    
    results_df = aips.validate_multiple_stocks(symbols, generate_summary=False)
    
    if not results_df.empty:
        # Filter by criteria
        print("\nApplying filters:")
        print("  - Minimum score: 6.0")
        print("  - Must be liquid")
        print("  - Category: Good or better")
        
        filtered = aips.filter_by_criteria(
            results_df,
            min_score=6.0,
            min_liquidity=True,
            categories=['Excellent', 'Very Good', 'Good']
        )
        
        print(f"\nFiltered results: {len(filtered)}/{len(results_df)} stocks")
        
        if not filtered.empty:
            print("\nFiltered Stocks:")
            for idx, row in filtered.iterrows():
                print(f"  {row['symbol']}: {row['overall_score']:.2f} "
                      f"({row['category']}) - {row['recommendation']}")


def example_4_component_analysis():
    """Example 4: Access individual analysis components"""
    
    print("\n" + "=" * 80)
    print("Example 4: Component Analysis")
    print("=" * 80)
    
    from utils import load_config
    from company_profile import CompanyProfileValidator
    from fundamental_analysis import FundamentalAnalyzer
    from technical_analysis import TechnicalAnalyzer
    
    config = load_config('config.yaml')
    symbol = 'TCS'
    
    print(f"\nAnalyzing {symbol} components individually...\n")
    
    # Company Profile
    print("1. Company Profile Analysis")
    print("-" * 40)
    profile_validator = CompanyProfileValidator(config)
    profile = profile_validator.validate_company(symbol)
    
    print(f"Company: {profile.get('company_name', 'N/A')}")
    print(f"Sector: {profile.get('sector', 'N/A')}")
    print(f"Market Cap: {profile.get('market_cap_formatted', 'N/A')}")
    print(f"Profile Score: {profile.get('profile_score', 0):.2f}/10")
    print(f"Red Flags: {len(profile.get('red_flags', []))}")
    
    # Fundamental Analysis
    print("\n2. Fundamental Analysis")
    print("-" * 40)
    fundamental_analyzer = FundamentalAnalyzer(config)
    fundamental = fundamental_analyzer.analyze(symbol)
    
    print(f"ROE: {fundamental.get('return_on_equity', 0):.2f}%")
    print(f"Debt/Equity: {fundamental.get('debt_to_equity', 0):.2f}")
    print(f"Current Ratio: {fundamental.get('current_ratio', 0):.2f}")
    print(f"Revenue Growth: {fundamental.get('revenue_growth_yoy', 0):.2f}%")
    print(f"Fundamental Score: {fundamental.get('fundamental_score', 0):.2f}/10")
    
    # Technical Analysis
    print("\n3. Technical Analysis")
    print("-" * 40)
    technical_analyzer = TechnicalAnalyzer(config)
    technical = technical_analyzer.analyze(symbol)
    
    print(f"RSI: {technical.get('rsi', 0):.2f} ({technical.get('rsi_signal', 'N/A')})")
    print(f"MACD: {technical.get('macd_trend', 'N/A')}")
    print(f"Overall Signal: {technical.get('overall_signal', 'N/A')}")
    print(f"Short-term Trend: {technical.get('short_term_direction', 'N/A')}")
    print(f"Technical Score: {technical.get('technical_score', 0):.2f}/10")


def example_5_top_picks():
    """Example 5: Get top stock picks"""
    
    print("\n" + "=" * 80)
    print("Example 5: Top Stock Picks")
    print("=" * 80)
    
    aips = AIPSOrchestrator('config.yaml')
    
    # Analyze a set of stocks
    symbols = ['RELIANCE', 'TCS', 'INFY', 'WIPRO', 'HDFCBANK', 'ICICIBANK',
               'TATAMOTORS', 'BHARTIARTL', 'ITC', 'AXISBANK', 'SBIN',
               'MARUTI', 'ASIANPAINT', 'HINDUNILVR', 'BAJFINANCE']
    
    print(f"\nAnalyzing {len(symbols)} stocks to find top picks...")
    
    results_df = aips.validate_multiple_stocks(symbols, generate_summary=False)
    
    if not results_df.empty:
        # Get top 5 picks
        top_picks = aips.get_top_picks(results_df, top_n=5)
        
        print("\n🎯 Top 5 Investment Picks:")
        print("=" * 80)
        
        for idx, row in top_picks.iterrows():
            print(f"\n{idx + 1}. {row['symbol']} - {row['company_name']}")
            print(f"   Score: {row['overall_score']:.2f}/10 ({row['category']})")
            print(f"   Price: ₹{row['current_price']:.2f}")
            print(f"   Recommendation: {row['recommendation']}")
            print(f"   Risk: {row['risk_level']}")
            print(f"   Return Potential: {row['return_potential']}")
            
            # Show strengths
            if row.get('key_strengths'):
                print(f"   Key Strengths:")
                for strength in row['key_strengths'][:3]:
                    print(f"     • {strength}")


def example_6_from_csv():
    """Example 6: Analyze stocks from CSV file"""
    
    print("\n" + "=" * 80)
    print("Example 6: Analyze from CSV File")
    print("=" * 80)
    
    # Create sample CSV
    sample_data = {
        'symbol': ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK'],
        'watchlist': ['Portfolio 1'] * 5
    }
    df = pd.DataFrame(sample_data)
    df.to_csv('sample_stocks.csv', index=False)
    print("\nCreated sample_stocks.csv with 5 stocks")
    
    # Analyze from file
    aips = AIPSOrchestrator('config.yaml')
    results_df = aips.validate_stocks_from_file('sample_stocks.csv')
    
    if not results_df.empty:
        print(f"\nAnalyzed {len(results_df)} stocks from CSV")
        print("\nResults:")
        for idx, row in results_df.iterrows():
            print(f"  {row['symbol']}: {row['overall_score']:.2f} - "
                  f"{row['recommendation']}")


def example_7_custom_config():
    """Example 7: Use custom configuration"""
    
    print("\n" + "=" * 80)
    print("Example 7: Custom Configuration")
    print("=" * 80)
    
    # You can create a custom config file
    print("\nTo use custom configuration:")
    print("1. Copy config.yaml to my_config.yaml")
    print("2. Modify settings as needed")
    print("3. Initialize AIPS with custom config:")
    print("\n   aips = AIPSOrchestrator('my_config.yaml')")
    
    print("\nExample customizations:")
    print("  - Change price range (e.g., 1-50)")
    print("  - Adjust scoring weights")
    print("  - Modify fundamental thresholds")
    print("  - Change technical indicator periods")
    print("  - Set different risk criteria")


def main():
    """Run all examples"""
    
    print("\n" + "=" * 80)
    print("AIPS - Example Usage Demonstrations")
    print("=" * 80)
    print("\nThis script demonstrates various ways to use AIPS")
    print("Note: Some examples require internet connection and may take time")
    
    try:
        # Run examples (comment out any you don't want to run)
        example_1_single_stock_analysis()
        # example_2_batch_analysis()
        # example_3_filtered_analysis()
        # example_4_component_analysis()
        # example_5_top_picks()
        # example_6_from_csv()
        example_7_custom_config()
        
        print("\n" + "=" * 80)
        print("Examples completed!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("Make sure you have:")
        print("  - Installed all requirements (pip install -r requirements.txt)")
        print("  - Internet connection for data fetching")
        print("  - Valid config.yaml file")


if __name__ == "__main__":
    main()
