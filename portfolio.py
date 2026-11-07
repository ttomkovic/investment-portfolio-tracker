import csv
from market_data import get_current_prices

def load_holdings(file_name: str) -> tuple[list[dict], list[str]]:
    with open(file_name, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        required_columns = {"symbol", "shares_quantity", "purchase_price"}

        if reader.fieldnames is None or not required_columns.issubset(reader.fieldnames):
            raise ValueError("Some required columns are missing")
        
        holdings = list(reader)
        valid_holdings = []
        warnings = []
        for i, holding in enumerate(holdings, start=2):
            holding['symbol'] = holding['symbol'].strip().upper()
            if not holding['symbol']:
                warnings.append(f"Row {i}: Symbol is missing")
                continue
            
            try:
                holding['shares_quantity'] = float(holding['shares_quantity'])
                holding['purchase_price'] = float(holding['purchase_price'])
            except (ValueError, TypeError):
                warnings.append(f"Row {i}: Invalid numeric value")
                continue

            if holding['shares_quantity'] <= 0:
                warnings.append(f"Row {i}: Shares quantity must be positive")
                continue

            if holding['purchase_price'] <= 0:
                warnings.append(f"Row {i}: Purchase price must be positive")
                continue

            valid_holdings.append(holding)
    return valid_holdings, warnings 


def calculate_investment_cost(holdings: list[dict]) -> list[dict]:
    results = []
    for holding in holdings:
        cost = holding["shares_quantity"] * holding["purchase_price"]
        holding_dict = {
            **holding,
            "investment_cost": cost
        }
        results.append(holding_dict)

    return results
        

def calculate_performance(holdings: list[dict], current_prices: dict) -> list[dict]:
    results = []

    for holding in holdings:
        symbol = holding['symbol']
        
        if symbol not in current_prices:
            raise ValueError(f"Missing current price for {symbol}")

        current_price = current_prices[symbol]

        current_value = holding["shares_quantity"] * current_price
        gain_loss = current_value - holding["investment_cost"]
        return_pct = gain_loss / holding["investment_cost"] * 100

        holding_new = {
            **holding,
            "current_value": current_value,
            "gain_loss": gain_loss,
            "return_pct": return_pct
        }
        results.append(holding_new)
    
    return results

def calculate_portfolio_totals(holdings: list[dict]) -> dict:

    if holdings == []:
        raise ValueError("Cannot calculate totals for an empty portfolio")
    
    total_investment_cost = 0
    total_current_value =0

    for holding in holdings:
        total_investment_cost += holding["investment_cost"]
        total_current_value += holding["current_value"]

    total_gain_loss = total_current_value - total_investment_cost
    portfolio_return_pct = total_gain_loss / total_investment_cost * 100

    holdings_portfolio = {
        "total_investment_cost": total_investment_cost,
        "total_current_value": total_current_value,
        "total_gain_loss": total_gain_loss,
        "portfolio_return_pct": portfolio_return_pct
    }

    return holdings_portfolio

def build_report_from_holdings(holdings: list[dict], warnings: list[str], current_prices: dict) -> dict:
    if not holdings:
        raise ValueError("No valid holdings found in the CSV file")
    
    holdings_with_investment_cost = calculate_investment_cost(holdings)
    holdings_with_performance = calculate_performance(holdings_with_investment_cost, current_prices)
    holdings_totals = calculate_portfolio_totals(holdings_with_performance)

    result = {
        "holdings": holdings_with_performance,
        "totals": holdings_totals,
        "warnings": warnings
    }

    return result

def build_portfolio_report(file_name: str, current_prices: dict) -> dict:
    holdings, warnings = load_holdings(file_name)

    result = build_report_from_holdings(holdings, warnings, current_prices)

    return result

def format_portfolio_report(report: dict) -> str:
    title = "INVESTMENT PORTFOLIO REPORT\n\n"

    all_holdings = ""
    for holding in report["holdings"]:
        symbol = holding["symbol"]
        shares = holding["shares_quantity"]
        investment_cost = holding["investment_cost"]
        current_value = holding["current_value"]
        gain_loss = holding["gain_loss"]
        sign_gain_loss = "+" if gain_loss >= 0 else "-"
        return_pct = holding["return_pct"]
        individual_holdings = (
            f"{symbol.upper()}\n"
            + f"  Shares: {shares:,.2f}\n"
            + f"  Investment Cost: ${investment_cost:,.2f}\n"
            + f"  Current Value: ${current_value:,.2f}\n"
            + f"  Gain/Loss: {sign_gain_loss}${abs(gain_loss):,.2f}\n"
            + f"  Return: {return_pct:+.2f}%\n\n"
            )
        all_holdings += individual_holdings
        
    totals = report["totals"]
    heading = "PORTFOLIO TOTALS\n"
    total_investment_cost = totals["total_investment_cost"]
    total_current_value = totals["total_current_value"]
    total_gain_loss = totals["total_gain_loss"]
    sign_total_gain_loss = "+" if total_gain_loss >= 0 else "-"
    portfolio_return_pct = totals["portfolio_return_pct"]

    formatted_report = (
        title
        + all_holdings
        + heading
        + f"Investment Cost: ${total_investment_cost:,.2f}\n"
        + f"Current Value: ${total_current_value:,.2f}\n"
        + f"Gain/Loss: {sign_total_gain_loss}${abs(total_gain_loss):,.2f}\n"
        + f"Return: {portfolio_return_pct:+,.2f}%"
        )

    warnings = report.get("warnings", [])
    if warnings:
        formatted_report += "\n\nDATA VALIDATION WARNINGS\n"
        for message in warnings:
            formatted_report += message + "\n"

    return formatted_report

def get_unique_symbols(holdings: list[dict]) -> list[str]:
    
    unique_symbols = []
    seen_symbols = set()

    for holding in holdings:
        symbol = holding["symbol"]
        
        if symbol not in seen_symbols:
            unique_symbols.append(symbol)
            seen_symbols.add(symbol)

    return unique_symbols

def build_live_portfolio_report(file_name: str) -> dict:
    holdings, warnings = load_holdings(file_name)

    if not holdings:
        raise ValueError("No data available")
    
    symbols = get_unique_symbols(holdings)
    prices, errors = get_current_prices(symbols)

    if len(prices) != len(symbols):
        raise ValueError(f"Prices are missing for the following symbols: {errors}")

    report = build_report_from_holdings(holdings, warnings, prices)

    return report
    

if __name__ == "__main__":
    current_prices = {
        "AAPL": 150.0,
        "MSFT": 380.0,
        }  

    print("INVESTMENT PORTFOLIO TRACKER\nSelect price source:\n1. Manual prices (demo)\n2. Live prices (Alpha Vantage)")
    choice = input("Enter choice: ")

    try:
        if choice == "1":
            print("Manual prices selected")
            report = build_portfolio_report("data/holdings.csv", current_prices)
        elif choice == "2":
            print("Live prices selected")
            report = build_live_portfolio_report("data/holdings.csv")
        else:
            print("Invalid choice")
            raise SystemExit(1)
    except ValueError as error:
        print(f"Error: {error}")
        raise SystemExit(1)

    formatted_report = format_portfolio_report(report)
    print(formatted_report)
