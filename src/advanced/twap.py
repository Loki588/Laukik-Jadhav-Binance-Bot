#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import time
import threading
from datetime import datetime, timedelta
from bot_base import AdvancedBot

class TWAPBot(AdvancedBot):
    def __init__(self):
        super().__init__()
        self.active_twaps = {}

    def execute_twap_strategy(self, symbol, side, total_quantity, duration_minutes, 
                             price_limit=None, randomize_timing=True):
        """
        Execute TWAP (Time-Weighted Average Price) strategy
        Splits large order into smaller chunks over time
        """
        try:
            # Validation
            if not self.validate_symbol(symbol):
                raise ValueError(f"Invalid symbol: {symbol}")
            if side.upper() not in ['BUY', 'SELL']:
                raise ValueError(f"Invalid side: {side}")
            self.validate_quantity(symbol, total_quantity)
            if duration_minutes <= 0:
                raise ValueError("Duration must be positive")

            # Calculate TWAP parameters
            num_chunks = min(10, max(1, int(duration_minutes / 2)))  # 1 chunk per 2 minutes minimum
            interval_minutes = duration_minutes / num_chunks

            # Get step size for symbol
            step_size = 0.001  # Default for BTCUSDT
            try:
                info = self.client.futures_exchange_info()
                for s in info['symbols']:
                    if s['symbol'] == symbol.upper():
                        for f in s['filters']:
                            if f['filterType'] == 'LOT_SIZE':
                                step_size = float(f['stepSize'])
            except Exception:
                pass  # fallback to default

            # Calculate chunk sizes rounded to step size
            raw_chunk = total_quantity / num_chunks
            chunk_sizes = [round(raw_chunk / step_size) * step_size] * num_chunks
            # Adjust last chunk to fix any rounding error
            chunk_sum = sum(chunk_sizes)
            if abs(chunk_sum - total_quantity) > 1e-8:
                diff = total_quantity - chunk_sum
                chunk_sizes[-1] += diff
                # Round last chunk again
                chunk_sizes[-1] = round(chunk_sizes[-1] / step_size) * step_size

            # Validate all chunk sizes
            for q in chunk_sizes:
                self.validate_quantity(symbol, q)

            current_price = self.get_current_price(symbol)

            # Warn if any chunk does not meet notional minimum
            notional_min = 100
            invalid_chunks = []
            for idx, q in enumerate(chunk_sizes):
                notional = q * (price_limit if price_limit else current_price)
                if notional < notional_min:
                    invalid_chunks.append((idx+1, q, notional))
            if invalid_chunks:
                print("\n⚠️  WARNING: Some chunks do not meet Binance's 100 USDT notional minimum:")
                for cid, q, n in invalid_chunks:
                    print(f"  Chunk {cid}: quantity={q}, notional={n:.2f} USDT")
                print("\nTo fix: Use a higher total quantity, fewer chunks, or a higher price limit so each chunk's notional is at least 100 USDT.")
                print("If you continue, these chunks will fail to execute.")
                
            self.validate_quantity(symbol, total_quantity)
            
            if duration_minutes <= 0:
                raise ValueError("Duration must be positive")
            

            # Calculate TWAP parameters
            # Default to 10 chunks, but ensure each chunk meets minimum quantity
            num_chunks = min(10, max(1, int(duration_minutes / 2)))  # 1 chunk per 2 minutes minimum
            interval_minutes = duration_minutes / num_chunks

            # Get step size for symbol
            step_size = 0.001  # Default for BTCUSDT
            try:
                info = self.client.futures_exchange_info()
                for s in info['symbols']:
                    if s['symbol'] == symbol.upper():
                        for f in s['filters']:
                            if f['filterType'] == 'LOT_SIZE':
                                step_size = float(f['stepSize'])
            except Exception:
                pass  # fallback to default

            # Calculate chunk sizes rounded to step size
            raw_chunk = total_quantity / num_chunks
            chunk_sizes = [round(raw_chunk / step_size) * step_size] * num_chunks
            # Adjust last chunk to fix any rounding error
            chunk_sum = sum(chunk_sizes)
            if abs(chunk_sum - total_quantity) > 1e-8:
                diff = total_quantity - chunk_sum
                chunk_sizes[-1] += diff
                # Round last chunk again
                chunk_sizes[-1] = round(chunk_sizes[-1] / step_size) * step_size


            # Validate all chunk sizes
            for q in chunk_sizes:
                self.validate_quantity(symbol, q)

            # Warn if any chunk does not meet notional minimum
            notional_min = 100
            invalid_chunks = []
            for idx, q in enumerate(chunk_sizes):
                notional = q * (price_limit if price_limit else current_price)
                if notional < notional_min:
                    invalid_chunks.append((idx+1, q, notional))
            if invalid_chunks:
                print("\n⚠️  WARNING: Some chunks do not meet Binance's 100 USDT notional minimum:")
                for cid, q, n in invalid_chunks:
                    print(f"  Chunk {cid}: quantity={q}, notional={n:.2f} USDT")
                print("\nTo fix: Use a higher total quantity, fewer chunks, or a higher price limit so each chunk's notional is at least 100 USDT.")
                print("If you continue, these chunks will fail to execute.")
            
            current_price = self.get_current_price(symbol)
            
            # Create TWAP execution plan
            twap_id = f"twap_{int(time.time())}"
            execution_plan = []
            
            import random
            base_interval = interval_minutes * 60  # Convert to seconds
            
            for i in range(num_chunks):
                # Randomize timing if enabled (±30% of interval)
                if randomize_timing and i > 0:
                    timing_variance = random.uniform(-0.3, 0.3) * base_interval
                    execution_time = datetime.now() + timedelta(seconds=(i * base_interval + timing_variance))
                else:
                    execution_time = datetime.now() + timedelta(seconds=(i * base_interval))

                chunk_quantity = chunk_sizes[i]

                execution_plan.append({
                    'chunk_id': i + 1,
                    'quantity': chunk_quantity,
                    'execution_time': execution_time,
                    'status': 'PENDING'
                })
            
            # Store TWAP data
            self.active_twaps[twap_id] = {
                'symbol': symbol.upper(),
                'side': side.upper(),
                'total_quantity': total_quantity,
                'duration_minutes': duration_minutes,
                'num_chunks': num_chunks,
                'price_limit': price_limit,
                'execution_plan': execution_plan,
                'executed_chunks': [],
                'created_at': datetime.now().isoformat(),
                'status': 'ACTIVE'
            }
            
            self.logger.info(f"TWAP strategy initiated: {twap_id}")
            
            # Enhanced output
            print(f"\n✅ TWAP STRATEGY INITIATED")
            print(f"{'='*60}")
            print(f"TWAP ID:          {twap_id}")
            print(f"Symbol:           {symbol.upper()}")
            print(f"Side:             {side.upper()}")
            print(f"Total Quantity:   {total_quantity}")
            print(f"Duration:         {duration_minutes} minutes")
            print(f"Number of Chunks: {num_chunks}")
            print(f"Chunk Sizes:      {[f'{q:.6f}' for q in chunk_sizes]}")
            print(f"Interval:         ~{interval_minutes:.1f} minutes")
            print(f"Current Price:    {current_price} USDT")
            print(f"Price Limit:      {'Market' if not price_limit else f'{price_limit} USDT'}")
            print(f"Randomized:       {randomize_timing}")
            print(f"Start Time:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"End Time:         {(datetime.now() + timedelta(minutes=duration_minutes)).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # Show execution schedule
            print(f"\n📅 EXECUTION SCHEDULE:")
            for chunk in execution_plan:
                print(f"  Chunk {chunk['chunk_id']:2d}: {chunk['quantity']:8.6f} at {chunk['execution_time'].strftime('%H:%M:%S')}")
            
            print(f"\n🚀 TWAP execution started in background...")
            print(f"   Monitor progress in bot.log\n")
            
            # Start execution thread
            execution_thread = threading.Thread(
                target=self._execute_twap_chunks,
                args=(twap_id,),
                daemon=False
            )
            execution_thread.start()
            
            return {
                'twap_id': twap_id,
                'execution_plan': execution_plan,
                'thread': execution_thread
            }
            
        except Exception as e:
            self.logger.error(f"TWAP strategy failed: {e}")
            print(f"\n❌ TWAP STRATEGY FAILED")
            print(f"Error: {str(e)}\n")
            return None
    
    def _execute_twap_chunks(self, twap_id):
        """Execute TWAP chunks according to schedule"""
        try:
            twap_data = self.active_twaps[twap_id]
            symbol = twap_data['symbol']
            side = twap_data['side']
            price_limit = twap_data['price_limit']
            execution_plan = twap_data['execution_plan']
            
            total_executed = 0
            execution_prices = []
            
            self.logger.info(f"Starting TWAP execution for {twap_id}")
            
            for chunk in execution_plan:
                # Wait until execution time
                now = datetime.now()
                if chunk['execution_time'] > now:
                    wait_seconds = (chunk['execution_time'] - now).total_seconds()
                    self.logger.info(f"TWAP {twap_id} chunk {chunk['chunk_id']}: waiting {wait_seconds:.1f}s")
                    time.sleep(wait_seconds)
                
                # Execute chunk
                try:
                    if price_limit:
                        # Use limit order
                        order = self.client.futures_create_order(
                            symbol=symbol,
                            side=side,
                            type='LIMIT',
                            timeInForce='GTC',
                            quantity=str(chunk['quantity']),
                            price=str(price_limit)
                        )
                    else:
                        # Use market order
                        order = self.client.futures_create_order(
                            symbol=symbol,
                            side=side,
                            type='MARKET',
                            quantity=str(chunk['quantity'])
                        )
                    
                    # Get execution price
                    if order['status'] == 'FILLED':
                        # For market orders, we need to get the actual fill price
                        # For simplicity, we'll use current market price
                        exec_price = self.get_current_price(symbol)
                        execution_prices.append(exec_price)
                    else:
                        exec_price = float(order.get('price', 0))
                    
                    chunk['status'] = 'EXECUTED'
                    chunk['order_id'] = order['orderId']
                    chunk['execution_price'] = exec_price
                    
                    total_executed += chunk['quantity']
                    
                    twap_data['executed_chunks'].append(chunk)
                    
                    self.logger.info(f"TWAP {twap_id} chunk {chunk['chunk_id']} executed: "
                                   f"{chunk['quantity']} at {exec_price}")
                    
                    print(f"✅ TWAP {twap_id} - Chunk {chunk['chunk_id']}/{len(execution_plan)} executed")
                    print(f"   Quantity: {chunk['quantity']}, Price: {exec_price}")
                    print(f"   Progress: {total_executed}/{twap_data['total_quantity']} ({total_executed/twap_data['total_quantity']*100:.1f}%)")
                    
                except Exception as e:
                    chunk['status'] = 'FAILED'
                    chunk['error'] = str(e)
                    self.logger.error(f"TWAP {twap_id} chunk {chunk['chunk_id']} failed: {e}")
                    print(f"❌ TWAP {twap_id} - Chunk {chunk['chunk_id']} failed: {e}")
            
            # Calculate TWAP average price
            if execution_prices:
                avg_price = sum(execution_prices) / len(execution_prices)
                twap_data['average_execution_price'] = avg_price
                twap_data['status'] = 'COMPLETED'
                
                print(f"\n🎯 TWAP {twap_id} COMPLETED")
                print(f"   Total Executed: {total_executed}")
                print(f"   Average Price: {avg_price:.2f} USDT")
                print(f"   Successful Chunks: {len(execution_prices)}/{len(execution_plan)}")
                
                self.logger.info(f"TWAP {twap_id} completed. Average price: {avg_price}")
            else:
                twap_data['status'] = 'FAILED'
                self.logger.error(f"TWAP {twap_id} failed - no successful executions")
                
        except Exception as e:
            self.logger.error(f"TWAP execution error for {twap_id}: {e}")
            self.active_twaps[twap_id]['status'] = 'ERROR'

def main():
    parser = argparse.ArgumentParser(
        description='Execute TWAP (Time-Weighted Average Price) strategy',
        epilog='Example: python twap.py BTCUSDT BUY 0.01 30 --chunks 5'
    )
    parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('side', help='Order side (BUY/SELL)')
    parser.add_argument('total_quantity', type=float, help='Total quantity to trade')
    parser.add_argument('duration', type=int, help='Duration in minutes')
    parser.add_argument('--price-limit', type=float, help='Price limit (use market if not specified)')
    parser.add_argument('--no-randomize', action='store_true', help='Disable timing randomization')
    
    args = parser.parse_args()
    
    try:
        bot = TWAPBot()
        result = bot.execute_twap_strategy(
            args.symbol, args.side, args.total_quantity, args.duration,
            args.price_limit, not args.no_randomize
        )
        
        if result:
            # Wait for completion
            result['thread'].join()
            print(f"\n✅ TWAP strategy execution finished")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  TWAP execution interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
