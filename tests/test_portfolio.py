import pytest
from unittest.mock import Mock, patch
from portfolio import load_holdings, calculate_investment_cost, calculate_performance, calculate_portfolio_totals, build_portfolio_report, format_portfolio_report, get_unique_symbols, build_live_portfolio_report
from market_data import extract_price, get_current_prices
import requests

def test_load_valid_holdings(tmp_path):
    csv_file = tmp_path / "holdings.csv"
    csv_file.write_text("symbol,shares_quantity,purchase_price\nAAPL,5,180.00\nMSFT,3,400.00", encoding="utf-8")

    holdings, warnings = load_holdings(csv_file)
    assert len(holdings) == 2
    assert holdings[0]["shares_quantity"] == 5.0
    assert isinstance(holdings[0]["shares_quantity"], float)
    assert holdings[1]["symbol"] == "MSFT"
    assert warnings == []

def test_load_invalid_holdings(tmp_path):
    csv_file = tmp_path / "holdings.csv"
    csv_file.write_text("symbol,shares_quantity,purchase_price\nAAPL,5,180.00\nTSLA,-2,250.00\nMSFT,3,400.00\nGOOG,five,150.00", encoding="utf-8")

    holdings, warnings = load_holdings(csv_file)
    
    assert len(holdings) == 2

    assert holdings[0]["symbol"] == "AAPL"
    assert holdings[1]["symbol"] == "MSFT"

    assert isinstance(holdings[0]["shares_quantity"], float)
    assert isinstance(holdings[1]["shares_quantity"], float)

    assert holdings[0]["shares_quantity"] == 5.0
    assert holdings[1]["shares_quantity"] == 3.0

    assert len(warnings) == 2
    assert "Row 3: Shares quantity must be positive" in warnings
    assert "Row 5: Invalid numeric value" in warnings

def test_symbol_normalization(tmp_path):
    csv_file = tmp_path / "holdings.csv"
    csv_file.write_text("symbol,shares_quantity,purchase_price\n  aapl  ,5,180.00\nmsft,3,400.00\n   ,2,150.00", encoding="utf-8")

    holdings, warnings = load_holdings(csv_file)

    assert len(holdings) == 2
    assert holdings[0]["symbol"] == "AAPL"
    assert holdings[1]["symbol"] == "MSFT"
    assert "Row 4: Symbol is missing" in warnings

def test_missing_numeric_value(tmp_path):
    csv_file = tmp_path / "holdings.csv"
    csv_file.write_text("symbol,shares_quantity,purchase_price\nAAPL,5,180.00\nMSFT,3\nNVDA,10,120.00\nTSLA,,130.00", encoding="utf-8")

    holdings, warnings = load_holdings(csv_file)

    assert len(holdings) == 2
    assert holdings[0]["symbol"] == "AAPL"
    assert holdings[1]["symbol"] == "NVDA"
    assert "Row 3: Invalid numeric value" in warnings
    assert "Row 5: Invalid numeric value" in warnings

def test_missing_required_column(tmp_path):
    csv_file = tmp_path / "holdings.csv"
    csv_file.write_text("symbol,shares_quantity\nAAPL,5\nMSFT,3", encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        load_holdings(csv_file)
    assert str(exc_info.value) == "Some required columns are missing"


def test_empty_csv_file(tmp_path):
    csv_file = tmp_path / "holdings.csv"
    csv_file.write_text("", encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        load_holdings(csv_file)
    assert str(exc_info.value) == "Some required columns are missing"

def test_calculate_investment_cost():
    holdings = [
    {"symbol": "AAPL", "shares_quantity": 5.0, "purchase_price": 180.0},
    {"symbol": "MSFT", "shares_quantity": 3.0, "purchase_price": 400.0}
    ]
    data = calculate_investment_cost(holdings)

    assert data[0]["investment_cost"] == 900.0
    assert data[1]["investment_cost"] == 1200.0
    assert "investment_cost" not in holdings[0]
    assert "investment_cost" not in holdings[1] 

def test_calculate_performance():   
    holdings = [
        {
            "symbol": "AAPL",
            "shares_quantity": 5.0,
            "purchase_price": 180.0,
            "investment_cost": 900.0
        },
        {
            "symbol": "MSFT",
            "shares_quantity": 3.0,
            "purchase_price": 400.0,
            "investment_cost": 1200.0
        }
    ]

    current_prices = {
        "AAPL": 200.0,
        "MSFT": 380.0
    }

    data = calculate_performance(holdings, current_prices)

    assert "current_value" not in holdings[0]

    assert data[0]["current_value"] == 1000.0
    assert data[0]["gain_loss"] == 100.0
    assert data[0]["return_pct"] == pytest.approx(11.11111111)

    assert data[1]["current_value"] == 1140.0
    assert data[1]["gain_loss"] == -60.0
    assert data[1]["return_pct"] == pytest.approx(-5.00)

def test_calculate_performance_missing_price():
    holdings = [
        {
            "symbol": "AAPL",
            "shares_quantity": 5.0,
            "purchase_price": 180.0,
            "investment_cost": 900.0
        },
        {
            "symbol": "MSFT",
            "shares_quantity": 3.0,
            "purchase_price": 400.0,
            "investment_cost": 1200.0
        },
        {
            "symbol": "TSLA",
            "shares_quantity": 3.0,
            "purchase_price": 100.0,
            "investment_cost": 300.0
        }
    ]
    
    current_prices = {
        "AAPL": 200.0,
        "MSFT": 380.0
    }

    with pytest.raises(ValueError) as exc_info:
        calculate_performance(holdings, current_prices)
    assert str(exc_info.value) == "Missing current price for TSLA"

def test_calculate_portfolio_totals():
    holdings = [
        {
            "symbol": "AAPL",
            "investment_cost": 900.0,
            "current_value": 1000.0
        },
        {
            "symbol": "MSFT",
            "investment_cost": 1200.0,
            "current_value": 1140.0
        }
    ]

    data = calculate_portfolio_totals(holdings)

    assert data["total_investment_cost"] == 2100.0
    assert data["total_current_value"] == 2140.0
    assert data["total_gain_loss"] == 40.0
    assert data["portfolio_return_pct"] == pytest.approx(1.9047619047)

def test_empty_holdings():
    holdings = []

    with pytest.raises(ValueError) as exc_info:
        calculate_portfolio_totals(holdings)
    assert str(exc_info.value) == "Cannot calculate totals for an empty portfolio"

def test_build_portfolio_report(tmp_path):
    csv_content = (
        "symbol,shares_quantity,purchase_price\n"
        "AAPL,5,180\n"
        "MSFT,3,400\n"
    )
    current_prices = {
        "AAPL": 150.0,
        "MSFT": 380.0
    }    

    csv_file = tmp_path / "holdings.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    report = build_portfolio_report(csv_file, current_prices)

    assert len(report["holdings"]) == 2
    assert report["holdings"][0]["investment_cost"] == 900.0
    assert report["holdings"][0]["current_value"] == 750.0
    assert report["totals"]["total_gain_loss"] == -210.0

def test_build_portfolio_report_no_valid_holdings(tmp_path):
    
    current_prices = {}  
    
    csv_file = tmp_path / "holdings.csv"
    csv_file.write_text("symbol,shares_quantity,purchase_price\nAAPL,,100")

    with pytest.raises(ValueError) as exc_info:
        build_portfolio_report(csv_file, current_prices)
    assert str(exc_info.value) == "No valid holdings found in the CSV file"


def test_format_portfolio_report(tmp_path):
    csv_content = (
                "symbol,shares_quantity,purchase_price\n"
                "AAPL,5,180\n"
                "MSFT,3,400\n"
            )
    current_prices = {
                "AAPL": 150.0,
                "MSFT": 380.0
            } 
    csv_file = tmp_path / "holdings.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    report = build_portfolio_report(csv_file, current_prices) 
    
    formatted_report = format_portfolio_report(report)

    assert "Investment Cost: $2,100.00" in formatted_report
    assert "Current Value: $1,890.00" in formatted_report
    assert "Gain/Loss: -$210.00" in formatted_report
    assert "Return: -10.00%" in formatted_report
    assert isinstance(formatted_report, str)
    assert "AAPL" in formatted_report
    assert "MSFT" in formatted_report
    assert "Investment Cost: $900.00" in formatted_report
    assert "Return: -5.00%" in formatted_report
    assert "AAPL\n  Shares:" in formatted_report
    assert "\n\nMSFT" in formatted_report

def test_format_single_holding():
    report = {
                "holdings": [
                        {
                        "symbol": "AAPL",
                        "shares_quantity": 5.0,
                        "investment_cost": 900.0,
                        "current_value": 750.0,
                        "gain_loss": -150.0,
                        "return_pct": -150 / 900 * 100
                    }
                ],
                "totals": {
                    "total_investment_cost": 900.0,
                    "total_current_value": 750.0,
                    "total_gain_loss": -150.0,
                    "portfolio_return_pct": -150 / 900 * 100
                }
            }

    formatted_report = format_portfolio_report(report)

    assert "AAPL\n  Shares: 5.00" in formatted_report
    assert "Shares: 5.00" in formatted_report
    assert "Gain/Loss: -$150.00" in formatted_report
    assert "Return: -16.67%" in formatted_report
    assert "DATA VALIDATION WARNINGS" not in formatted_report

def test_format_report_with_warnings():
    report = {
        "holdings": [
            {
                "symbol": "AAPL",
                "shares_quantity": 5.0,
                "investment_cost": 900.0,
                "current_value": 750.0,
                "gain_loss": -150.0,
                "return_pct": -150 / 900 * 100
            }
        ],
        "totals": {
                "total_investment_cost": 900.0,
                "total_current_value": 750.0,
                "total_gain_loss": -150.0,
                "portfolio_return_pct": -150 / 900 * 100
        },
        "warnings": [
                "Row 3: Shares quantity must be positive",
                "Row 5: Invalid numeric value"
        ]
    }

    formatted_report = format_portfolio_report(report)

    assert "DATA VALIDATION WARNINGS" in formatted_report
    assert "Row 3: Shares quantity must be positive" in formatted_report
    assert "Row 5: Invalid numeric value" in formatted_report
    assert formatted_report.index("PORTFOLIO TOTALS") < formatted_report.index("DATA VALIDATION WARNINGS")

def test_get_unique_symbols():
    holdings = [
        {"symbol": "AAPL"},
        {"symbol": "MSFT"},
        {"symbol": "AAPL"},
        {"symbol": "NVDA"},
        {"symbol": "MSFT"}
    ]

    result = get_unique_symbols(holdings)

    assert result == ["AAPL", "MSFT", "NVDA"]
    assert get_unique_symbols([]) == []

def test_extract_price_valid():
    data = {
        "Global Quote": {
            "01. symbol": "AAPL",
            "05. price": "348.2200"
        }
    }

    price = extract_price(data)

    assert price == 348.22
    assert isinstance(price, float)

def test_extract_price_missing():
    data = {
        "Global Quote": {}
    }

    with pytest.raises(ValueError, match="Price is missing"):
        extract_price(data)

def test_extract_price_invalid():
    data = {
        "Global Quote": {
            "05. price": "unavailable"
        }
    }

    with pytest.raises(ValueError, match="Invalid price value"):
        extract_price(data)

@pytest.mark.parametrize(
        "invalid_price",
        [
            "0",
            "-25.00",
            "nan",
            "inf"
        ]
    )
def test_extract_price_nonpositive_or_nonfinite(invalid_price):
    data = {
        "Global Quote": {
            "05. price": invalid_price
        }
    }

    with pytest.raises(ValueError, match="Price must be a positive finite number"):
        extract_price(data)

def test_get_current_prices_valid():
    fake_response = Mock()

    fake_response.json.return_value = {
            "Global Quote": {
                "05. price": "185.50"
            }
        }

    with patch("market_data.requests.get") as mock_get:
        mock_get.return_value = fake_response

        prices, errors = get_current_prices(["AAPL"])

    assert prices == {"AAPL": 185.50}
    assert errors == {}

def test_get_current_prices_invalid():
    fake_response = Mock()

    fake_response.json.return_value = {
            "Global Quote": {}
        }

    with patch("market_data.requests.get") as mock_get:
        mock_get.return_value = fake_response

        prices, errors = get_current_prices(["AAPL"])

    assert prices == {}
    assert errors == {"AAPL": "Price is missing"}

def test_get_current_prices_http_error():
    fake_response = Mock()

    fake_response.raise_for_status.side_effect = (requests.exceptions.HTTPError("500 Server Error"))

    with patch("market_data.requests.get") as mock_get:
        mock_get.return_value = fake_response

        prices, errors = get_current_prices(["AAPL"])

    assert prices == {}
    assert errors == {"AAPL": "500 Server Error"}

def test_get_current_prices_multiple_symbols():
    response_aapl = Mock()
    response_aapl.json.return_value = {
        "Global Quote": {"05. price": "185.50"}
    }

    response_nvda = Mock()
    response_nvda.json.return_value = {
        "Global Quote": {"05. price": "140.25"}
    }

    with patch("market_data.requests.get") as mock_get, \
        patch("market_data.time.sleep") as mock_sleep:
        mock_get.side_effect = [
            response_aapl,
            requests.exceptions.HTTPError("500 Server Error"),
            response_nvda
        ]

        prices, errors = get_current_prices(["AAPL", "MSFT", "NVDA"])

    assert prices == {"AAPL": 185.50, "NVDA": 140.25}
    assert errors == {"MSFT": "500 Server Error"}
    assert mock_sleep.call_count == 2

def test_get_current_prices_api_note():
    fake_response = Mock()
    
    fake_response.json.return_value = {"Note": "API call frequency limit reached"}

    with patch("market_data.requests.get") as mock_get:
        mock_get.return_value = fake_response

        prices, errors = get_current_prices(["AAPL"])

    assert prices == {}
    assert errors == {"AAPL": "API call frequency limit reached"}

def test_get_current_prices_rate_limit_stops_requests():
    response_aapl = Mock()
    response_aapl.json.return_value = {
        "Global Quote": {"05. price": "185.50"}
    }

    response_limit = Mock()
    response_limit.json.return_value = {
        "Note": "API call frequency limit reached"
    }

    with patch("market_data.requests.get") as mock_get, \
        patch("market_data.time.sleep") as mock_sleep:
        mock_get.side_effect = [
            response_aapl,
            response_limit
        ]

        prices, errors = get_current_prices(["AAPL", "MSFT", "NVDA"])

    assert prices == {"AAPL": 185.50}
    assert errors == {"MSFT": "API call frequency limit reached"}
    assert mock_get.call_count == 2
    mock_sleep.assert_called_once_with(1.2)

def test_build_live_portfolio_report(tmp_path):
    csv_content = (
        "symbol,shares_quantity,purchase_price\n"
        "AAPL,5,180\n"
        "MSFT,3,400\n"
    ) 

    csv_file = tmp_path / "holdings.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    with patch("portfolio.get_current_prices") as mock_prices:
        mock_prices.return_value = (
            {"AAPL": 150.0, "MSFT": 380.0},
            {}
        )
        report = build_live_portfolio_report(csv_file)

    assert len(report["holdings"]) == 2
    assert report["holdings"][0]["investment_cost"] == 900.0
    assert report["holdings"][0]["current_value"] == 750.0
    assert report["totals"]["total_gain_loss"] == -210.0
    mock_prices.assert_called_once_with(["AAPL", "MSFT"])

def test_build_live_portfolio_report_missing_prices(tmp_path):
    csv_content = (
        "symbol,shares_quantity,purchase_price\n"
        "AAPL,5,180\n"
        "MSFT,3,400\n"
    ) 

    csv_file = tmp_path / "holdings.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    with patch("portfolio.get_current_prices") as mock_prices:
        mock_prices.return_value = (
            {"AAPL": 150.0},
            {"MSFT": "API request failed"}
        )
        with pytest.raises(ValueError, match="API request failed"):
            build_live_portfolio_report(csv_file)

def test_build_live_portfolio_report_no_valid_holdings(tmp_path):
    csv_file = tmp_path / "holdings.csv"
    csv_file.write_text(
        "symbol,shares_quantity,purchase_price\nAAPL,,100",
        encoding="utf-8"
    )

    with patch("portfolio.get_current_prices") as mock_prices:
        with pytest.raises(ValueError, match="No data available"):
            build_live_portfolio_report(csv_file)

    mock_prices.assert_not_called()

def test_get_current_prices_information():
    fake_response = Mock()
    
    fake_response.json.return_value = {"Information": "API daily limit reached"}

    with patch("market_data.requests.get") as mock_get:
        mock_get.return_value = fake_response

        prices, errors = get_current_prices(["AAPL", "MSFT"])

    assert prices == {}
    assert errors == {"AAPL": "API daily limit reached"}
    mock_get.assert_called_once()
