#!/usr/bin/env python3
import pandas as pd
import requests
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot_base import AdvancedBot

class SentimentAnalyzer(AdvancedBot):
    def __init__(self):
        super().__init__()
        self.fear_greed_data = None
        
    def load_fear_greed_data_from_drive(self, drive_url=None):
        """Load Fear & Greed index data from Google Drive"""
        try:
            if not drive_url:
                # Use the provided Google Drive link
                drive_url = "https://drive.google.com/file/d/1PgQC0tO8XN-wqkNyghWc_-mnrYv_nhSf/view"
            
            # Convert Google Drive sharing link to direct download
            file_id = drive_url.split('/d/')[1].split('/')[0]
            download_url = f"https://drive.google.com/uc?id={file_id}"
            
            print(f"📥 Downloading Fear & Greed index from Google Drive...")
            
            # Download and load data
            self.fear_greed_data = pd.read_csv(download_url)
            
            self.logger.info(f"Fear & Greed data loaded: {len(self.fear_greed_data)} records")
            print(f"✅ Fear & Greed data loaded: {len(self.fear_greed_data)} records")
            
            # Display data info
            print(f"\n📊 Sentiment Data Overview:")
            print(f"   Columns: {list(self.fear_greed_data.columns)}")
            print(f"   Shape: {self.fear_greed_data.shape}")
            if 'value' in self.fear_greed_data.columns:
                print(f"   Value range: {self.fear_greed_data['value'].min()} - {self.fear_greed_data['value'].max()}")
            
            return self.fear_greed_data
            
        except Exception as e:
            self.logger.error(f"Error loading Fear & Greed data: {e}")
            print(f"❌ Error loading Fear & Greed data: {e}")
            return None
    
    def get_current_sentiment_score(self):
        """Get current market sentiment score"""
        try:
            if self.fear_greed_data is None:
                raise ValueError("No Fear & Greed data loaded")
            
            # Get most recent sentiment score
            if 'value' in self.fear_greed_data.columns:
                current_score = self.fear_greed_data['value'].iloc[-1]
                
                sentiment_label = self.interpret_sentiment_score(current_score)
                
                self.logger.info(f"Current sentiment score: {current_score} ({sentiment_label})")
                return {
                    'score': current_score,
                    'label': sentiment_label,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                raise ValueError("No 'value' column found in Fear & Greed data")
                
        except Exception as e:
            self.logger.error(f"Error getting sentiment score: {e}")
            return None
    
    def interpret_sentiment_score(self, score):
        """Interpret numerical sentiment score"""
        if score <= 20:
            return "EXTREME_FEAR"
        elif score <= 40:
            return "FEAR"
        elif score <= 60:
            return "NEUTRAL"
        elif score <= 80:
            return "GREED"
        else:
            return "EXTREME_GREED"
    
    def get_sentiment_based_multipliers(self, sentiment_score):
        """Get trading multipliers based on sentiment"""
        sentiment_label = self.interpret_sentiment_score(sentiment_score)
        
        # Define multipliers for different strategies
        multipliers = {
            'EXTREME_FEAR': {
                'grid_spacing_multiplier': 1.5,  # Wider grids during extreme fear
                'twap_interval_multiplier': 1.3,  # Slower TWAP during volatility
                'position_size_multiplier': 1.2,  # Slightly larger positions (contrarian)
                'risk_level': 'HIGH'
            },
            'FEAR': {
                'grid_spacing_multiplier': 1.2,
                'twap_interval_multiplier': 1.1,
                'position_size_multiplier': 1.1,
                'risk_level': 'MEDIUM_HIGH'
            },
            'NEUTRAL': {
                'grid_spacing_multiplier': 1.0,
                'twap_interval_multiplier': 1.0,
                'position_size_multiplier': 1.0,
                'risk_level': 'MEDIUM'
            },
            'GREED': {
                'grid_spacing_multiplier': 1.2,
                'twap_interval_multiplier': 1.1,
                'position_size_multiplier': 0.9,  # Smaller positions during greed
                'risk_level': 'MEDIUM_HIGH'
            },
            'EXTREME_GREED': {
                'grid_spacing_multiplier': 1.5,  # Wider grids during extreme greed
                'twap_interval_multiplier': 1.3,
                'position_size_multiplier': 0.8,  # Much smaller positions
                'risk_level': 'HIGH'
            }
        }
        
        return multipliers.get(sentiment_label, multipliers['NEUTRAL'])
    
    def generate_sentiment_based_recommendations(self, symbol):
        """Generate trading recommendations based on sentiment"""
        try:
            sentiment = self.get_current_sentiment_score()
            if not sentiment:
                return None
            
            multipliers = self.get_sentiment_based_multipliers(sentiment['score'])
            current_price = self.get_current_price(symbol)
            
            recommendations = {
                'symbol': symbol,
                'current_price': current_price,
                'sentiment_score': sentiment['score'],
                'sentiment_label': sentiment['label'],
                'risk_level': multipliers['risk_level'],
                'strategy_adjustments': {
                    'grid_trading': {
                        'recommended': multipliers['risk_level'] in ['MEDIUM', 'MEDIUM_HIGH'],
                        'spacing_adjustment': f"{(multipliers['grid_spacing_multiplier'] - 1) * 100:+.1f}%",
                        'suggested_range_low': current_price * (1 - 0.05 * multipliers['grid_spacing_multiplier']),
                        'suggested_range_high': current_price * (1 + 0.05 * multipliers['grid_spacing_multiplier'])
                    },
                    'twap_strategy': {
                        'recommended': True,
                        'interval_adjustment': f"{(multipliers['twap_interval_multiplier'] - 1) * 100:+.1f}%",
                        'suggested_duration': int(30 * multipliers['twap_interval_multiplier'])  # minutes
                    },
                    'position_sizing': {
                        'size_adjustment': f"{(multipliers['position_size_multiplier'] - 1) * 100:+.1f}%",
                        'max_risk_per_trade': 2.0 / multipliers['position_size_multiplier']  # % of account
                    }
                },
                'market_outlook': self.get_market_outlook(sentiment['label']),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Sentiment-based recommendations generated for {symbol}")
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return None
    
    def get_market_outlook(self, sentiment_label):
        """Get market outlook based on sentiment"""
        outlooks = {
            'EXTREME_FEAR': "Market in extreme fear. Potential buying opportunity for contrarian strategies. High volatility expected.",
            'FEAR': "Fearful market sentiment. Consider careful accumulation strategies. Moderate volatility likely.",
            'NEUTRAL': "Balanced market sentiment. Normal trading strategies recommended. Standard volatility expected.",
            'GREED': "Greedy market sentiment. Consider profit-taking strategies. Moderate volatility likely.",
            'EXTREME_GREED': "Market in extreme greed. High risk of reversal. Consider defensive strategies. High volatility expected."
        }
        
        return outlooks.get(sentiment_label, "Unable to determine market outlook")

def main():
    analyzer = SentimentAnalyzer()
    
    # Load Fear & Greed data
    data = analyzer.load_fear_greed_data_from_drive()
    
    if data is not None:
        # Get current sentiment
        sentiment = analyzer.get_current_sentiment_score()
        if sentiment:
            print(f"\n😱📈 Current Market Sentiment:")
            print(f"   Score: {sentiment['score']}/100")
            print(f"   Label: {sentiment['label']}")
        
        # Generate recommendations
        recommendations = analyzer.generate_sentiment_based_recommendations('BTCUSDT')
        if recommendations:
            print(f"\n🎯 Sentiment-Based Recommendations:")
            print(f"   Risk Level: {recommendations['risk_level']}")
            print(f"   Grid Trading: {'✅ Recommended' if recommendations['strategy_adjustments']['grid_trading']['recommended'] else '❌ Not Recommended'}")
            print(f"   Grid Spacing: {recommendations['strategy_adjustments']['grid_trading']['spacing_adjustment']}")
            print(f"   TWAP Interval: {recommendations['strategy_adjustments']['twap_strategy']['interval_adjustment']}")
            print(f"   Position Size: {recommendations['strategy_adjustments']['position_sizing']['size_adjustment']}")
            print(f"\n📊 Market Outlook:")
            print(f"   {recommendations['market_outlook']}")

if __name__ == "__main__":
    main()
