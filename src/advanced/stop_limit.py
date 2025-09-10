#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from datetime import datetime
from bot_base import AdvancedBot

class StopLimitBot(AdvancedBot):
    def place_stop_limit_order(self, symbol, side, quantity, stop_price, limit_price, 
                              reduce_only=False):
        """Advanced stop-limit order implementation"""
        try:
            # Enhanced validation
            if not self.validate_symbol(symbol):
                raise ValueError(f"Invalid symbol: {symbol}")
                
            if side.upper() not in ['BUY', 'SELL']:
                raise ValueError(f"Invalid side: {side}")
                
            self.validate_quantity(symbol, quantity)
            
            if float(stop_price) <= 0 or float(limit_price) <= 0:
                raise ValueError("Stop price and limit price must be positive")
            
            # Get current price for validation
            current_price = self.get_current_price(symbol)
            
            # Logical validation for stop-limit orders
            if side.upper() == 'BUY':
                # Buy stop: stop price should be above current price
                if float(stop_price) <= current_price:
                    print(f"⚠️  WARNING: Buy stop price ({stop_price}) should be above current price ({current_price})")
            else:
                # Sell stop: stop price should be below current price
                if float(stop_price) >= current_price:
                    print(f"⚠️  WARNING: Sell stop price ({stop_price}) should be below current price ({current_price})")
            
            # Place stop-limit order
            self.logger.info(f"Placing stop-limit order: {side} {quantity} {symbol} "
                           f"stop@{stop_price} limit@{limit_price}")
            
            order_params = {
                'symbol': symbol.upper(),
                'side': side.upper(),
                'type': 'STOP',
                'quantity': str(quantity),
                'price': str(limit_price),
                'stopPrice': str(stop_price),
                'timeInForce': 'GTC'
            }
            
            if reduce_only:
                order_params['reduceOnly'] = 'true'
            
            order = self.client.futures_create_order(**order_params)
            
            self.log_order_result("STOP_LIMIT", order)
            
            # Enhanced output
            print(f"\n✅ STOP-LIMIT ORDER PLACED")
            print(f"{'='*50}")
            print(f"Symbol:           {order['symbol']}")
            print(f"Side:             {order['side']}")
            print(f"Quantity:         {order['origQty']}")
            print(f"Stop Price:       {stop_price} USDT")
            print(f"Limit Price:      {limit_price} USDT")
            print(f"Current Price:    {current_price} USDT")
            print(f"Order ID:         {order['orderId']}")
            print(f"Status:           {order['status']}")
            print(f"Reduce Only:      {reduce_only}")
            print(f"Timestamp:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*50}")
            print(f"💡 This order will trigger when price reaches {stop_price}")
            print(f"   Then it will place a limit order at {limit_price}\n")
            
            return order
            
        except Exception as e:
            self.logger.error(f"Stop-limit order failed: {e}")
            print(f"\n❌ STOP-LIMIT ORDER FAILED")
            print(f"Error: {str(e)}\n")
            return None

def main():
    parser = argparse.ArgumentParser(
        description='Place stop-limit order on Binance Futures Testnet',
        epilog='Example: python stop_limit.py BTCUSDT SELL 0.001 35000 34000'
    )
    parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('side', help='Order side (BUY/SELL)')
    parser.add_argument('quantity', type=float, help='Order quantity')
    parser.add_argument('stop_price', type=float, help='Stop trigger price')
    parser.add_argument('limit_price', type=float, help='Limit execution price')
    parser.add_argument('--reduce-only', action='store_true', 
                        help='Reduce only (close position only)')
    
    args = parser.parse_args()
    
    try:
        bot = StopLimitBot()
        order = bot.place_stop_limit_order(
            args.symbol, args.side, args.quantity, 
            args.stop_price, args.limit_price, args.reduce_only
        )
        if order:
            print("success")
        else:
            print("❌ Stop-limit order was not placed.")
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
