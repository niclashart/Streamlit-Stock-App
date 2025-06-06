import streamlit as st
from datetime import datetime

from src.models.order import OrderModel
from src.services.stock_service import StockService, ChatbotService

def chatbot_view(username):
    """Chat bot view for stock assistant"""
    st.title("🤖 Stock Assistant")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "assistant", "content": "Hallo! Ich bin dein Stock Assistant. Wie kann ich dir heute helfen?"}
        ]
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
    # Get user input
    user_input = st.chat_input("Stelle eine Frage zu Aktien...")
    
    # Handle user input
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
            
        # Check if user is asking about a specific ticker
        words = user_input.upper().split()
        potential_tickers = [word for word in words if word.isalpha() and len(word) <= 5 and word not in ["WIE", "WAS", "WANN", "WARUM", "WESHALB", "WO", "WER", "WIESO", "IST", "SIND", "DER", "DIE", "DAS"]]
        
        ticker = None
        if potential_tickers:
            # Try to validate the first potential ticker
            try:
                price = StockService.get_current_price(potential_tickers[0])
                if price is not None:
                    ticker = potential_tickers[0]
            except:
                pass
                
        # Generate response
        with st.chat_message("assistant"):
            response = ChatbotService.generate_response(user_input, ticker)
            st.write(response)
            
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

def trading_view(username):
    """Automated trading view"""
    st.subheader("💹 Automatisierter Handel")
    
    # Initialize orders_checked
    if "orders_checked" not in st.session_state:
        st.session_state["orders_checked"] = datetime.now().timestamp() - 130  # Check soon
    
    # Check for orders that need to be executed (every 2 minutes)
    current_time = datetime.now().timestamp()
    if current_time - st.session_state["orders_checked"] > 120:
        executed_orders = check_orders()
        if executed_orders:
            for order in executed_orders:
                st.success(f"Order ausgeführt: {order['ticker']} - {order['order_type']} bei ${order['price']}")
        st.session_state["orders_checked"] = current_time
    
    # Create order form
    with st.form("order_form"):
        st.subheader("🛒 Neue Order erstellen")
        
        col1, col2 = st.columns(2)
        ticker = col1.text_input("Ticker", max_chars=10).upper()
        order_type = col2.selectbox("Order-Typ", ["buy", "sell"])
        
        col3, col4 = st.columns(2)
        price = col3.number_input("Zielpreis ($)", min_value=0.01, step=0.01)
        quantity = col4.number_input("Anzahl", min_value=0.01, step=0.01)
        
        if st.form_submit_button("Order erstellen"):
            if ticker and price > 0 and quantity > 0:
                if OrderModel.add(username, ticker, order_type, price, quantity):
                    st.success(f"Order für {ticker} erstellt!")
                else:
                    st.error("Fehler beim Erstellen der Order.")
            else:
                st.error("Bitte fülle alle Felder aus.")
    
    # Show pending orders
    st.subheader("⏳ Ausstehende Orders")
    orders = OrderModel.load(username)
    
    if orders.empty or "pending" not in orders["status"].values:
        st.info("Du hast keine ausstehenden Orders.")
    else:
        pending = orders[orders["status"] == "pending"].reset_index(drop=True)
        for i, row in pending.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
            col1.write(row["ticker"])
            col2.write(row["order_type"])
            col3.write(f"${row['price']:.2f}")
            col4.write(f"{row['quantity']}")
            
            if col5.button("Abbrechen", key=f"cancel_{i}"):
                if OrderModel.cancel(username, i):
                    st.success(f"Order für {row['ticker']} abgebrochen!")
                    st.rerun()
                else:
                    st.error("Fehler beim Abbrechen der Order.")

def check_orders():
    """Check all pending orders and execute them if target price is reached"""
    orders = OrderModel.load()
    if orders.empty or "pending" not in orders["status"].values:
        return []
    
    executed_orders = []
    
    for idx, order in orders[orders["status"] == "pending"].iterrows():
        ticker = order["ticker"]
        try:
            current_price = StockService.get_current_price(ticker)
            
            if current_price is None:
                continue
                
            if (order["order_type"] == "buy" and current_price <= order["price"]) or \
               (order["order_type"] == "sell" and current_price >= order["price"]):
                # Order conditions met
                executed_orders.append({
                    "ticker": ticker,
                    "order_type": order["order_type"],
                    "price": current_price
                })
                
                # Update order status
                order_id = order.name  # Get row index
                OrderModel.update_status(order_id, "executed")
                
        except Exception as e:
            print(f"Error checking order for {ticker}: {e}")
    
    return executed_orders

def buybot_view(username):
    """Buy Bot main view combining chatbot and trading"""
    tab1, tab2 = st.tabs(["💬 Stock Chatbot", "📊 Automated Trading"])
    
    with tab1:
        chatbot_view(username)
        
    with tab2:
        trading_view(username)
