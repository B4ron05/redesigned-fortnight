import pandas as pd
from fredapi import Fred
import time  # <--- Add this line right here!

def fetch_fred_history(api_key):
    # ... rest of your code ...
    """
    Pulls historical government macro data.
    Pulls the entire series to protect the API rate limit.
    """
    fred = Fred(api_key=api_key)
    
    metrics = {
        "GDP Growth QoQ (%)": {"id": "GDPC1", "units": "pch", "divide": 1},
        "Retail Sales MoM (%)": {"id": "RSAFS", "units": "pch", "divide": 1},      
        "Consumer Confidence": {"id": "UMCSENT", "units": "lin", "divide": 1},
        "CPI YoY (%)": {"id": "CPIAUCSL", "units": "pc1", "divide": 1},             
        "PPI YoY (%)": {"id": "PPIFIS", "units": "pc1", "divide": 1},               
        "PCE YoY (%)": {"id": "PCEPI", "units": "pc1", "divide": 1},             
        "10 Yr Yield (%)": {"id": "GS10", "units": "lin", "divide": 1},
        "Non-Farm Payroll (k)": {"id": "PAYEMS", "units": "chg", "divide": 1},      
        "Unemployment Rate (%)": {"id": "UNRATE", "units": "lin", "divide": 1},
        "Weekly Jobless Claims (k)": {"id": "ICSA", "units": "lin", "divide": 1000},
        "JOLTS Openings (M)": {"id": "JTSJOL", "units": "lin", "divide": 1000}
    }
    
    results = {}
    for name, config in metrics.items():
        try:
            time.sleep(0.2) # THIS FIXES THE RATE LIMIT CRASH
            data = fred.get_series(config["id"], units=config["units"])
            
            df = pd.DataFrame({
                "Date": data.index,
                "Value": (data / config["divide"]).round(2)
            }).set_index("Date")
            
            results[name] = df
        except Exception as e:
            print(f"Error fetching {name} from FRED: {e}")
            results[name] = pd.DataFrame()
            
    return results