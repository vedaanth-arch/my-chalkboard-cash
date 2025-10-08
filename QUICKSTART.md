# AIPS Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

Open PowerShell in the AIPS directory and run:

```powershell
pip install -r requirements.txt
```

### Step 2: Run Your First Analysis

Analyze a single stock:

```powershell
python aips_main.py RELIANCE
```

### Step 3: View the Results

The system will display:
- Investment Validity Score (0-10)
- Recommendation (Buy/Hold/Sell)
- Key strengths and weaknesses
- Report location

### Step 4: Generate Detailed Report

For a comprehensive HTML report:

```powershell
python aips_main.py RELIANCE -r
```

Open the generated HTML file in `reports/` folder to see:
- Complete score breakdown
- Fundamental metrics
- Technical indicators
- Risk analysis
- Investment recommendation

## 📊 Common Use Cases

### Analyze Multiple Stocks

```powershell
python aips_main.py RELIANCE TCS INFY HDFCBANK ICICIBANK -r -o results.csv
```

### Analyze Stocks from Excel/CSV

1. Create a file `mystocks.csv` with a column named `symbol`:
```csv
symbol
RELIANCE
TCS
INFY
HDFCBANK
```

2. Run analysis:
```powershell
python aips_main.py -f mystocks.csv -r -o analysis_results.csv
```

### Use Python API

Create a file `my_analysis.py`:

```python
from aips_main import AIPSOrchestrator

# Initialize
aips = AIPSOrchestrator()

# Analyze stocks
symbols = ['RELIANCE', 'TCS', 'INFY']
results = aips.validate_multiple_stocks(symbols)

# Get top picks
top_5 = aips.get_top_picks(results, top_n=5)
print(top_5[['symbol', 'overall_score', 'recommendation']])

# Filter by score
good_stocks = aips.filter_by_criteria(results, min_score=6.5)
print(f"Found {len(good_stocks)} stocks with score >= 6.5")
```

Run it:
```powershell
python my_analysis.py
```

## 📁 Output Files

### Reports Directory
- `SYMBOL_report_TIMESTAMP.html` - Interactive HTML report
- `SYMBOL_report_TIMESTAMP.xlsx` - Excel workbook
- `batch_summary_TIMESTAMP.xlsx` - Batch analysis summary

### Logs Directory
- `aips.log` - Detailed execution logs

## ⚙️ Customization

Edit `config.yaml` to change:

```yaml
# Target price range
price_range:
  min: 1.0
  max: 100.0

# Scoring weights (must sum to 100)
scoring_weights:
  company_profile: 15
  fundamental_analysis: 40
  technical_analysis: 30
  risk_factors: 15

# Investment thresholds
fundamental_thresholds:
  min_roe: 10.0          # Minimum Return on Equity
  max_debt_equity: 2.0   # Maximum Debt-to-Equity
  min_current_ratio: 1.0 # Minimum Current Ratio
```

## 💡 Tips

1. **Start Small**: Analyze 1-2 stocks first to understand the output
2. **Review Reports**: HTML reports provide the most comprehensive view
3. **Check Logs**: If something fails, check `logs/aips.log`
4. **Batch Processing**: Use CSV files for analyzing many stocks
5. **Internet Required**: System fetches real-time data from Yahoo Finance

## 🎯 Understanding Scores

| Score Range | Category | Recommendation |
|-------------|----------|----------------|
| 8.0 - 10.0  | Excellent | Strong Buy |
| 7.0 - 7.9   | Very Good | Buy |
| 6.0 - 6.9   | Good | Moderate Buy |
| 5.0 - 5.9   | Fair | Hold |
| 4.0 - 4.9   | Below Average | Monitor |
| 3.0 - 3.9   | Poor | Consider Selling |
| 0.0 - 2.9   | Very Poor | Avoid |

## 🔍 Example Output

```
==========================================
Starting validation for RELIANCE
==========================================
Step 1/4: Validating company profile...
Step 2/4: Performing fundamental analysis...
Step 3/4: Performing technical analysis...
Step 4/4: Calculating investment score...
Generating detailed report...

Validation complete for RELIANCE
Score: 7.85/10
Recommendation: Suitable for Investment - Buy
==========================================

✓ Analysis complete
Report: reports/RELIANCE_report_20250108_143022.html
```

## ⚠️ Troubleshooting

### "Module not found" error
```powershell
pip install -r requirements.txt --upgrade
```

### "No data available" error
- Check if stock symbol is correct
- Try adding .NS suffix: `RELIANCE.NS`
- Verify internet connection

### Slow performance
- Normal for first run (downloads data)
- Subsequent runs use cached data
- Batch processing is more efficient

## 📚 Next Steps

1. **Read the Full README**: See `README.md` for comprehensive documentation
2. **Explore Examples**: Run `python example_usage.py`
3. **Customize Config**: Adjust `config.yaml` for your needs
4. **Review Reports**: Understand the detailed analysis format

## 🆘 Need Help?

1. Check `logs/aips.log` for detailed error messages
2. Review `README.md` for comprehensive documentation
3. Look at `example_usage.py` for code samples
4. Verify all dependencies are installed

---

**Happy Investing! 📈**

*Remember: This is a research tool. Always consult financial advisors before making investment decisions.*
