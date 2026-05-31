import requests
from datetime import datetime, timedelta

def fetch_finnhub_forecasts(api_key):
    """
    Queries Finnhub's Economic Calendar.
    - De-annualizes US GDP Growth to QoQ.
    - Captures pure Headline data (blocking 'Core') for Inflation.
    - Safely scales jobs data (NFP, JOLTS).
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=45)
    
    from_date = start_date.strftime("%Y-%m-%d")
    to_date = end_date.strftime("%Y-%m-%d")
    
    url = f"https://finnhub.io/api/v1/calendar/economic?from={from_date}&to={to_date}&token={api_key}"
    
    # Initialize dictionary to perfectly match scoring_logic.py
    results = {
        "GDP Growth QoQ": {"value": "N/A", "forecast": "N/A", "difference": 0},
        "Retail Sales MoM": {"value": "N/A", "forecast": "N/A", "difference": 0},
        "Real Personal Income MoM": {"value": "N/A", "forecast": "N/A", "difference": 0},
        "CPI YoY": {"value": "N/A", "forecast": "N/A", "difference": 0},
        "PPI YoY": {"value": "N/A", "forecast": "N/A", "difference": 0},
        "PCE YoY": {"value": "N/A", "forecast": "N/A", "difference": 0},
        "10 Yr Yield": {"value": "N/A", "forecast": "N/A", "difference": 0}, 
        "Non-Farm Payroll": {"value": "N/A", "forecast": "N/A", "difference": 0}, 
        "Unemployment Rate %": {"value": "N/A", "forecast": "N/A", "difference": 0},
        "Weekly Jobless Claims": {"value": "N/A", "forecast": "N/A", "difference": 0},
        "JOLTS Job Openings": {"value": "N/A", "forecast": "N/A", "difference": 0}
    }
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            events_list = data.get("economicCalendar", [])
            
            # Sort chronologically (oldest to newest) to let latest prints overwrite
            events_list = sorted(events_list, key=lambda x: x.get("time", ""))
            
            for item in events_list:
                if item.get("country") != "US":
                    continue
                    
                title = item.get("event", "").lower()
                actual = item.get("actual")
                estimate = item.get("estimate")
                
                if actual is not None:
                    safe_est = estimate if estimate is not None else actual
                    diff = round(actual - safe_est, 2)
                    
                    # CORE BLOCKER
                    is_core = "core" in title or "ex" in title or "excluding" in title
                    
                    # 1. NON-FARM PAYROLLS (Blocks ADP, allows Private as fallback if Headline is missing)
                    if ("nonfarm" in title or "non-farm" in title) and "adp" not in title:
                        val = actual / 1000 if actual > 1000 else actual
                        est = safe_est / 1000 if abs(safe_est) > 1000 else safe_est
                        results["Non-Farm Payroll"] = {"value": round(val, 1), "forecast": round(est, 1) if estimate is not None else "N/A", "difference": round(val - est, 1)}
                        
                    # 2. UNEMPLOYMENT RATE
                    elif "unemployment rate" in title:
                        results["Unemployment Rate %"] = {"value": round(actual, 2), "forecast": round(safe_est, 2) if estimate is not None else "N/A", "difference": diff}
                        
                    # 3. WEEKLY JOBLESS CLAIMS
                    elif "initial jobless claims" in title:
                        val = actual / 1000 if actual > 1000 else actual
                        est = safe_est / 1000 if abs(safe_est) > 1000 else safe_est
                        results["Weekly Jobless Claims"] = {"value": round(val, 1), "forecast": round(est, 1) if estimate is not None else "N/A", "difference": round(val - est, 1)}
                        
                    # 4. JOLTS JOB OPENINGS (Math fixed to safely handle millions/thousands)
                    elif "jolts" in title and "opening" in title:
                        if actual > 1000000:
                            val, est = actual / 1000000, safe_est / 1000000
                        elif actual > 1000:
                            val, est = actual / 1000, safe_est / 1000
                        else:
                            val, est = actual, safe_est
                        results["JOLTS Job Openings"] = {"value": round(val, 2), "forecast": round(est, 2) if estimate is not None else "N/A", "difference": round(val - est, 2)}
                        
                    # 5. GDP (De-Annualized to QoQ)
                    elif "gdp" in title and "growth" in title:
                        val, est = actual / 4, safe_est / 4
                        results["GDP Growth QoQ"] = {"value": round(val, 2), "forecast": round(est, 2) if estimate is not None else "N/A", "difference": round(val - est, 2)}
                        
                    # 6. CONSUMER CONFIDENCE (Widened to catch Michigan or CB)
                    elif "consumer" in title and ("confidence" in title or "sentiment" in title):
                        results["Consumer Confidence"] = {"value": round(actual, 2), "forecast": round(safe_est, 2) if estimate is not None else "N/A", "difference": diff}
                        
                    # 7. RETAIL SALES (Headline only)
                    elif "retail sales" in title and not is_core:
                        if "mom" in title or "month" in title:
                            results["Retail Sales MoM"] = {"value": round(actual, 2), "forecast": round(safe_est, 2) if estimate is not None else "N/A", "difference": diff}
                        
                    # 8. CPI (Headline YoY only)
                    elif ("cpi" in title or "inflation" in title) and "yoy" in title and not is_core:
                        results["CPI YoY"] = {"value": round(actual, 2), "forecast": round(safe_est, 2) if estimate is not None else "N/A", "difference": diff}
                        
                    # 9. PPI (Headline YoY only)
                    elif "ppi" in title and "yoy" in title and not is_core:
                        results["PPI YoY"] = {"value": round(actual, 2), "forecast": round(safe_est, 2) if estimate is not None else "N/A", "difference": diff}
                        
                    # 10. PCE (Headline YoY only)
                    elif ("pce" in title or "personal consumption" in title) and not is_core:
                        if "mom" not in title and "qoq" not in title and "quarter" not in title:
                            results["PCE YoY"] = {"value": round(actual, 2), "forecast": round(safe_est, 2) if estimate is not None else "N/A", "difference": diff}
                        
                    # 11. 10-YR YIELD AUCTION
                    elif "10-year note auction" in title or "10-yr note auction" in title:
                        results["10 Yr Yield"] = {"value": round(actual, 2), "forecast": round(safe_est, 2) if estimate is not None else "N/A", "difference": diff}
                        
    except Exception as e:
        print(f"Finnhub API Error: {e}")
        
    return results