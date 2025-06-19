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



## Installation & Start with Docker

1. Clone the repository and switch to the project directory:
   ```bash
   git clone https://github.com/niclashart/Streamlit-Stock-App.git
   cd Streamlit-Stock-App
   ```

2. Create a `.env` file in the project root with your DeepSeek API key:
   ```
   DEEPSEEK_API_KEY=your_api_key_here
   ```

3. Build and start all services with Docker Compose:
   ```bash
   docker-compose up -d --build
   ```

4. The application will then be available at:  
   [http://localhost:8501](http://localhost:8501)  
   (or at the IP/domain of your server)


**Note:**  
For updates, simply update the code (`git pull`), then run `docker-compose up -d --build` again.

---

## Demo Deployment

For demonstration purposes, the application is deployed on a cloud server at Hetzner. The workflow for loading and starting the application was performed there. You can access the running demo instance at:

[http://188.245.96.62:8501/](http://188.245.96.62:8501/)



## Architecture

The application consists of three services (microservices architecture):

- **Frontend:** Streamlit app (user interface)
- **DeepSeek Service:** Flask API for AI chatbot functionality
- **Stock Service:** Flask API for stock and dividend data

The services communicate via HTTP APIs and are orchestrated together using Docker Compose.

## Data Storage

- The application now uses a SQLite database (`stock_app.db`) for users, portfolios, and orders.



## Usage

### Start with Docker

1. Make sure Docker and Docker Compose are installed.
2. Create the `.env` file with your DeepSeek API key.
3. Start the application with:
   ```bash
   docker-compose up -d --build
   ```
4. Open the app in your browser: [http://localhost:8501](http://localhost:8501)

### Update to a new version

1. Pull the latest changes:
   ```bash
   git pull
   ```
2. Restart the containers:
   ```bash
   docker-compose up -d --build
   ```




## Configuration

The application uses environment variables to configure the API key. Create a `.env` file in the project root with the following content:
```
DEEPSEEK_API_KEY=your_api_key_here
```


## Nice to Know

- Under **Overview**, you get a summary of your executed and pending orders. Orders can be created either via **Portfolio Management** or under **Buy Bot > Automated Trading**.
- In **Buy Bot > Stock Chatbot**, you can ask for information or analyses about various stocks using natural language.
- Under **Single Analysis**, you can view a detailed overview of a stock selected in the **Overview** section.


## Security Note

This application uses MD5 for password hashing, which is not recommended for production use. For a production environment, consider using a more secure hashing algorithm like bcrypt or Argon2.

## License

MIT License

## Acknowledgments

- Data provided by Yahoo Finance API
- AI capabilities powered by DeepSeek
- Built with Streamlit