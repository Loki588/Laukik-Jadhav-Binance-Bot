#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import time
import threading
from datetime import datetime
from bot_base import AdvancedBot

class OCOBot(AdvancedBot):
    def __init__(self):
        super().__init__()
        self.oco_pairs = {}  # Track OCO order pairs
        
    def place_oco_order(self, symbol, quantity, take_profit_price, stop_loss_price, 
                       position_side='LONG'):
        """
        Place OCO order (Take Profit + Stop Loss)
        For futures, we simulate OCO with linked orders
        """
        try:
            # Validation
            if not self.validate_symbol(symbol):
                raise ValueError(f"Invalid symbol: {symbol}")
                
            self.validate_quantity(symbol, quantity)
            
            if float(take_profit_price) <= 0 or float(stop_loss_price) <= 0:
                raise ValueError("Take profit and stop loss prices must be positive")
            
            current_price = self.get_current_price(symbol)
            
            # Determine order sides based on position
            if position_side.upper() == 'LONG':
                tp_side = 'SELL'  # Take profit sells long position
                sl_side = 'SELL'  # Stop loss sells long position
                
                # Validation for long position
                if float(take_profit_price) <= current_price:
                    raise ValueError(f"Take profit ({take_profit_price}) should be above current price ({current_price}) for LONG position")
                if float(stop_loss_price) >= current_price:
                    raise ValueError(f"Stop loss ({stop_loss_price}) should be below current price ({current_price}) for LONG position")
            else:
                tp_side = 'BUY'   # Take profit buys back short position
                sl_side = 'BUY'   # Stop loss buys back short position
                
                # Validation for short position
                if float(take_profit_price) >= current_price:
                    raise ValueError(f"Take profit ({take_profit_price}) should be below current price ({current_price}) for SHORT position")
                if float(stop_loss_price) <= current_price:
                    raise ValueError(f"Stop loss ({stop_loss_price}) should be above current price ({current_price}) for SHORT position")
            
            self.logger.info(f"Placing OCO orders for {position_side} position: "
                           f"TP@{take_profit_price} SL@{stop_loss_price}")
            
            # Place Take Profit Order (Limit)
            tp_order = self.client.futures_create_order(
                symbol=symbol.upper(),
                side=tp_side,
                type='LIMIT',
                timeInForce='GTC',
                quantity=str(quantity),
                price=str(take_profit_price),
                reduceOnly='true'  # This closes the position
            )
            
            # Place Stop Loss Order (Stop Market)
            sl_order = self.client.futures_create_order(
                symbol=symbol.upper(),
                side=sl_side,
                type='STOP_MARKET',
                quantity=str(quantity),
                stopPrice=str(stop_loss_price),
                reduceOnly='true'  # This closes the position
            )
            
            # Track OCO pair
            oco_id = f"oco_{int(time.time())}"
            self.oco_pairs[oco_id] = {
                'symbol': symbol.upper(),
                'quantity': quantity,
                'position_side': position_side,
                'take_profit': tp_order,
                'stop_loss': sl_order,
                'created_at': datetime.now().isoformat(),
                'status': 'ACTIVE'
            }
            
            self.log_order_result("OCO_TAKE_PROFIT", tp_order)
            self.log_order_result("OCO_STOP_LOSS", sl_order)
            
            # Enhanced output
            print(f"\n✅ OCO ORDERS PLACED")
            print(f"{'='*60}")
            print(f"OCO ID:           {oco_id}")
            print(f"Symbol:           {symbol.upper()}")
            print(f"Position Side:    {position_side}")
            print(f"Quantity:         {quantity}")
            print(f"Current Price:    {current_price} USDT")
            print(f"")
            print(f"📈 TAKE PROFIT ORDER:")
            print(f"   Order ID:      {tp_order['orderId']}")
            print(f"   Side:          {tp_order['side']}")
            print(f"   Type:          LIMIT")
            print(f"   Price:         {take_profit_price} USDT")
            print(f"   Potential P&L: {((float(take_profit_price) - current_price) / current_price * 100):+.2f}%")
            print(f"")
            print(f"📉 STOP LOSS ORDER:")
            print(f"   Order ID:      {sl_order['orderId']}")
            print(f"   Side:          {sl_order['side']}")
            print(f"   Type:          STOP_MARKET")
            print(f"   Stop Price:    {stop_loss_price} USDT")
            print(f"   Potential P&L: {((float(stop_loss_price) - current_price) / current_price * 100):+.2f}%")
            print(f"")
            print(f"Timestamp:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            print(f"💡 When one order executes, manually cancel the other")
            print(f"   (True OCO requires exchange support)\n")
            
            # Start monitoring thread (optional enhancement)
            monitor_thread = threading.Thread(
                target=self._monitor_oco_orders, 
                args=(oco_id,),
                daemon=True
            )
            monitor_thread.start()
            
            return {
                'oco_id': oco_id,
                'take_profit': tp_order,
                'stop_loss': sl_order
            }
            
        except Exception as e:
            self.logger.error(f"OCO order failed: {e}")
            print(f"\n❌ OCO ORDER FAILED")
            print(f"Error: {str(e)}\n")
            return None
    
    def _monitor_oco_orders(self, oco_id):
        """Monitor OCO orders and cancel opposite when one fills"""
        try:
            oco_data = self.oco_pairs[oco_id]
            symbol = oco_data['symbol']
            tp_order_id = oco_data['take_profit']['orderId']
            sl_order_id = oco_data['stop_loss']['orderId']
            
            self.logger.info(f"Starting OCO monitoring for {oco_id}")
            
            while True:
                time.sleep(30)  # Check every 30 seconds
                
                # Check take profit order
                tp_status = self.client.futures_get_order(symbol=symbol, orderId=tp_order_id)
                sl_status = self.client.futures_get_order(symbol=symbol, orderId=sl_order_id)
                
                if tp_status['status'] == 'FILLED':
                    # Take profit filled, cancel stop loss
                    self.logger.info(f"OCO {oco_id}: Take profit filled, cancelling stop loss")
                    try:
                        self.client.futures_cancel_order(symbol=symbol, orderId=sl_order_id)
                        print(f"✅ OCO {oco_id}: Take profit executed, stop loss cancelled")
                    except:
                        pass  # May already be cancelled
                    break
                    
                elif sl_status['status'] == 'FILLED':
                    # Stop loss filled, cancel take profit
                    self.logger.info(f"OCO {oco_id}: Stop loss filled, cancelling take profit")
                    try:
                        self.client.futures_cancel_order(symbol=symbol, orderId=tp_order_id)
                        print(f"✅ OCO {oco_id}: Stop loss executed, take profit cancelled")
                    except:
                        pass  # May already be cancelled
                    break
                    
                elif tp_status['status'] == 'CANCELED' or sl_status['status'] == 'CANCELED':
                    # One order cancelled externally
                    self.logger.info(f"OCO {oco_id}: One order cancelled externally")
                    break
                    
        except Exception as e:
            self.logger.error(f"OCO monitoring error for {oco_id}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='Place OCO (One-Cancels-Other) orders',
        epilog='Example: python oco.py BTCUSDT 0.001 45000 30000 --position LONG'
    )
    parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('quantity', type=float, help='Order quantity')
    parser.add_argument('take_profit_price', type=float, help='Take profit price')
    parser.add_argument('stop_loss_price', type=float, help='Stop loss price')
    parser.add_argument('--position', choices=['LONG', 'SHORT'], default='LONG',
                        help='Position side (default: LONG)')
    
    args = parser.parse_args()
    
    try:
        bot = OCOBot()
        result = bot.place_oco_order(
            args.symbol, args.quantity, args.take_profit_price, 
            args.stop_loss_price, args.position
        )
        
        if result:
            print(f"Use these commands to check order status:")
            print(f"  Check TP: python -c \"from bot_base import AdvancedBot; bot=AdvancedBot(); print(bot.client.futures_get_order(symbol='{args.symbol}', orderId={result['take_profit']['orderId']}))\"")
            print(f"  Check SL: python -c \"from bot_base import AdvancedBot; bot=AdvancedBot(); print(bot.client.futures_get_order(symbol='{args.symbol}', orderId={result['stop_loss']['orderId']}))\"")
        
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
