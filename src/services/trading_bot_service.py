"""
Trading bot service module for checking and executing orders
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import threading
from datetime import datetime
from typing import List, Dict, Any
from src.models.order import OrderService, Order
from src.models.portfolio import PortfolioService
from src.services.stock_service import StockService
from src.database.storage_factory import StorageFactory

class TradingBotService:
    """Service to check and execute orders based on current market conditions"""
    
    def __init__(self, check_interval: int = 60):
        """Initialize the trading bot service
        
        Args:
            check_interval: Seconds between checks for pending orders
        """
        self.check_interval = check_interval
        self.order_service = OrderService()
        self.running = False
        self.thread = None
        self._last_check_time = None
        self._executed_orders = []
        
    def start(self):
        """Start the trading bot in a separate thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_bot)
            self.thread.daemon = True  # Thread will die when main program exits
            self.thread.start()
            
    def stop(self):
        """Stop the trading bot"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)  # Wait for thread to finish
            
    def get_last_check_time(self) -> datetime:
        """Get the last time orders were checked"""
        return self._last_check_time or datetime.now()
        
    def get_executed_orders(self) -> List[Dict[str, Any]]:
        """Get recently executed orders and clear the list"""
        executed = self._executed_orders.copy()
        self._executed_orders = []
        return executed
        
    def _run_bot(self):
        """Main loop for checking and executing orders"""
        while self.running:
            try:
                self._check_pending_orders()
                self._last_check_time = datetime.now()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"Error in trading bot: {e}")
                time.sleep(self.check_interval)  # Sleep even on error
                
    def _check_pending_orders(self):
        """Check pending orders and execute if conditions are met"""
        pending_orders = self.order_service.get_pending_orders()
        
        print(f"[Trading Bot] Checking {len(pending_orders)} pending orders...")
        
        for order in pending_orders:
            ticker = order.ticker
            try:
                # Get current price
                current_price = StockService.get_current_price(ticker)
                
                if current_price is None:
                    print(f"[Trading Bot] Could not get current price for {ticker}, skipping")
                    continue
                
                print(f"[Trading Bot] Order: {order.order_type} {ticker} @ ${order.price}, Current price: ${current_price}")
                    
                # Check if order should be executed
                execute = False
                if order.order_type == "buy" and current_price <= order.price:
                    execute = True
                    print(f"[Trading Bot] BUY condition met: {current_price} <= {order.price}")
                elif order.order_type == "sell" and current_price >= order.price:
                    execute = True
                    print(f"[Trading Bot] SELL condition met: {current_price} >= {order.price}")
                else:
                    print(f"[Trading Bot] Price conditions not met, keeping order as pending")
                    
                if execute:
                    # Execute the order
                    print(f"[Trading Bot] Executing order...")
                    self.order_service.execute_order(order, current_price)
                    
                    # Record executed order
                    self._executed_orders.append({
                        "username": order.username,
                        "ticker": ticker,
                        "type": order.order_type,
                        "price": current_price,
                        "quantity": order.quantity
                    })
                    
                    print(f"[Trading Bot] Successfully executed {order.order_type} order for {ticker} at ${current_price}")
            except Exception as e:
                print(f"[Trading Bot] Error processing order for {ticker}: {e}")
                
# Singleton instance of the trading bot - check every 30 seconds for demo purposes
# In production, this should be longer like 5-15 minutes
trading_bot = TradingBotService(check_interval=30)
