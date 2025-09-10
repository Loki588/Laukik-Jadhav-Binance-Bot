import os
import logging
import json
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

class AdvancedBot:
    def __init__(self):
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.secret_key = os.getenv('BINANCE_SECRET_KEY')
        self.testnet = True
        
        # Initialize Binance client with error handling
        try:
            self.client = Client(
                self.api_key, 
                self.secret_key, 
                testnet=self.testnet,
                tld='com'
            )
            self.client.ping()  # Test connection
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Binance: {e}")
        
        # Setup comprehensive logging
        self.setup_logging()
        self.logger.info("Bot initialized successfully")
        
        # Initialize order tracking
        self.active_orders = {}
        
    def setup_logging(self):
        """Setup comprehensive logging system"""
        log_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler('bot.log')
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        console_handler.setLevel(logging.INFO)
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def validate_symbol(self, symbol):
        """Enhanced symbol validation"""
        try:
            exchange_info = self.client.futures_exchange_info()
            active_symbols = [
                s['symbol'] for s in exchange_info['symbols'] 
                if s['status'] == 'TRADING'
            ]
            is_valid = symbol.upper() in active_symbols
            self.logger.info(f"Symbol validation: {symbol} -> {'Valid' if is_valid else 'Invalid'}")
            return is_valid
        except Exception as e:
            self.logger.error(f"Error validating symbol {symbol}: {e}")
            return False
            
    def validate_quantity(self, symbol, quantity):
        """Validate quantity against symbol filters"""
        try:
            exchange_info = self.client.futures_exchange_info()
            symbol_info = next(
                s for s in exchange_info['symbols'] 
                if s['symbol'] == symbol.upper()
            )
            
            # Check LOT_SIZE filter
            lot_size = next(
                f for f in symbol_info['filters'] 
                if f['filterType'] == 'LOT_SIZE'
            )
            
            min_qty = float(lot_size['minQty'])
            max_qty = float(lot_size['maxQty'])
            step_size = float(lot_size['stepSize'])
            
            qty = float(quantity)
            
            if qty < min_qty or qty > max_qty:
                raise ValueError(f"Quantity {qty} outside allowed range [{min_qty}, {max_qty}]")
                
            # Check step size compliance
            if (qty - min_qty) % step_size != 0:
                raise ValueError(f"Quantity {qty} doesn't comply with step size {step_size}")
                
            self.logger.info(f"Quantity validation passed: {quantity}")
            return True
            
        except Exception as e:
            self.logger.error(f"Quantity validation failed: {e}")
            raise ValueError(f"Invalid quantity: {e}")
            
    def get_current_price(self, symbol):
        """Get current market price"""
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol.upper())
            price = float(ticker['price'])
            self.logger.info(f"Current price for {symbol}: {price}")
            return price
        except Exception as e:
            self.logger.error(f"Error getting price for {symbol}: {e}")
            return None
            
    def get_account_info(self):
        """Get detailed account information"""
        try:
            account = self.client.futures_account()
            balance = float(account['totalWalletBalance'])
            self.logger.info(f"Account balance: {balance} USDT")
            return account
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return None
            
    def log_order_result(self, order_type, order_result):
        """Standardized order logging"""
        if order_result:
            self.logger.info(f"{order_type} order executed successfully: {json.dumps(order_result, indent=2)}")
            # Track order
            self.active_orders[order_result['orderId']] = {
                'type': order_type,
                'timestamp': datetime.now().isoformat(),
                'details': order_result
            }
        else:
            self.logger.error(f"{order_type} order failed")
