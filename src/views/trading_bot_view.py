"""
Trading bot view for AI stock assistant and automated order management
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from datetime import datetime
from models.order import OrderService, Order
from services.chatbot_service import ChatbotService
from services.stock_service import StockService

def check_pending_orders() -> list:
    """Check pending orders and execute them if price conditions are met"""
    order_service = OrderService()
    pending_orders = order_service.get_pending_orders()
    executed_orders = []
    
    for order in pending_orders:
        ticker = order.ticker
        try:
            # Get current price
            current_price = StockService.get_current_price(ticker)
            
            if current_price is None:
                continue
                
            # Check if order should be executed
            execute = False
            if order.order_type == "buy" and current_price <= order.price:
                execute = True
            elif order.order_type == "sell" and current_price >= order.price:
                execute = True
                
            if execute:
                # Execute the order
                order_service.execute_order(order, current_price)
                executed_orders.append({
                    "username": order.username,
                    "ticker": ticker,
                    "type": order.order_type,
                    "price": current_price,
                    "quantity": order.quantity
                })
        except Exception as e:
            print(f"Error processing order for {ticker}: {e}")
    
    return executed_orders

def show_trading_bot_view() -> None:
    """Display the trading bot view with chatbot and order management"""
    st.title("🤖 Stock Assistant")
    
    # Initialize session state variables for chat history
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    
    if "orders_checked" not in st.session_state:
        st.session_state["orders_checked"] = datetime.now().timestamp() - 120  # Check immediately first time
    
    # Check for orders that need to be executed (every 2 minutes)
    current_time = datetime.now().timestamp()
    if current_time - st.session_state["orders_checked"] > 120:
        with st.spinner("Checking pending orders..."):
            executed_orders = check_pending_orders()
            if executed_orders:
                st.success(f"🎉 {len(executed_orders)} order(s) were executed!")
                for order in executed_orders:
                    if order["username"] == st.session_state["username"]:
                        st.info(f"Your {order['type']} order for {order['quantity']} shares of {order['ticker']} was executed at ${order['price']:.2f}!")
        st.session_state["orders_checked"] = current_time
    
    # Create tabs for chatbot and order management
    tab1, tab2 = st.tabs(["💬 Stock Chatbot", "📊 Automated Trading"])
    
    # Tab 1: Stock Info Chatbot
    with tab1:
        st.subheader("💬 Ask about stocks")
        
        # Initialize chatbot service
        chatbot_service = ChatbotService()
        
        # Display API key status
        if chatbot_service.api_key:
            st.success("DeepSeek API key is configured ✅")
        else:
            st.warning("DeepSeek API key not found. Please add it to your .env file to enable advanced features.")
            st.info("Set DEEPSEEK_API_KEY=your_api_key in a .env file in the app directory.")
        
        # Display past messages
        for message in st.session_state["messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Input for new messages
        if prompt := st.chat_input("Ask about a stock or market trend..."):
            # Add user message to chat history
            st.session_state["messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Extract ticker if present
            ticker_match = chatbot_service.extract_ticker(prompt)
            
            # Generate assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = chatbot_service.generate_response(
                        prompt, 
                        ticker_match, 
                        [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state["messages"][-10:]]
                    )
                    st.markdown(response)
            
            # Add assistant response to chat history
            st.session_state["messages"].append({"role": "assistant", "content": response})

    # Tab 2: Automated Trading
    with tab2:
        st.subheader("📊 Set Automated Buy/Sell Orders")
        
        # Initialize order service
        order_service = OrderService()
        
        # Get user's portfolio tickers and shares
        from src.models.portfolio import PortfolioService
        portfolio_service = PortfolioService(st.session_state["username"])
        portfolio = portfolio_service.load_portfolio()
        
        total_holdings = {}
        for position in portfolio.positions:
            total_holdings[position.ticker] = position.shares
        
        if total_holdings:
            # Display current holdings
            st.info("Your current holdings:")
            holdings_text = ", ".join(f"{ticker}: {shares} shares" for ticker, shares in total_holdings.items())
            st.text(holdings_text)
        
        # Form to create new automated orders
        with st.form("order_form"):
            st.subheader("Create New Order")
            
            col1, col2 = st.columns(2)
            with col1:
                ticker = st.text_input("Ticker Symbol (e.g., AAPL)").upper()
                order_type = st.selectbox("Order Type", ["buy", "sell"])
            
            with col2:
                if ticker:
                    try:
                        current_price = StockService.get_current_price(ticker)
                        if current_price:
                            st.metric("Current Price", f"${current_price:.2f}")
                            
                            # Set default price based on order type
                            default_price = current_price * 0.95 if order_type == "buy" else current_price * 1.05
                            price = st.number_input("Target Price ($)", 
                                                min_value=0.01, 
                                                value=float(f"{default_price:.2f}"),
                                                help="Order will execute when price reaches this level")
                        else:
                            price = st.number_input("Target Price ($)", min_value=0.01, value=1.00)
                    except:
                        st.warning("Could not fetch current price. Enter target price manually.")
                        price = st.number_input("Target Price ($)", min_value=0.01, value=1.00)
                else:
                    price = st.number_input("Target Price ($)", min_value=0.01, value=1.00)
                
                quantity = st.number_input("Quantity", min_value=0.01, value=1.0)
            
            submitted = st.form_submit_button("Create Order")
            
            if submitted:
                if ticker and price > 0 and quantity > 0:
                    if order_type == "sell":
                        # Check if user has enough shares to sell
                        if ticker in total_holdings and total_holdings[ticker] >= quantity:
                            order = Order(
                                username=st.session_state["username"],
                                ticker=ticker,
                                order_type=order_type,
                                price=price,
                                quantity=quantity
                            )
                            order_service.create_order(order)
                            st.success(f"Order created! Will {order_type} {quantity} shares of {ticker} when price reaches ${price:.2f}")
                        else:
                            st.error(f"Not enough shares of {ticker} in your portfolio for this sell order.")
                    else:
                        order = Order(
                            username=st.session_state["username"],
                            ticker=ticker,
                            order_type=order_type,
                            price=price,
                            quantity=quantity
                        )
                        order_service.create_order(order)
                        st.success(f"Order created! Will {order_type} {quantity} shares of {ticker} when price reaches ${price:.2f}")
                else:
                    st.error("Please enter a valid ticker, price, and quantity.")
        
        # Display pending orders
        st.subheader("Your Pending Orders")
        user_orders = order_service.get_orders(st.session_state["username"])
        pending_orders = [o for o in user_orders if o.status == "pending"]
        
        if pending_orders:
            # Add a cancel button to each order
            for i, order in enumerate(pending_orders):
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                col1.write(f"{order.ticker}")
                col2.write(f"{order.order_type.capitalize()}")
                col3.write(f"${order.price:.2f} × {order.quantity}")
                if col4.button(f"Cancel", key=f"cancel_{i}"):
                    if order_service.cancel_order(st.session_state["username"], i):
                        st.success(f"Order for {order.ticker} cancelled")
                        st.rerun()
        else:
            st.info("You have no pending orders.")
            
        # Display order history (executed and cancelled)
        history_orders = [o for o in user_orders if o.status in ["executed", "cancelled"]]
        if history_orders:
            st.subheader("Order History")
            for order in history_orders:
                status_color = "green" if order.status == "executed" else "gray"
                st.write(f"{order.ticker} - {order.order_type.capitalize()} {order.quantity} shares at ${order.price:.2f} - "
                         f"<span style='color:{status_color}'>{order.status.upper()}</span> on {order.created_at}", unsafe_allow_html=True)
