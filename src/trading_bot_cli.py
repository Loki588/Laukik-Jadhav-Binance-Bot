#!/usr/bin/env python3
"""
Binance Futures Trading Bot - Master CLI Controller
Comprehensive command-line interface for all trading strategies
"""

import sys
import os
import argparse
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot_base import AdvancedBot
from market_orders import MarketOrderBot
from limit_orders import LimitOrderBot
from advanced.stop_limit import StopLimitBot
from advanced.oco import OCOBot
from advanced.twap import TWAPBot
from advanced.grid_orders import GridBot
from data.historical_data import HistoricalDataAnalyzer
from data.sentiment_analyzer import SentimentAnalyzer

class TradingBotCLI:
    def __init__(self):
        self.bot = AdvancedBot()
        
    def show_welcome_message(self):
        """Show welcome message with beginner guidance"""
        try:
            # Get current BTC price for dynamic examples
            current_price = self.bot.get_current_price('BTCUSDT')
            min_quantity = 100 / current_price if current_price else 0.002
            
            print(f"\n🚀 BINANCE FUTURES TRADING BOT")
            print(f"{'='*60}")
            print(f" Connected to Binance Testnet (No real money involved)")
            print(f" Current BTC Price: ${current_price:,.2f}" if current_price else "📊 Fetching current prices...")
            print(f" Minimum Order Size: {min_quantity:.8f} BTC (~$100)")
            print(f"\n BEGINNER'S QUICK START:")
            print(f"   1. python src/trading_bot_cli.py status")
            print(f"   2. python src/trading_bot_cli.py price BTCUSDT")
            print(f"   3. python src/trading_bot_cli.py analyze-sentiment") 
            print(f"   4. python src/trading_bot_cli.py market BTCUSDT BUY {min_quantity:.6f}")
            print(f"{'='*60}\n")
        except Exception as e:
            print(f"\n🚀 BINANCE FUTURES TRADING BOT")
            print(f"{'='*60}")
            print(f" Connected to Binance Testnet (No real money involved)")
            print(f" Start with: python src/trading_bot_cli.py status")
            print(f"{'='*60}\n")
    
    def show_current_price(self, symbol):
        """Show current price and trading context"""
        try:
            price = self.bot.get_current_price(symbol)
            if not price:
                print(f"❌ Could not fetch price for {symbol}")
                return
                
            min_quantity = 100 / price
            
            print(f"\n {symbol.upper()} MARKET DATA")
            print(f"{'='*50}")
            print(f"Current Price:     ${price:,.2f}")
            print(f"Minimum Quantity:  {min_quantity:.8f} {symbol[:3]}")
            print(f"Min Order Value:   $100.00")
            print(f"{'='*50}")
            
            # Smart examples based on current price
            self.show_smart_examples(symbol, price, min_quantity)
            
        except Exception as e:
            print(f"❌ Error fetching price: {e}")
    
    def show_smart_examples(self, symbol, current_price, min_qty):
        """Show contextual trading examples based on current price"""
        print(f"\n SMART TRADING EXAMPLES (Based on ${current_price:,.0f}):")
        print(f"{'='*60}")
        
        # Stop-Limit Examples
        stop_loss_price = current_price * 0.95
        stop_profit_price = current_price * 1.05
        print(f"  STOP-LIMIT (Risk Management):")
        print(f"   For LONG Protection (5% stop loss):")
        print(f"   python src/trading_bot_cli.py stop-limit {symbol} SELL {min_qty:.6f} {stop_loss_price:.0f} {stop_loss_price-100:.0f}")
        
        # OCO Examples  
        take_profit = current_price * 1.07
        stop_loss = current_price * 0.93
        print(f"\n OCO (Automatic Profit/Loss):")
        print(f"   For LONG Position (+7% profit / -7% loss):")
        print(f"   python src/trading_bot_cli.py oco {symbol} {min_qty:.6f} {take_profit:.0f} {stop_loss:.0f} --position LONG")
        
        # TWAP Examples
        large_quantity = min_qty * 5
        print(f"\n TWAP (Large Order Execution):")
        print(f"   Split ${large_quantity*current_price:.0f} order over 10 minutes:")
        print(f"   python src/trading_bot_cli.py twap {symbol} BUY {large_quantity:.6f} 10")
        
        # Grid Examples
        grid_low = current_price * 0.95
        grid_high = current_price * 1.05
        print(f"\n GRID (Range Trading ±5%):")
        print(f"   Profit from {grid_low:.0f}-{grid_high:.0f} range:")
        print(f"   python src/trading_bot_cli.py grid {symbol} {grid_low:.0f} {grid_high:.0f} 8 {min_qty:.6f}")
        print(f"{'='*60}\n")

    def show_account_status(self):
        """Display account status and balance"""
        try:
            account = self.bot.get_account_info()
            if account:
                print(f"\n ACCOUNT STATUS")
                print(f"{'='*50}")
                print(f"Total Balance:        {account['totalWalletBalance']} USDT")
                print(f"Available Balance:    {account['availableBalance']} USDT") 
                print(f"Total Unrealized PNL: {account['totalUnrealizedProfit']} USDT")
                print(f"Account Update Time:  {datetime.fromtimestamp(account['updateTime']/1000).strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*50}")
                
                # Beginner tips
                print(f"\n TIPS:")
                print(f"   • This is testnet - no real money involved")
                print(f"   • Minimum order value: ~$100 USD")
                print(f"   • Use 'python src/trading_bot_cli.py price BTCUSDT' to check prices")
                
                
            else:
                print(" Unable to fetch account information")
                print(" Make sure your .env file has correct API keys")
                
        except Exception as e:
            print(f" Error fetching account status: {e}")
            print(" Common fixes:")
            print("   • Check your internet connection")
            print("   • Verify API keys in .env file")
            print("   • Ensure you're using testnet keys")

    def show_open_positions(self, symbol=None):
        """Display open positions"""
        try:
            positions = self.bot.client.futures_position_information(symbol=symbol)
            active_positions = [p for p in positions if float(p['positionAmt']) != 0]
            
            if active_positions:
                print(f"\n OPEN POSITIONS")
                print(f"{'='*70}")
                for pos in active_positions:
                    pnl_color = "🟢" if float(pos['unRealizedProfit']) >= 0 else "🔴"
                    print(f"Symbol: {pos['symbol']:12} | "
                          f"Side: {pos['positionSide']:6} | " 
                          f"Size: {pos['positionAmt']:12} | "
                          f"Entry: {pos['entryPrice']:12} | "
                          f"PNL: {pnl_color} {pos['unRealizedProfit']:12}")
                print(f"{'='*70}\n")
            else:
                print("\n No open positions")
                print(" Use market or limit orders to open positions\n")
                
        except Exception as e:
            print(f" Error fetching positions: {e}")

    def show_open_orders(self, symbol=None):
        """Display open orders"""
        try:
            orders = self.bot.client.futures_get_open_orders(symbol=symbol)
            
            if orders:
                print(f"\ OPEN ORDERS")
                print(f"{'='*80}")
                for order in orders:
                    status_icon = "⏳" if order['status'] == 'NEW' else "✅"
                    print(f"ID: {order['orderId']:12} | "
                          f"Symbol: {order['symbol']:12} | "
                          f"Side: {order['side']:4} | "
                          f"Type: {order['type']:12} | "
                          f"Qty: {order['origQty']:12} | "
                          f"Price: {order['price']:12} | "
                          f"Status: {status_icon} {order['status']}")
                print(f"{'='*80}\n")
            else:
                print(f"\n No open orders{' for ' + symbol if symbol else ''}")
                print(" Place orders using market, limit, or advanced commands\n")
                
        except Exception as e:
            print(f"❌ Error fetching orders: {e}")

def create_parser():
    """Create comprehensive argument parser with beginner-friendly help"""
    parser = argparse.ArgumentParser(
        description=' Binance Futures Trading Bot - Complete Trading Solution',
        epilog='''
 BEGINNER GUIDE - Copy these commands (include "python src/"):

 Start Here:
  python src/trading_bot_cli.py status
  python src/trading_bot_cli.py price BTCUSDT
  python src/trading_bot_cli.py status --positions --orders

  # Quick log check
    Get-Content bot.log -Tail 10
    
  # Watch logs live (press Ctrl+C to stop)
    Get-Content bot.log -Wait  

  # cancel specific order (ANY type)
    python src/trading_bot_cli.py cancel BTCUSDT 12345678  



 #Market Analysis:  
  python src/trading_bot_cli.py analyze-sentiment
  python src/trading_bot_cli.py analyze-historical

 #Basic Trading:
  python src/trading_bot_cli.py market BTCUSDT BUY 0.002
  python src/trading_bot_cli.py limit BTCUSDT SELL 0.002 45000

 #Advanced Trading:
  Stop-Limit Example (Risk Management):
  python src/trading_bot_cli.py stop-limit BTCUSDT SELL 0.002 40000 39000
  
  Current BTC Price: $42,150
  -For LONG position protection:
   python src/trading_bot_cli.py stop-limit BTCUSDT SELL 0.002 40000 39500
   If price drops to $40,000, sell at $39,500 (5% stop loss)
  
  -For SHORT position protection:  
   python src/trading_bot_cli.py stop-limit BTCUSDT BUY 0.002 44000 44500
   If price rises to $44,000, buy at $44,500 (4.4% stop loss)
  
  OCO Example (Automatic Profit/Loss):
  python src/trading_bot_cli.py oco BTCUSDT 0.002 45000 35000 --position LONG
  
  Current BTC Price: $42,150
  -For LONG position:
   python src/trading_bot_cli.py oco BTCUSDT 0.002 45000 39000 --position LONG
   Take profit at $45,000 (+6.8%) OR stop loss at $39,000 (-7.5%)
   
  -For SHORT position:
   python src/trading_bot_cli.py oco BTCUSDT 0.002 39000 45000 --position SHORT  
   Take profit at $39,000 (-7.5%) OR stop loss at $45,000 (+6.8%)
  
 Strategies:
  TWAP Example (Large Order Execution):
  python src/trading_bot_cli.py twap BTCUSDT BUY 0.005 10
  
  Current BTC Price: $42,150
  For $500 purchase (0.012 BTC):
  -Quick execution (5 min):
  python src/trading_bot_cli.py twap BTCUSDT BUY 0.012 5
  Split into 5 chunks over 5 minutes (reduce market impact)
  
  -Stealth execution (30 min):
  python src/trading_bot_cli.py twap BTCUSDT BUY 0.012 30  
  Split into 10 chunks over 30 minutes (minimal price impact)
  
  Grid Example (Range Trading):
  python src/trading_bot_cli.py grid BTCUSDT 38000 48000 5 0.002
  
  Current BTC Price: $42,150 (good for grid center)
  -Conservative grid (±5%):
  python src/trading_bot_cli.py grid BTCUSDT 40000 44000 8 0.001
  8 levels between $40k-$44k, profit from $150 price swings
  
  -Aggressive grid (±10%):
  python src/trading_bot_cli.py grid BTCUSDT 38000 46000 10 0.002
  10 levels between $38k-$46k, profit from $800 price swings


        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Price command (NEW)
    price_parser = subparsers.add_parser('price', help='Show current market price and smart examples')
    price_parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')

    # Status commands
    status_parser = subparsers.add_parser('status', help='Show account status')
    status_parser.add_argument('--positions', action='store_true', help='Show positions')
    status_parser.add_argument('--orders', action='store_true', help='Show open orders')
    status_parser.add_argument('--symbol', help='Filter by symbol')

    # Market order
    market_parser = subparsers.add_parser('market', help='Place market order')
    market_parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    market_parser.add_argument('side', help='BUY or SELL')
    market_parser.add_argument('quantity', type=float, help='Order quantity (min $100 value)')

    # Limit order
    limit_parser = subparsers.add_parser('limit', help='Place limit order')
    limit_parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    limit_parser.add_argument('side', help='BUY or SELL')
    limit_parser.add_argument('quantity', type=float, help='Order quantity (min $100 value)')
    limit_parser.add_argument('price', type=float, help='Limit price')
    limit_parser.add_argument('--tif', default='GTC', help='Time in force (GTC/IOC/FOK)')

    # Stop-limit order
    stop_parser = subparsers.add_parser('stop-limit', help='Place stop-limit order')
    stop_parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    stop_parser.add_argument('side', help='BUY or SELL')
    stop_parser.add_argument('quantity', type=float, help='Order quantity (min $100 value)')
    stop_parser.add_argument('stop_price', type=float, help='Stop trigger price')
    stop_parser.add_argument('limit_price', type=float, help='Limit execution price')
    stop_parser.add_argument('--reduce-only', action='store_true', help='Reduce position only')

    # OCO order
    oco_parser = subparsers.add_parser('oco', help='Place OCO (One-Cancels-Other) order')
    oco_parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    oco_parser.add_argument('quantity', type=float, help='Order quantity (min $100 value)')
    oco_parser.add_argument('take_profit', type=float, help='Take profit price')
    oco_parser.add_argument('stop_loss', type=float, help='Stop loss price')
    oco_parser.add_argument('--position', choices=['LONG', 'SHORT'], default='LONG', help='Position side')

    # TWAP strategy
    twap_parser = subparsers.add_parser('twap', help='Execute TWAP (Time-Weighted Average Price) strategy')
    twap_parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    twap_parser.add_argument('side', help='BUY or SELL')
    twap_parser.add_argument('quantity', type=float, help='Total quantity to trade')
    twap_parser.add_argument('duration', type=int, help='Duration in minutes')
    twap_parser.add_argument('--price-limit', type=float, help='Price limit (optional)')
    twap_parser.add_argument('--no-randomize', action='store_true', help='Disable timing randomization')

    # Grid strategy
    grid_parser = subparsers.add_parser('grid', help='Create grid trading strategy')
    grid_parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    grid_parser.add_argument('price_low', type=float, help='Grid lower bound price')
    grid_parser.add_argument('price_high', type=float, help='Grid upper bound price')
    grid_parser.add_argument('levels', type=int, help='Number of grid levels')
    grid_parser.add_argument('quantity', type=float, help='Quantity per grid level')

    # Analysis commands
    subparsers.add_parser('analyze-sentiment', help='Analyze market sentiment (Fear & Greed)')
    subparsers.add_parser('analyze-historical', help='Analyze historical data patterns')

    # Cancel command
    cancel_parser = subparsers.add_parser('cancel', help='Cancel any order by ID')
    cancel_parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    cancel_parser.add_argument('order_id', type=int, help='Order ID to cancel')

    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        # Show welcome message and help for new users
        cli = TradingBotCLI()
        cli.show_welcome_message()
        parser.print_help()
        return

    try:
        cli = TradingBotCLI()

        # Price command (NEW)
        if args.command == 'price':
            cli.show_current_price(args.symbol)

        # Status commands
        elif args.command == 'status':
            cli.show_account_status()
            if args.positions:
                cli.show_open_positions(args.symbol)
            if args.orders:
                cli.show_open_orders(args.symbol)

        # Basic orders
        elif args.command == 'market':
            print(f"🎯 Placing market {args.side} order for {args.quantity} {args.symbol}...")
            bot = MarketOrderBot()
            bot.place_market_order(args.symbol, args.side, args.quantity)

        elif args.command == 'limit':
            print(f"🎯 Placing limit {args.side} order for {args.quantity} {args.symbol} at {args.price}...")
            bot = LimitOrderBot()
            bot.place_limit_order(args.symbol, args.side, args.quantity, args.price, args.tif)

        # Advanced orders
        elif args.command == 'stop-limit':
            print(f"🎯 Placing stop-limit {args.side} order for {args.quantity} {args.symbol}...")
            bot = StopLimitBot()
            bot.place_stop_limit_order(args.symbol, args.side, args.quantity, 
                                     args.stop_price, args.limit_price, args.reduce_only)

        elif args.command == 'oco':
            print(f"🎯 Placing OCO order for {args.quantity} {args.symbol} ({args.position} position)...")
            bot = OCOBot()
            bot.place_oco_order(args.symbol, args.quantity, args.take_profit, 
                              args.stop_loss, args.position)

        # Strategies
        elif args.command == 'twap':
            print(f"🎯 Starting TWAP strategy for {args.quantity} {args.symbol} over {args.duration} minutes...")
            bot = TWAPBot()
            bot.execute_twap_strategy(args.symbol, args.side, args.quantity, args.duration,
                                    args.price_limit, not args.no_randomize)

        elif args.command == 'grid':
            print(f"🎯 Creating grid strategy for {args.symbol} ({args.levels} levels)...")
            bot = GridBot()
            bot.create_grid_strategy(args.symbol, args.price_low, args.price_high,
                                   args.levels, args.quantity)

        # Analysis
        elif args.command == 'analyze-sentiment':
            print("🎯 Analyzing market sentiment...")
            analyzer = SentimentAnalyzer()
            analyzer.load_fear_greed_data_from_drive()
            recommendations = analyzer.generate_sentiment_based_recommendations('BTCUSDT')
            if recommendations:
                print(f"\n🎯 Sentiment Analysis Results:")
                print(f"   Current Score: {recommendations['sentiment_score']}/100 ({recommendations['sentiment_label']})")
                print(f"   Risk Level: {recommendations['risk_level']}")
                print(f"   Market Outlook: {recommendations['market_outlook']}")

        elif args.command == 'analyze-historical':
            print("🎯 Analyzing historical data...")
            analyzer = HistoricalDataAnalyzer()
            data = analyzer.load_historical_data_from_drive()
            if data is not None:
                vol_analysis = analyzer.analyze_trading_patterns('BTC')
                grid_analysis = analyzer.get_optimal_grid_range('BTC')
                
                if vol_analysis:
                    print(f"\n📈 Trading Pattern Analysis:")
                    print(f"   Optimal TWAP Intervals: {vol_analysis.get('optimal_twap_intervals', 'N/A')}")
                    
                if grid_analysis:
                    print(f"\n📊 Optimal Grid Range:")
                    print(f"   Suggested: ${grid_analysis['suggested_low']:.2f} - ${grid_analysis['suggested_high']:.2f}")
        
        elif args.command == 'cancel':
            print(f"🚫 Cancelling order {args.order_id} for {args.symbol}...")
            try:
                result = cli.bot.client.futures_cancel_order(symbol=args.symbol, orderId=args.order_id)
                print(f"✅ Order {args.order_id} cancelled successfully")
                cli.bot.logger.info(f"Order cancelled: {args.order_id}")
            except Exception as e:
                print(f"❌ Error cancelling order: {e}")
        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        print("\n💡 Common solutions:")
        print("   • Check your internet connection")
        print("   • Verify .env file has correct API keys")
        print("   • Ensure minimum $100 order value")
        
        sys.exit(1)

if __name__ == "__main__":
    main()
