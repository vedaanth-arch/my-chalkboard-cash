"""
AIPS - Main Orchestrator
Coordinates the entire stock validation workflow
"""

import logging
import argparse
import sys
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime

from utils import (
    setup_logging,
    load_config,
    ensure_directories,
    ProgressTracker,
    validate_stock_symbol
)
from company_profile import CompanyProfileValidator
from fundamental_analysis import FundamentalAnalyzer
from technical_analysis import TechnicalAnalyzer
from investment_scorer import InvestmentScorer
from report_generator import ReportGenerator


class AIPSOrchestrator:
    """Main orchestrator for AIPS validation workflow"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize AIPS with configuration"""
        
        # Load configuration
        self.config = load_config(config_path)
        
        # Setup logging
        log_level = self.config.get('output', {}).get('log_level', 'INFO')
        log_file = self.config.get('output', {}).get('log_file', 'logs/aips.log')
        self.logger = setup_logging(log_level, log_file)
        
        # Ensure directories exist
        ensure_directories()
        
        # Initialize components
        self.logger.info("Initializing AIPS components...")
        self.profile_validator = CompanyProfileValidator(self.config)
        self.fundamental_analyzer = FundamentalAnalyzer(self.config)
        self.technical_analyzer = TechnicalAnalyzer(self.config)
        self.investment_scorer = InvestmentScorer(self.config)
        self.report_generator = ReportGenerator(self.config)
        
        self.logger.info("AIPS initialization complete")
    
    def validate_single_stock(self, symbol: str, generate_report: bool = True) -> Dict[str, Any]:
        """
        Validate a single stock
        
        Args:
            symbol: Stock symbol
            generate_report: Whether to generate detailed report
        
        Returns:
            Dictionary with validation results
        """
        self.logger.info(f"=" * 80)
        self.logger.info(f"Starting validation for {symbol}")
        self.logger.info(f"=" * 80)
        
        try:
            # Step 1: Company Profile Validation
            self.logger.info("Step 1/4: Validating company profile...")
            profile = self.profile_validator.validate_company(symbol)
            
            if profile.get('error'):
                self.logger.error(f"Profile validation failed: {profile.get('error')}")
                return self._create_failed_result(symbol, profile.get('error'))
            
            # Check price range
            if not profile.get('within_price_range', False):
                self.logger.warning(f"{symbol} is outside target price range")
            
            # Step 2: Fundamental Analysis
            self.logger.info("Step 2/4: Performing fundamental analysis...")
            fundamental = self.fundamental_analyzer.analyze(symbol)
            
            if fundamental.get('error'):
                self.logger.warning(f"Fundamental analysis had issues: {fundamental.get('error')}")
            
            # Step 3: Technical Analysis
            self.logger.info("Step 3/4: Performing technical analysis...")
            technical = self.technical_analyzer.analyze(symbol)
            
            if technical.get('error'):
                self.logger.warning(f"Technical analysis had issues: {technical.get('error')}")
            
            # Step 4: Investment Scoring
            self.logger.info("Step 4/4: Calculating investment score...")
            score_result = self.investment_scorer.calculate_investment_score(
                profile, fundamental, technical
            )
            
            # Generate report if requested
            if generate_report:
                self.logger.info("Generating detailed report...")
                report_path = self.report_generator.generate_stock_report(
                    profile, fundamental, technical, score_result
                )
                score_result['report_path'] = report_path
            
            self.logger.info(f"Validation complete for {symbol}")
            self.logger.info(f"Score: {score_result.get('overall_score', 0):.2f}/10")
            self.logger.info(f"Recommendation: {score_result.get('recommendation', 'N/A')}")
            self.logger.info(f"=" * 80)
            
            return {
                'success': True,
                'symbol': symbol,
                'profile': profile,
                'fundamental': fundamental,
                'technical': technical,
                'score_result': score_result
            }
            
        except Exception as e:
            self.logger.error(f"Error validating {symbol}: {e}", exc_info=True)
            return self._create_failed_result(symbol, str(e))
    
    def validate_multiple_stocks(
        self,
        symbols: List[str],
        generate_individual_reports: bool = False,
        generate_summary: bool = True
    ) -> pd.DataFrame:
        """
        Validate multiple stocks
        
        Args:
            symbols: List of stock symbols
            generate_individual_reports: Generate report for each stock
            generate_summary: Generate batch summary report
        
        Returns:
            DataFrame with all results
        """
        self.logger.info(f"Starting batch validation for {len(symbols)} stocks")
        
        # Remove duplicates and validate symbols
        valid_symbols = []
        for symbol in set(symbols):
            if validate_stock_symbol(symbol):
                valid_symbols.append(symbol)
            else:
                self.logger.warning(f"Invalid symbol format: {symbol}")
        
        self.logger.info(f"Processing {len(valid_symbols)} valid symbols")
        
        # Initialize progress tracker
        progress = ProgressTracker(len(valid_symbols))
        
        # Collect results
        all_results = []
        
        for i, symbol in enumerate(valid_symbols, 1):
            self.logger.info(f"\n[{i}/{len(valid_symbols)}] Processing {symbol}")
            
            try:
                result = self.validate_single_stock(symbol, generate_individual_reports)
                
                if result.get('success', False):
                    all_results.append(result['score_result'])
                    progress.update(success=True)
                else:
                    progress.update(success=False)
                
                # Log progress
                self.logger.info(progress.get_status())
                
            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {e}")
                progress.update(success=False)
        
        # Create DataFrame
        if all_results:
            results_df = pd.DataFrame(all_results)
            
            # Sort by overall score
            results_df = results_df.sort_values('overall_score', ascending=False)
            
            # Generate summary report
            if generate_summary:
                summary_path = self.report_generator.generate_batch_summary(results_df)
                self.logger.info(f"Batch summary report: {summary_path}")
            
            # Print summary statistics
            self._print_batch_summary(results_df)
            
            return results_df
        else:
            self.logger.error("No successful validations")
            return pd.DataFrame()
    
    def validate_stocks_from_file(
        self,
        file_path: str,
        symbol_column: str = 'symbol'
    ) -> pd.DataFrame:
        """
        Validate stocks from CSV or Excel file
        
        Args:
            file_path: Path to file containing stock symbols
            symbol_column: Name of column containing symbols
        
        Returns:
            DataFrame with results
        """
        self.logger.info(f"Loading stocks from {file_path}")
        
        try:
            # Load file
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format. Use CSV or Excel.")
            
            # Extract symbols
            if symbol_column not in df.columns:
                raise ValueError(f"Column '{symbol_column}' not found in file")
            
            symbols = df[symbol_column].tolist()
            self.logger.info(f"Loaded {len(symbols)} symbols from file")
            
            # Validate stocks
            return self.validate_multiple_stocks(symbols)
            
        except Exception as e:
            self.logger.error(f"Error loading stocks from file: {e}")
            return pd.DataFrame()
    
    def get_top_picks(self, results_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """Get top N stock recommendations"""
        
        # Filter for suitable investments only
        suitable = results_df[
            results_df['recommendation'].str.contains('Suitable', na=False)
        ]
        
        # Sort by score
        top_picks = suitable.nlargest(top_n, 'overall_score')
        
        return top_picks
    
    def filter_by_criteria(
        self,
        results_df: pd.DataFrame,
        min_score: float = None,
        max_score: float = None,
        min_liquidity: bool = True,
        categories: List[str] = None
    ) -> pd.DataFrame:
        """Filter results by criteria"""
        
        filtered = results_df.copy()
        
        if min_score is not None:
            filtered = filtered[filtered['overall_score'] >= min_score]
        
        if max_score is not None:
            filtered = filtered[filtered['overall_score'] <= max_score]
        
        if min_liquidity:
            filtered = filtered[filtered['is_liquid'] == True]
        
        if categories:
            filtered = filtered[filtered['category'].isin(categories)]
        
        return filtered
    
    def _create_failed_result(self, symbol: str, error: str) -> Dict[str, Any]:
        """Create failed result"""
        return {
            'success': False,
            'symbol': symbol,
            'error': error,
            'score_result': {
                'symbol': symbol,
                'overall_score': 0.0,
                'recommendation': 'Validation Failed',
                'error': error
            }
        }
    
    def _print_batch_summary(self, results_df: pd.DataFrame):
        """Print summary of batch results"""
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info("BATCH VALIDATION SUMMARY")
        self.logger.info("=" * 80)
        
        total = len(results_df)
        self.logger.info(f"Total stocks analyzed: {total}")
        
        # Category breakdown
        if 'category' in results_df.columns:
            self.logger.info("\nCategory Distribution:")
            for category, count in results_df['category'].value_counts().items():
                self.logger.info(f"  {category}: {count} ({count/total*100:.1f}%)")
        
        # Recommendation breakdown
        if 'recommendation' in results_df.columns:
            suitable = len(results_df[results_df['recommendation'].str.contains('Suitable', na=False)])
            risky = len(results_df[results_df['recommendation'].str.contains('Risky', na=False)])
            
            self.logger.info(f"\nSuitable for investment: {suitable} ({suitable/total*100:.1f}%)")
            self.logger.info(f"Risky/Not recommended: {risky} ({risky/total*100:.1f}%)")
        
        # Score statistics
        if 'overall_score' in results_df.columns:
            self.logger.info(f"\nScore Statistics:")
            self.logger.info(f"  Average: {results_df['overall_score'].mean():.2f}")
            self.logger.info(f"  Median: {results_df['overall_score'].median():.2f}")
            self.logger.info(f"  Highest: {results_df['overall_score'].max():.2f}")
            self.logger.info(f"  Lowest: {results_df['overall_score'].min():.2f}")
        
        # Top 5 stocks
        if len(results_df) > 0:
            self.logger.info("\nTop 5 Stocks by Score:")
            top_5 = results_df.nlargest(5, 'overall_score')
            for idx, row in top_5.iterrows():
                self.logger.info(
                    f"  {row.get('symbol', 'N/A')}: "
                    f"{row.get('overall_score', 0):.2f} - "
                    f"{row.get('recommendation', 'N/A')}"
                )
        
        self.logger.info("=" * 80 + "\n")


def main():
    """Main entry point for AIPS"""
    
    parser = argparse.ArgumentParser(
        description='AIPS - AI-Driven Penny Stock Validation System'
    )
    
    parser.add_argument(
        'symbols',
        nargs='*',
        help='Stock symbols to analyze (e.g., RELIANCE INFY TCS)'
    )
    
    parser.add_argument(
        '-f', '--file',
        help='CSV or Excel file containing stock symbols'
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '-r', '--report',
        action='store_true',
        help='Generate individual reports for each stock'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output file for results (CSV)'
    )
    
    args = parser.parse_args()
    
    # Initialize AIPS
    try:
        aips = AIPSOrchestrator(args.config)
    except Exception as e:
        print(f"Error initializing AIPS: {e}")
        sys.exit(1)
    
    # Process stocks
    if args.file:
        # Process from file
        results_df = aips.validate_stocks_from_file(args.file)
    elif args.symbols:
        # Process individual symbols
        if len(args.symbols) == 1:
            # Single stock
            result = aips.validate_single_stock(args.symbols[0], generate_report=True)
            if result.get('success'):
                print(f"\n✓ Validation complete for {args.symbols[0]}")
                print(f"Score: {result['score_result']['overall_score']:.2f}/10")
                print(f"Recommendation: {result['score_result']['recommendation']}")
                if 'report_path' in result['score_result']:
                    print(f"Report: {result['score_result']['report_path']}")
            else:
                print(f"\n✗ Validation failed: {result.get('error')}")
            sys.exit(0)
        else:
            # Multiple stocks
            results_df = aips.validate_multiple_stocks(
                args.symbols,
                generate_individual_reports=args.report
            )
    else:
        parser.print_help()
        sys.exit(1)
    
    # Save results
    if not results_df.empty and args.output:
        results_df.to_csv(args.output, index=False)
        print(f"\nResults saved to: {args.output}")
    
    print("\nAIPS validation complete!")


if __name__ == "__main__":
    main()
