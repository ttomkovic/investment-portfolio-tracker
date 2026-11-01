# Investment Portfolio Tracker

A Python command-line application that tracks a hypothetical investment portfolio, retrieves stock prices, and calculates investment performance.

This project was developed to practice Python programming, working with CSV files, integrating external APIs, error handling, and automated testing.

## Features

- Load portfolio holdings from a CSV file.
- Validate holdings and report invalid rows.
- Calculate investment cost, current value, gain/loss, and percentage returns.
- Retrieve stock prices using the Alpha Vantage API.
- Choose between manual demonstration prices and API-based prices.
- Handle missing prices, API errors, and rate-limit responses.
- Display a formatted portfolio report in the terminal.
- Run automated tests using pytest.

## Project Structure

```text
investment-portfolio-tracker/
├── data/
│   └── holdings.csv
├── tests/
│   └── test_portfolio.py
├── portfolio.py
├── market_data.py
├── README.md
├── .gitignore
└── .env
```

## Installation

Clone the repository and navigate to the project directory.

Create and activate a Python virtual environment.

Install the required packages:

```bash
python -m pip install requests python-dotenv pytest
```

## API Configuration

To use live stock prices, obtain an API key from [Alpha Vantage](https://www.alphavantage.co/).

Create a `.env` file in the project directory:

```env
ALPHA_VANTAGE_API_KEY=your_api_key_here
```

The `.env` file is excluded from version control to protect the API key.

## Usage

Prepare a CSV file at `data/holdings.csv` with the following columns:

```csv
symbol,shares_quantity,purchase_price
AAPL,5,180
MSFT,3,400
```

Run the application:

```bash
python portfolio.py
```

Select one of the available options:

```text
1. Manual prices (demo)
2. Live prices (Alpha Vantage)
```

The application displays individual holding performance, portfolio totals, and any CSV validation warnings.

## Testing

Run the automated test suite:

```bash
python -m pytest -q
```

The project currently includes 34 passing tests covering portfolio calculations, CSV validation, report generation, API responses, error handling, and live-price integration using mocks.

## Current Limitations

- The application uses hypothetical portfolio holdings.
- Live prices depend on Alpha Vantage API availability and rate limits.
- The application requires all stock prices to be available before generating a live report.
- Price timestamps and historical performance are not currently included.

## Future Improvements

- Support partial reports when some stock prices are unavailable.
- Include stock price timestamps.
- Add historical portfolio performance tracking.
- Improve CLI configuration and error reporting.