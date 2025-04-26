# Stock Portfolio Assistant

## Overview
This application is a comprehensive stock portfolio management system built with Streamlit. It offers a user-friendly interface for tracking investments, analyzing stock performance, setting up automated buy/sell orders, and getting AI-powered stock insights through a conversational chatbot.

## Key Features

### User Authentication
- Secure login and registration system
- Password recovery functionality
- MD5 password hashing for security

### Portfolio Management
- Add, view, and track stock positions
- Record purchase prices, dates, and quantities
- Automatically update portfolio values based on current market prices

### Portfolio Analysis
- Visual performance tracking with interactive charts
- Comparison against major benchmarks (S&P 500, Nasdaq, MSCI World)
- Dividend tracking and analysis
- Portfolio rebalancing recommendations
- Detailed metrics including total value, performance, and gains/losses

### Stock Analysis
- Individual stock analysis with key metrics
- Price history visualization
- Fundamental data (market cap, P/E ratio, dividends)

### Automated Trading System
- Set up buy and sell orders at target prices
- Automatic order execution when price conditions are met
- Order history tracking
- Cancel pending orders as needed

### AI Stock Assistant
- Conversational AI chatbot for stock information and advice
- Powered by DeepSeek's API
- Stock ticker detection in natural language
- Comprehensive stock information retrieval
- Context-aware responses that maintain conversation history
- Fallback functionality when API is unavailable

## Installation

1. Clone this repository:
```bash
git clone https://github.com/niclashart/Streamlit-Stock-App
cd stock-portfolio-assistant
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your DeepSeek API key:
```
DEEPSEEK_API_KEY=your_api_key_here
```

4. Run the application:
```bash
streamlit run app.py
```

## Dependencies

- Python 3.8+
- Streamlit
- Pandas
- yfinance
- Plotly
- Requests
- Python-dotenv

## Data Structure
- `users.csv` - Stores username and hashed passwords
- `orders.csv` - Tracks all buy/sell orders and their statuses
- `portfolio_{username}.csv` - Individual portfolio data for each user

## Usage

### First-time Use
1. Register for a new account
2. Add stocks to your portfolio with purchase information
3. Explore portfolio analytics and set up automated orders

### Portfolio Management
- Track your investments across multiple stocks
- Monitor performance against market benchmarks
- Analyze dividend income

### Automated Trading
- Set a buy order for AAPL at $170 to automatically purchase when the price drops
- Create a sell order for TSLA at $250 to lock in profits when the target is reached

### AI Assistant
- "Tell me about NVDA stock"
- "What are the dividend prospects for MSFT?"
- "How has AAPL performed compared to the market?"
- "What's the P/E ratio of AMZN?"

## Configuration

The application uses environment variables to configure the API key. Create a `.env` file in the project root with the following content:
```
DEEPSEEK_API_KEY=your_api_key_here
```

## Security Note

This application uses MD5 for password hashing, which is not recommended for production use. For a production environment, consider using a more secure hashing algorithm like bcrypt or Argon2.

## License

MIT License

## Acknowledgments

- Data provided by Yahoo Finance API
- AI capabilities powered by DeepSeek
- Built with Streamlit