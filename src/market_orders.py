#!/usr/bin/env python3
from datetime import datetime
import sys
import argparse
from bot_base import AdvancedBot

class MarketOrderBot(AdvancedBot):
    def place_market_order(self, symbol, side, quantity):
        """Enhanced market order with comprehensive validation"""
        try:
            # Input validation
            if not self.validate_symbol(symbol):
                raise ValueError(f"Invalid symbol: {symbol}")
                
            if side.upper() not in ['BUY', 'SELL']:
                raise ValueError(f"Invalid side: {side}. Must be BUY or SELL")
                
            self.validate_quantity(symbol, quantity)
            
            # Get current price for logging
            current_price = self.get_current_price(symbol)
            
            # Place market order
            self.logger.info(f"Placing market order: {side} {quantity} {symbol} at market price ~{current_price}")
            
            order = self.client.futures_create_order(
                symbol=symbol.upper(),
                side=side.upper(),
                type='MARKET',
                quantity=str(quantity)
            )
            
            self.log_order_result("MARKET", order)
            
            # Enhanced output
            print(f"\n✅ MARKET ORDER EXECUTED")
            print(f"{'='*50}")
            print(f"Symbol:           {order['symbol']}")
            print(f"Side:             {order['side']}")
            print(f"Quantity:         {order['origQty']}")
            print(f"Status:           {order['status']}")
            print(f"Order ID:         {order['orderId']}")
            print(f"Executed Price:   ~{current_price} USDT")
            print(f"Timestamp:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*50}\n")
            
            return order
            
        except Exception as e:
            self.logger.error(f"Market order failed: {e}")
            print(f"\n❌ MARKET ORDER FAILED")
            print(f"Error: {str(e)}\n")
            return None
            
    def get_order_status(self, symbol, order_id):
        """Check order status"""
        try:
            order = self.client.futures_get_order(symbol=symbol, orderId=order_id)
            self.logger.info(f"Order status check: {order_id} -> {order['status']}")
            return order
        except Exception as e:
            self.logger.error(f"Error checking order status: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(
        description='Place market order on Binance Futures Testnet',
        epilog='Example: python market_orders.py BTCUSDT BUY 0.001'
    )
    parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('side', help='Order side (BUY/SELL)')
    parser.add_argument('quantity', type=float, help='Order quantity')
    parser.add_argument('--check-balance', action='store_true', help='Show account balance')
    
    args = parser.parse_args()
    
    try:
        bot = MarketOrderBot()
        
        if args.check_balance:
            account = bot.get_account_info()
            if account:
                print(f"Available Balance: {account['totalWalletBalance']} USDT")
        
        bot.place_market_order(args.symbol, args.side, args.quantity)
        
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
