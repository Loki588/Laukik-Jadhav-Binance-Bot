#!/usr/bin/env python3
import sys
import argparse
from datetime import datetime
from bot_base import AdvancedBot

class LimitOrderBot(AdvancedBot):
    def place_limit_order(self, symbol, side, quantity, price, time_in_force='GTC'):
        """Enhanced limit order with price validation"""
        try:
            # Input validation
            if not self.validate_symbol(symbol):
                raise ValueError(f"Invalid symbol: {symbol}")
                
            if side.upper() not in ['BUY', 'SELL']:
                raise ValueError(f"Invalid side: {side}")
                
            self.validate_quantity(symbol, quantity)
            
            if float(price) <= 0:
                raise ValueError(f"Invalid price: {price}")
            
            # Get current market price for comparison
            current_price = self.get_current_price(symbol)
            price_diff = ((float(price) - current_price) / current_price) * 100
            
            # Warning for extreme prices
            if abs(price_diff) > 10:
                print(f"⚠️  WARNING: Your limit price is {price_diff:.2f}% from current market price")
                print(f"   Current: {current_price}, Your Price: {price}")
            
            # Place limit order
            self.logger.info(f"Placing limit order: {side} {quantity} {symbol} at {price}")
            
            order = self.client.futures_create_order(
                symbol=symbol.upper(),
                side=side.upper(),
                type='LIMIT',
                timeInForce=time_in_force,
                quantity=str(quantity),
                price=str(price)
            )
            
            self.log_order_result("LIMIT", order)
            
            # Enhanced output
            print(f"\n✅ LIMIT ORDER PLACED")
            print(f"{'='*50}")
            print(f"Symbol:           {order['symbol']}")
            print(f"Side:             {order['side']}")
            print(f"Quantity:         {order['origQty']}")
            print(f"Limit Price:      {order['price']} USDT")
            print(f"Current Price:    {current_price} USDT")
            print(f"Price Difference: {price_diff:+.2f}%")
            print(f"Status:           {order['status']}")
            print(f"Order ID:         {order['orderId']}")
            print(f"Time in Force:    {time_in_force}")
            print(f"Timestamp:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*50}\n")
            
            return order
            
        except Exception as e:
            self.logger.error(f"Limit order failed: {e}")
            print(f"\n❌ LIMIT ORDER FAILED")
            print(f"Error: {str(e)}\n")
            return None
            
    def cancel_order(self, symbol, order_id):
        """Cancel existing order"""
        try:
            result = self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
            self.logger.info(f"Order cancelled: {order_id}")
            print(f"✅ Order {order_id} cancelled successfully")
            return result
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            print(f"❌ Error cancelling order: {e}")
            return None
            
    def get_open_orders(self, symbol=None):
        """Get all open orders"""
        try:
            orders = self.client.futures_get_open_orders(symbol=symbol)
            self.logger.info(f"Retrieved {len(orders)} open orders")
            return orders
        except Exception as e:
            self.logger.error(f"Error getting open orders: {e}")
            return []

def main():
    parser = argparse.ArgumentParser(
        description='Place limit order on Binance Futures Testnet',
        epilog='Example: python limit_orders.py BTCUSDT BUY 0.001 30000'
    )
    parser.add_argument('symbol', nargs='?', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('side', nargs='?', help='Order side (BUY/SELL)')
    parser.add_argument('quantity', nargs='?', type=float, help='Order quantity')
    parser.add_argument('price', nargs='?', type=float, help='Limit price')
    parser.add_argument('--tif', default='GTC', choices=['GTC', 'IOC', 'FOK'], 
                        help='Time in force (default: GTC)')
    parser.add_argument('--show-open', action='store_true', help='Show open orders')

    args = parser.parse_args()

    try:
        bot = LimitOrderBot()

        if args.show_open:
            if not args.symbol:
                parser.error('symbol is required with --show-open')
            orders = bot.get_open_orders(args.symbol)
            if orders:
                print(f"\n📋 Open Orders for {args.symbol}:")
                for order in orders:
                    print(f"  ID: {order['orderId']}, Side: {order['side']}, "
                          f"Price: {order['price']}, Qty: {order['origQty']}")
            else:
                print(f"\n📋 No open orders for {args.symbol}")
            return

        # If not showing open orders, require all positional arguments
        missing = [
            name for name, value in zip(['side', 'quantity', 'price'], [args.side, args.quantity, args.price])
            if value is None
        ]
        if args.symbol is None or missing:
            parser.error(f"the following arguments are required: symbol, side, quantity, price")

        bot.place_limit_order(args.symbol, args.side, args.quantity, args.price, args.tif)

    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
