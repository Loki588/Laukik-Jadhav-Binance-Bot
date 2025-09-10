#!/usr/bin/env python3
import pandas as pd
import requests
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot_base import AdvancedBot

class HistoricalDataAnalyzer(AdvancedBot):
    def __init__(self):
        super().__init__()
        self.historical_data = None
        
    def load_historical_data_from_drive(self, drive_url=None):
        """Load historical data from Google Drive link"""
        try:
            if not drive_url:
                # Use the provided Google Drive link
                drive_url = "https://drive.google.com/file/d/1IAfLZwu6rJzyWKgBToqwSmmVYU6VbjVs/view"
                
            # Convert Google Drive sharing link to direct download
            file_id = drive_url.split('/d/')[1].split('/')[0]
            download_url = f"https://drive.google.com/uc?id={file_id}"
            
            print(f" Downloading historical data from Google Drive...")
            
            # Download and load data
            self.historical_data = pd.read_csv(download_url)
            
            self.logger.info(f"Historical data loaded: {len(self.historical_data)} records")
            print(f" Historical data loaded: {len(self.historical_data)} records")
            
            # Display data info
            print(f"\n Data Overview:")
            print(f"   Columns: {list(self.historical_data.columns)}")
            print(f"   Data type: Trading execution records")
            print(f"   Shape: {self.historical_data.shape}")
            
            # Show sample data
            if len(self.historical_data) > 0:
                print(f"\n Sample Data (first 2 rows):")
                print(self.historical_data.head(2)[['Coin', 'Execution Price', 'Size USD', 'Side']].to_string())
            
            return self.historical_data
            
        except Exception as e:
            self.logger.error(f"Error loading historical data: {e}")
            print(f"❌ Error loading historical data: {e}")
            return None
    
    def analyze_trading_patterns(self, symbol='BTC'):
        """Analyze trading execution patterns for TWAP optimization"""
        try:
            if self.historical_data is None:
                raise ValueError("No historical data loaded")
            
            # Filter for specific coin if requested
            if 'Coin' in self.historical_data.columns:
                symbol_data = self.historical_data[self.historical_data['Coin'].str.contains(symbol, case=False, na=False)]
                if len(symbol_data) == 0:
                    symbol_data = self.historical_data  # Use all data if symbol not found
            else:
                symbol_data = self.historical_data
            
            print(f"\n Trading Pattern Analysis for {symbol}:")
            print(f"   Analyzed {len(symbol_data)} trades")
            
            # Analyze execution prices if available
            if 'Execution Price' in symbol_data.columns:
                prices = pd.to_numeric(symbol_data['Execution Price'], errors='coerce').dropna()
                
                if len(prices) > 0:
                    avg_price = prices.mean()
                    price_std = prices.std()
                    min_price = prices.min()
                    max_price = prices.max()
                    
                    # Calculate volatility-like metric
                    price_volatility = (price_std / avg_price) * 100 if avg_price > 0 else 0
                    
                    print(f"   Average Price: ${avg_price:.2f}")
                    print(f"   Price Range: ${min_price:.2f} - ${max_price:.2f}")
                    print(f"   Price Volatility: {price_volatility:.2f}%")
                    
                    # Optimal TWAP recommendations based on price volatility
                    if price_volatility < 2:
                        twap_recommendation = "Low volatility - use shorter intervals"
                        optimal_intervals = [5, 10, 15]  # minutes
                    elif price_volatility < 5:
                        twap_recommendation = "Medium volatility - use standard intervals"
                        optimal_intervals = [10, 15, 30]
                    else:
                        twap_recommendation = "High volatility - use longer intervals"
                        optimal_intervals = [30, 45, 60]
                    
                    print(f"   TWAP Recommendation: {twap_recommendation}")
                    print(f"   Optimal TWAP Intervals: {optimal_intervals} minutes")
            
            # Analyze trading sides
            if 'Side' in symbol_data.columns:
                side_counts = symbol_data['Side'].value_counts()
                total_trades = len(symbol_data)
                
                print(f"\n Trading Distribution:")
                for side, count in side_counts.items():
                    percentage = (count / total_trades) * 100
                    print(f"   {side}: {count} trades ({percentage:.1f}%)")
            
            # Analyze PnL patterns
            if 'Closed PnL' in symbol_data.columns:
                pnl_data = pd.to_numeric(symbol_data['Closed PnL'], errors='coerce').dropna()
                
                if len(pnl_data) > 0:
                    profitable_trades = (pnl_data > 0).sum()
                    losing_trades = (pnl_data < 0).sum()
                    total_pnl = pnl_data.sum()
                    avg_win = pnl_data[pnl_data > 0].mean() if profitable_trades > 0 else 0
                    avg_loss = pnl_data[pnl_data < 0].mean() if losing_trades > 0 else 0
                    
                    print(f"\n PnL Analysis:")
                    print(f"   Profitable Trades: {profitable_trades}")
                    print(f"   Losing Trades: {losing_trades}")
                    print(f"   Win Rate: {(profitable_trades / len(pnl_data) * 100):.1f}%")
                    print(f"   Average Win: ${avg_win:.2f}")
                    print(f"   Average Loss: ${avg_loss:.2f}")
                    print(f"   Total PnL: ${total_pnl:.2f}")
            
            analysis = {
                'symbol': symbol,
                'total_trades': len(symbol_data),
                'price_volatility': price_volatility if 'Execution Price' in symbol_data.columns else 0,
                'optimal_twap_intervals': optimal_intervals if 'Execution Price' in symbol_data.columns else [15, 30, 45]
            }
            
            self.logger.info(f"Trading pattern analysis completed for {symbol}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing trading patterns: {e}")
            print(f"❌ Error in analysis: {e}")
            return None
    
    def get_optimal_grid_range(self, symbol='BTC', confidence_level=0.8):
        """Calculate optimal grid range based on execution price data"""
        try:
            if self.historical_data is None:
                raise ValueError("No historical data loaded")
            
            # Filter for specific coin
            if 'Coin' in self.historical_data.columns:
                symbol_data = self.historical_data[self.historical_data['Coin'].str.contains(symbol, case=False, na=False)]
                if len(symbol_data) == 0:
                    symbol_data = self.historical_data
            else:
                symbol_data = self.historical_data
            
            if 'Execution Price' in symbol_data.columns:
                prices = pd.to_numeric(symbol_data['Execution Price'], errors='coerce').dropna()
                
                if len(prices) > 100:  # Need sufficient data
                    # Use recent data (last 25% of trades)
                    recent_prices = prices.tail(int(len(prices) * 0.25))
                    
                    min_price = recent_prices.min()
                    max_price = recent_prices.max()
                    avg_price = recent_prices.mean()
                    price_std = recent_prices.std()
                    
                    # Calculate grid range with confidence interval
                    confidence_multiplier = {0.8: 1.28, 0.9: 1.64, 0.95: 1.96}[confidence_level]
                    
                    # Expand range by standard deviation
                    range_expansion = price_std * confidence_multiplier * 0.1
                    suggested_low = min_price - range_expansion
                    suggested_high = max_price + range_expansion
                    
                    # Ensure reasonable bounds (at least 5% range)
                    min_range = avg_price * 0.05
                    if (suggested_high - suggested_low) < min_range:
                        suggested_low = avg_price - (min_range / 2)
                        suggested_high = avg_price + (min_range / 2)
                    
                    grid_range = {
                        'suggested_low': suggested_low,
                        'suggested_high': suggested_high,
                        'avg_price': avg_price,
                        'recent_low': min_price,
                        'recent_high': max_price,
                        'confidence_level': confidence_level,
                        'price_std': price_std
                    }
                    
                    print(f"\n Grid Range Analysis for {symbol}:")
                    print(f"   Recent Price Range: ${min_price:.2f} - ${max_price:.2f}")
                    print(f"   Average Price: ${avg_price:.2f}")
                    print(f"   Suggested Grid Low: ${suggested_low:.2f}")
                    print(f"   Suggested Grid High: ${suggested_high:.2f}")
                    print(f"   Grid Range: ${suggested_high - suggested_low:.2f}")
                    print(f"   Confidence Level: {confidence_level * 100}%")
                    
                    self.logger.info(f"Grid range analysis completed for {symbol}")
                    return grid_range
                else:
                    print(f"❌ Insufficient price data for {symbol} (need >100 records)")
                    return None
            else:
                print(f"❌ No execution price data found")
                return None
                
        except Exception as e:
            self.logger.error(f"Error calculating grid range: {e}")
            print(f"❌ Error in grid range calculation: {e}")
            return None

def main():
    analyzer = HistoricalDataAnalyzer()
    
    # Load historical data
    data = analyzer.load_historical_data_from_drive()
    
    if data is not None:
        print(f" Data loading successful - ready for analysis")
        
        # Analyze trading patterns for BTC
        btc_analysis = analyzer.analyze_trading_patterns('BTC')
        
        # Calculate optimal grid range for BTC
        grid_analysis = analyzer.get_optimal_grid_range('BTC')
        
        # Show top traded coins
        if 'Coin' in data.columns:
            print(f"\n Top Traded Coins:")
            top_coins = data['Coin'].value_counts().head(5)
            for coin, count in top_coins.items():
                print(f"   {coin}: {count} trades")
        
        

if __name__ == "__main__":
    main()
