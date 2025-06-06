# Stock Portfolio Assistant

## Overview
This application is a comprehensive stock portfolio management system with a modular architecture. It consists of a frontend built with Streamlit and a backend API built with FastAPI. The application offers a user-friendly interface for tracking investments, analyzing stock performance, setting up automated buy/sell orders, and getting AI-powered stock insights through a conversational chatbot.

## Key Features

### User Authentication
- Secure login and registration system with JWT authentication
- Password recovery functionality
- Bcrypt password hashing for enhanced security

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

## Architecture

This project uses a modern, modular architecture:

- **Frontend**: Streamlit for an interactive user interface
- **Backend**: FastAPI for a fast, asynchronous API with layered architecture:
  - API Layer: Routes and endpoints
  - Service Layer: Business logic
  - Repository Layer: Data access
  - Model Layer: Database schema
- **Database**: PostgreSQL for persistent data storage with Alembic migrations
- **Deployment**: Docker and Docker Compose for containerized deployment

For detailed information on the architecture, see [architecture.md](architecture.md).

## Installation

### Using Docker (recommended)

1. Clone this repository:
```bash
git clone https://github.com/niclashart/Streamlit-Stock-App
cd Streamlit-Stock-App
```

2. Create a `.env` file in the project root with your configuration:
```
DEEPSEEK_API_KEY=your_api_key_here
JWT_SECRET_KEY=your_jwt_secret_here
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=stockapp
DB_HOST=postgres
```

3. Start the application with Docker Compose:
```bash
docker-compose up -d
```

4. Access the application:
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000/api/v1/docs

### Without Docker (Development)

1. Clone this repository:
```bash
git clone https://github.com/niclashart/Streamlit-Stock-App
cd Streamlit-Stock-App
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with configuration:
```
DEEPSEEK_API_KEY=your_api_key_here
JWT_SECRET_KEY=your_jwt_secret_here
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=stockapp
DB_HOST=localhost
```

4. Set up PostgreSQL database

5. Run the backend:
```bash
cd backend
uvicorn main:app --reload
```

6. Run the frontend:
```bash
cd frontend
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
### Database Tables
- `users` - Stores user information and authentication data
- `positions` - Portfolio positions for each user
- `orders` - Trading orders with status tracking

### Legacy CSV Files (for reference only)
- `users.csv` - Stores username and hashed passwords
- `orders.csv` - Tracks all buy/sell orders and their statuses
- `portfolio_{username}.csv` - Individual portfolio data for each user

## Usage

### First-time Use
1. Register for a new account
2. Add stocks to your portfolio with purchase information
3. Explore portfolio analytics and set up automated orders

### Running Database Migrations
To initialize or update the database schema:
```bash
cd backend
alembic upgrade head
```

To create a new migration after changing models:
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

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

## Running Tests

To run automated tests:

```bash
cd Streamlit-Stock-App
pytest
```

## API Documentation

When the application is running, API documentation is available at:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## License

MIT License

## Acknowledgments

- Data provided by Yahoo Finance API
- AI capabilities powered by DeepSeek
- Built with Streamlit