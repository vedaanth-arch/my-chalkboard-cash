# AIPS - AI-Driven Penny Stock Validation System

## 🎯 Overview

**AIPS (AI-Driven Penny Stock Validation System)** is a comprehensive, data-driven stock analysis platform specifically designed for Indian penny stocks priced between ₹1 and ₹100. The system performs multi-dimensional validation combining company profile analysis, fundamental metrics, technical indicators, and risk assessment to generate actionable investment recommendations.

## ✨ Features

### 🏢 Company Profile Validation
- Comprehensive company background analysis
- Sector and industry classification
- Ownership structure and promoter holding analysis
- Governance risk assessment
- Red flag identification (litigation, regulatory issues, etc.)
- Market capitalization categorization

### 💰 Fundamental Analysis
- Financial statement analysis (Balance Sheet, P&L, Cash Flow)
- Key financial metrics calculation:
  - Return on Equity (ROE)
  - Profit margins
  - Debt-to-Equity ratio
  - Current ratio and liquidity metrics
  - Revenue and earnings growth trends
- 5-year historical trend analysis
- Dividend history evaluation
- Valuation metrics (P/E, P/B, EV/EBITDA)

### 📊 Technical Analysis
- Technical indicators:
  - Moving Averages (SMA, EMA)
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - Stochastic Oscillator
- Support and resistance level identification
- Volume analysis and liquidity assessment
- Volatility analysis
- Trend detection (short, medium, long-term)
- Trading signal generation

### 🎯 Investment Scoring
- Comprehensive scoring system (0-10 scale)
- Weighted scoring across multiple dimensions:
  - Company Profile (15%)
  - Fundamental Analysis (40%)
  - Technical Analysis (30%)
  - Risk Factors (15%)
- Clear investment recommendations:
  - Suitable for Investment (Strong Buy/Buy/Moderate Buy)
  - Hold
  - Risky/Not Recommended
- Risk level assessment
- Expected return potential estimation

### 📈 Reporting & Visualization
- Multi-format reports:
  - Interactive HTML reports
  - Excel spreadsheets
  - JSON data exports
- Comprehensive stock dashboards
- Batch summary reports
- Top picks identification
- Risk and return analysis

## 🚀 Quick Start

### Installation

1. **Clone or download the AIPS project**

2. **Install dependencies:**
```powershell
pip install -r requirements.txt
```

3. **Configure settings (optional):**
   - Edit `config.yaml` to customize analysis parameters
   - Copy `.env.example` to `.env` and add any API keys

### Basic Usage

#### Analyze a Single Stock

```powershell
python aips_main.py RELIANCE
```

#### Analyze Multiple Stocks

```powershell
python aips_main.py RELIANCE INFY TCS TATAMOTORS HDFCBANK
```

#### Analyze Stocks from a File

```powershell
# Create a CSV file with stock symbols
python aips_main.py -f stocks.csv -r -o results.csv
```

#### Generate Detailed Reports

```powershell
python aips_main.py RELIANCE -r
```

### Command Line Options

```
usage: aips_main.py [-h] [-f FILE] [-c CONFIG] [-r] [-o OUTPUT] [symbols ...]

positional arguments:
  symbols               Stock symbols to analyze (e.g., RELIANCE INFY TCS)

optional arguments:
  -h, --help           Show this help message and exit
  -f FILE, --file FILE CSV or Excel file containing stock symbols
  -c CONFIG            Path to configuration file (default: config.yaml)
  -r, --report         Generate individual reports for each stock
  -o OUTPUT            Output file for results (CSV)
```

## 📚 Programmatic Usage

### Python API

```python
from aips_main import AIPSOrchestrator

# Initialize AIPS
aips = AIPSOrchestrator('config.yaml')

# Validate single stock
result = aips.validate_single_stock('RELIANCE', generate_report=True)
print(f"Score: {result['score_result']['overall_score']:.2f}/10")
print(f"Recommendation: {result['score_result']['recommendation']}")

# Validate multiple stocks
symbols = ['RELIANCE', 'INFY', 'TCS', 'TATAMOTORS']
results_df = aips.validate_multiple_stocks(symbols, generate_summary=True)

# Get top picks
top_picks = aips.get_top_picks(results_df, top_n=5)
print(top_picks[['symbol', 'overall_score', 'recommendation']])

# Filter by criteria
filtered = aips.filter_by_criteria(
    results_df,
    min_score=6.0,
    min_liquidity=True,
    categories=['Excellent', 'Very Good']
)
```

### Using Individual Modules

```python
from utils import load_config
from company_profile import CompanyProfileValidator
from fundamental_analysis import FundamentalAnalyzer
from technical_analysis import TechnicalAnalyzer
from investment_scorer import InvestmentScorer

# Load config
config = load_config('config.yaml')

# Company profile
profile_validator = CompanyProfileValidator(config)
profile = profile_validator.validate_company('RELIANCE')

# Fundamental analysis
fundamental_analyzer = FundamentalAnalyzer(config)
fundamentals = fundamental_analyzer.analyze('RELIANCE')

# Technical analysis
technical_analyzer = TechnicalAnalyzer(config)
technicals = technical_analyzer.analyze('RELIANCE')

# Investment scoring
scorer = InvestmentScorer(config)
score = scorer.calculate_investment_score(profile, fundamentals, technicals)
print(f"Investment Validity Score: {score['overall_score']:.2f}/10")
```

## ⚙️ Configuration

Edit `config.yaml` to customize:

- **Price Range:** Min/max price for penny stocks
- **Market Settings:** Exchange (NSE/BSE), suffixes
- **Analysis Periods:** Short/medium/long-term timeframes
- **Technical Indicators:** MA periods, RSI thresholds, MACD settings
- **Fundamental Thresholds:** Min market cap, debt ratios, margins
- **Scoring Weights:** Customize weight distribution
- **Risk Flags:** Define red flag criteria
- **Output Settings:** Report formats, directories

Example configuration:

```yaml
price_range:
  min: 1.0
  max: 100.0

scoring_weights:
  company_profile: 15
  fundamental_analysis: 40
  technical_analysis: 30
  risk_factors: 15

fundamental_thresholds:
  min_roe: 10.0
  max_debt_equity: 2.0
  min_current_ratio: 1.0
```

## 📊 Understanding the Scores

### Investment Validity Score (0-10)

- **8.0 - 10.0:** Excellent - Strong Buy
- **7.0 - 7.9:** Very Good - Buy
- **6.0 - 6.9:** Good - Moderate Buy
- **5.0 - 5.9:** Fair - Hold
- **4.0 - 4.9:** Below Average - Monitor
- **3.0 - 3.9:** Poor - Consider Selling
- **0.0 - 2.9:** Very Poor - Avoid

### Component Scores

1. **Company Profile Score (15% weight)**
   - Evaluates company background, governance, ownership structure
   - Identifies red flags and regulatory issues

2. **Fundamental Score (40% weight)**
   - Analyzes financial health, profitability, growth
   - Assesses valuation and dividend history

3. **Technical Score (30% weight)**
   - Evaluates price momentum, trends, indicators
   - Assesses liquidity and volatility

4. **Risk Score (15% weight)**
   - Identifies potential risks (debt, liquidity, governance)
   - Evaluates red flags and warning signs

## 📁 Project Structure

```
AIPS/
├── aips_main.py              # Main orchestrator script
├── company_profile.py         # Company validation module
├── fundamental_analysis.py    # Fundamental analysis module
├── technical_analysis.py      # Technical analysis module
├── investment_scorer.py       # Scoring and recommendation engine
├── report_generator.py        # Report generation module
├── utils.py                   # Utility functions
├── config.yaml                # Configuration file
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
├── README.md                  # This file
├── example_usage.py           # Usage examples
├── reports/                   # Generated reports directory
├── logs/                      # Log files directory
├── data/                      # Data cache directory
└── cache/                     # Cache directory
```

## 🔧 Troubleshooting

### Common Issues

1. **"No data available" errors:**
   - Check if the stock symbol is correct (use NSE/BSE format)
   - Verify the stock is actively traded
   - Try adding .NS (NSE) or .BO (BSE) suffix

2. **Low data quality warnings:**
   - Some penny stocks have limited historical data
   - Results may be less reliable for very small companies

3. **Installation issues:**
   - Ensure Python 3.8+ is installed
   - Install Visual C++ Build Tools for ta-lib on Windows
   - Use `pip install --upgrade pip` before installing requirements

### Getting Help

- Check the logs in `logs/aips.log` for detailed error messages
- Review the configuration in `config.yaml`
- Ensure all dependencies are installed correctly

## ⚠️ Disclaimer

**IMPORTANT:** This system is for informational and educational purposes only. It should NOT be considered as professional investment advice. 

- Always conduct your own thorough research
- Consult with qualified financial advisors
- Understand the risks involved in penny stock investing
- Past performance does not guarantee future results
- The developers are not responsible for any investment losses

Penny stocks are highly speculative and risky investments. Only invest what you can afford to lose.

## 📝 License

This project is provided as-is for educational and research purposes.

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Additional data sources integration
- Enhanced web scraping for regulatory data
- Real-time price alerts
- Portfolio tracking features
- Machine learning-based predictions
- Advanced charting and visualization

## 📧 Support

For questions, issues, or feature requests, please check the documentation or review the example usage files.

## 🔄 Version History

### Version 1.0.0 (Current)
- Initial release
- Company profile validation
- Fundamental analysis engine
- Technical analysis with 15+ indicators
- Investment scoring system
- Multi-format reporting (HTML, Excel, JSON)
- Batch processing capabilities
- Comprehensive configuration options

---

**Made with ❤️ for Indian stock market investors**

*Remember: Invest wisely, diversify, and never invest more than you can afford to lose.*
