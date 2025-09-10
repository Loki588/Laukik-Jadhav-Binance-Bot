#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import time
import threading
from datetime import datetime
from bot_base import AdvancedBot

class GridBot(AdvancedBot):
    def _get_tick_size(self, symbol):
        # Default tick size for BTCUSDT
        tick_size = 0.10
        try:
            info = self.client.futures_exchange_info()
            for s in info['symbols']:
                if s['symbol'] == symbol.upper():
                    for f in s['filters']:
                        if f['filterType'] == 'PRICE_FILTER':
                            tick_size = float(f['tickSize'])
        except Exception:
            pass
        return tick_size

    def __init__(self):
        super().__init__()
        self.active_grids = {}
        
    def create_grid_strategy(self, symbol, price_range_low, price_range_high, 
                           grid_levels, quantity_per_level, investment_amount=None):
        """
        Create grid trading strategy
        Places buy and sell orders at regular price intervals
        """
        try:
            # Validation
            if not self.validate_symbol(symbol):
                raise ValueError(f"Invalid symbol: {symbol}")
                
            if float(price_range_low) >= float(price_range_high):
                raise ValueError("Low range must be less than high range")
                
            if grid_levels < 2:
                raise ValueError("Grid must have at least 2 levels")
            
            current_price = self.get_current_price(symbol)
            
            if not (float(price_range_low) <= current_price <= float(price_range_high)):
                raise ValueError(f"Current price ({current_price}) must be within grid range [{price_range_low}, {price_range_high}]")
            
            # Calculate grid parameters
            price_range = float(price_range_high) - float(price_range_low)
            grid_spacing = price_range / (grid_levels - 1)
            
            # Generate grid levels
            grid_id = f"grid_{int(time.time())}"
            buy_orders = []
            sell_orders = []
            
            tick_size = self._get_tick_size(symbol)
            def round_to_tick(price):
                return round(round(price / tick_size) * tick_size, 8)

            for i in range(grid_levels):
                level_price = float(price_range_low) + (i * grid_spacing)
                level_price = round_to_tick(level_price)
                if level_price < current_price:
                    # Place buy orders below current price
                    buy_orders.append({
                        'level': i + 1,
                        'price': level_price,
                        'quantity': quantity_per_level,
                        'status': 'PENDING'
                    })
                elif level_price > current_price:
                    # Place sell orders above current price
                    sell_orders.append({
                        'level': i + 1,
                        'price': level_price,
                        'quantity': quantity_per_level,
                        'status': 'PENDING'
                    })
            
            # Store grid data
            self.active_grids[grid_id] = {
                'symbol': symbol.upper(),
                'price_range_low': float(price_range_low),
                'price_range_high': float(price_range_high),
                'grid_levels': grid_levels,
                'grid_spacing': grid_spacing,
                'quantity_per_level': quantity_per_level,
                'current_price': current_price,
                'buy_orders': buy_orders,
                'sell_orders': sell_orders,
                'executed_trades': [],
                'created_at': datetime.now().isoformat(),
                'status': 'ACTIVE'
            }
            
            self.logger.info(f"Grid strategy created: {grid_id}")
            
            # Enhanced output
            print(f"\n✅ GRID STRATEGY CREATED")
            print(f"{'='*60}")
            print(f"Grid ID:          {grid_id}")
            print(f"Symbol:           {symbol.upper()}")
            print(f"Current Price:    {current_price} USDT")
            print(f"Price Range:      {price_range_low} - {price_range_high} USDT")
            print(f"Grid Levels:      {grid_levels}")
            print(f"Grid Spacing:     {grid_spacing:.2f} USDT")
            print(f"Quantity/Level:   {quantity_per_level}")
            print(f"")
            print(f"📊 GRID SETUP:")
            print(f"   Buy Orders:    {len(buy_orders)} levels below {current_price}")
            print(f"   Sell Orders:   {len(sell_orders)} levels above {current_price}")
            print(f"   Total Orders:  {len(buy_orders) + len(sell_orders)}")
            
            if investment_amount:
                total_investment = len(buy_orders) * quantity_per_level * current_price
                print(f"   Est. Investment: {total_investment:.2f} USDT")
            
            print(f"{'='*60}")
            
            # Display grid levels
            print(f"\n📋 GRID LEVELS:")
            all_levels = []
            
            # Add buy levels
            for buy in buy_orders:
                all_levels.append((buy['level'], buy['price'], 'BUY', buy['quantity']))
            
            # Add current price level
            current_level = None
            for i in range(grid_levels):
                level_price = float(price_range_low) + (i * grid_spacing)
                if abs(level_price - current_price) < grid_spacing / 2:
                    current_level = i + 1
                    all_levels.append((current_level, current_price, 'CURRENT', 0))
                    break
            
            # Add sell levels
            for sell in sell_orders:
                all_levels.append((sell['level'], sell['price'], 'SELL', sell['quantity']))
            
            # Sort by level
            all_levels.sort(key=lambda x: x[0])
            
            for level, price, order_type, quantity in all_levels:
                if order_type == 'CURRENT':
                    print(f"   Level {level:2d}: {price:8.2f} USDT ← CURRENT PRICE")
                else:
                    print(f"   Level {level:2d}: {price:8.2f} USDT [{order_type:4s}] Qty: {quantity}")
            
            print(f"\n🚀 Placing grid orders...")
            
            # Place all grid orders
            placed_orders = self._place_grid_orders(grid_id)
            
            if placed_orders:
                print(f"✅ Grid orders placed successfully!")
                print(f"   Buy Orders:  {placed_orders['buy_count']}")
                print(f"   Sell Orders: {placed_orders['sell_count']}")
                print(f"   Total:       {placed_orders['total_count']}")
                
                # Start monitoring
                monitor_thread = threading.Thread(
                    target=self._monitor_grid_orders,
                    args=(grid_id,),
                    daemon=True
                )
                monitor_thread.start()
                
                return {
                    'grid_id': grid_id,
                    'placed_orders': placed_orders,
                    'monitor_thread': monitor_thread
                }
            else:
                print(f"❌ Failed to place grid orders")
                return None
                
        except Exception as e:
            self.logger.error(f"Grid strategy failed: {e}")
            print(f"\n❌ GRID STRATEGY FAILED")
            print(f"Error: {str(e)}\n")
            return None
    
    def _place_grid_orders(self, grid_id):
        """Place all grid orders"""
        try:
            grid_data = self.active_grids[grid_id]
            symbol = grid_data['symbol']
            
            buy_count = 0
            sell_count = 0
            
            # Place buy orders
            for buy_order in grid_data['buy_orders']:
                try:
                    order = self.client.futures_create_order(
                        symbol=symbol,
                        side='BUY',
                        type='LIMIT',
                        timeInForce='GTC',
                        quantity=str(buy_order['quantity']),
                        price=str(buy_order['price'])
                    )
                    
                    buy_order['order_id'] = order['orderId']
                    buy_order['status'] = 'PLACED'
                    buy_count += 1
                    
                    self.logger.info(f"Grid {grid_id} buy order placed: {order['orderId']} at {buy_order['price']}")
                    
                except Exception as e:
                    buy_order['status'] = 'FAILED'
                    buy_order['error'] = str(e)
                    self.logger.error(f"Grid {grid_id} buy order failed: {e}")
            
            # Place sell orders
            for sell_order in grid_data['sell_orders']:
                try:
                    order = self.client.futures_create_order(
                        symbol=symbol,
                        side='SELL',
                        type='LIMIT',
                        timeInForce='GTC',
                        quantity=str(sell_order['quantity']),
                        price=str(sell_order['price'])
                    )
                    
                    sell_order['order_id'] = order['orderId']
                    sell_order['status'] = 'PLACED'
                    sell_count += 1
                    
                    self.logger.info(f"Grid {grid_id} sell order placed: {order['orderId']} at {sell_order['price']}")
                    
                except Exception as e:
                    sell_order['status'] = 'FAILED'
                    sell_order['error'] = str(e)
                    self.logger.error(f"Grid {grid_id} sell order failed: {e}")
            
            return {
                'buy_count': buy_count,
                'sell_count': sell_count,
                'total_count': buy_count + sell_count
            }
            
        except Exception as e:
            self.logger.error(f"Error placing grid orders for {grid_id}: {e}")
            return None
    
    def _monitor_grid_orders(self, grid_id):
        """Monitor grid orders and replace filled orders"""
        try:
            grid_data = self.active_grids[grid_id]
            symbol = grid_data['symbol']
            
            self.logger.info(f"Starting grid monitoring for {grid_id}")
            
            while grid_data['status'] == 'ACTIVE':
                time.sleep(60)  # Check every minute
                
                # Check buy orders
                for buy_order in grid_data['buy_orders']:
                    if buy_order['status'] == 'PLACED':
                        try:
                            order_status = self.client.futures_get_order(
                                symbol=symbol, 
                                orderId=buy_order['order_id']
                            )
                            
                            if order_status['status'] == 'FILLED':
                                buy_order['status'] = 'FILLED'
                                grid_data['executed_trades'].append({
                                    'type': 'BUY',
                                    'price': buy_order['price'],
                                    'quantity': buy_order['quantity'],
                                    'timestamp': datetime.now().isoformat()
                                })
                                
                                print(f"🎯 Grid {grid_id}: Buy order filled at {buy_order['price']}")
                                self.logger.info(f"Grid {grid_id} buy order filled: {buy_order['order_id']}")
                                
                                # TODO: Place corresponding sell order at higher level
                                # This would implement the full grid trading logic
                                
                        except Exception as e:
                            self.logger.error(f"Error checking buy order status: {e}")
                
                # Check sell orders
                for sell_order in grid_data['sell_orders']:
                    if sell_order['status'] == 'PLACED':
                        try:
                            order_status = self.client.futures_get_order(
                                symbol=symbol, 
                                orderId=sell_order['order_id']
                            )
                            
                            if order_status['status'] == 'FILLED':
                                sell_order['status'] = 'FILLED'
                                grid_data['executed_trades'].append({
                                    'type': 'SELL',
                                    'price': sell_order['price'],
                                    'quantity': sell_order['quantity'],
                                    'timestamp': datetime.now().isoformat()
                                })
                                
                                print(f"🎯 Grid {grid_id}: Sell order filled at {sell_order['price']}")
                                self.logger.info(f"Grid {grid_id} sell order filled: {sell_order['order_id']}")
                                
                                # TODO: Place corresponding buy order at lower level
                                
                        except Exception as e:
                            self.logger.error(f"Error checking sell order status: {e}")
                            
        except Exception as e:
            self.logger.error(f"Grid monitoring error for {grid_id}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='Create grid trading strategy',
        epilog='Example: python grid_orders.py BTCUSDT 40000 50000 10 0.001'
    )
    parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('price_low', type=float, help='Grid range low price')
    parser.add_argument('price_high', type=float, help='Grid range high price')
    parser.add_argument('levels', type=int, help='Number of grid levels')
    parser.add_argument('quantity', type=float, help='Quantity per grid level')
    parser.add_argument('--investment', type=float, help='Total investment amount (optional)')
    
    args = parser.parse_args()
    
    try:
        bot = GridBot()
        result = bot.create_grid_strategy(
            args.symbol, args.price_low, args.price_high,
            args.levels, args.quantity, args.investment
        )
        
        if result:
            print(f"\n💡 Grid strategy is now active and monitoring...")
            print(f"   Press Ctrl+C to stop monitoring")
            print(f"   Check bot.log for detailed execution logs")
            
            try:
                # Keep main thread alive
                result['monitor_thread'].join()
            except KeyboardInterrupt:
                print(f"\n⚠️  Grid monitoring stopped by user")
                # TODO: Cancel all pending grid orders
                
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
