import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, TextBox, CheckButtons
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class TradierGEXAnalyzer:
    def __init__(self, api_key):
        """
        Initialize the GEX Analyzer
        
        Args:
            api_key: Your Tradier API token
        """
        self.api_key = api_key
        self.ticker = 'SPX'
        self.expiration_type = '0DTE'
        self.auto_refresh = True
        self.update_interval = 60000  # ms
        self.base_url = "https://api.tradier.com/v1"
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json'
        }
        
        # Data storage
        self.current_price = 0
        self.gex_data = None
        self.last_update = None
        self.current_expiration = None
        
        # Create figure with subplots and controls
        self.fig = plt.figure(figsize=(18, 12))
        gs = self.fig.add_gridspec(4, 3, hspace=0.3, wspace=0.3)
        
        # Control panel (top)
        self.ax_controls = self.fig.add_subplot(gs[0, :])
        self.ax_controls.axis('off')
        
        # Stats panel
        self.ax_stats = self.fig.add_subplot(gs[1, :])
        self.ax_stats.axis('off')
        
        # Charts
        self.ax_gex = self.fig.add_subplot(gs[2, :])
        self.ax_cumulative = self.fig.add_subplot(gs[3, 0:2])
        self.ax_recommendation = self.fig.add_subplot(gs[3, 2])
        self.ax_recommendation.axis('off')
        
        self.setup_controls()
        
    def setup_controls(self):
        """Setup interactive controls"""
        # Title
        self.fig.suptitle('Real-time GEX Dashboard - Live Tradier Data', 
                         fontsize=16, fontweight='bold')
        
        # Ticker buttons
        ticker_positions = [0.05, 0.12, 0.19, 0.26, 0.33, 0.40]
        tickers = ['SPX', 'SPY', 'QQQ', 'AAPL', 'TSLA', 'CUSTOM']
        self.ticker_buttons = []
        
        for i, ticker in enumerate(tickers):
            ax_btn = plt.axes([ticker_positions[i], 0.92, 0.06, 0.04])
            btn = Button(ax_btn, ticker, color='lightblue', hovercolor='skyblue')
            btn.label.set_fontsize(10)
            btn.on_clicked(lambda event, t=ticker: self.change_ticker(t))
            self.ticker_buttons.append(btn)
        
        # Expiration type buttons
        exp_positions = [0.50, 0.57, 0.64, 0.71]
        expirations = ['0DTE', '1DTE', 'Weekly', 'Monthly']
        self.exp_buttons = []
        
        for i, exp in enumerate(expirations):
            ax_btn = plt.axes([exp_positions[i], 0.92, 0.06, 0.04])
            btn = Button(ax_btn, exp, color='lightgreen', hovercolor='lightcoral')
            btn.label.set_fontsize(10)
            btn.on_clicked(lambda event, e=exp: self.change_expiration(e))
            self.exp_buttons.append(btn)
        
        # Refresh button
        ax_refresh = plt.axes([0.80, 0.92, 0.08, 0.04])
        self.refresh_btn = Button(ax_refresh, 'Refresh Now', color='orange', hovercolor='gold')
        self.refresh_btn.label.set_fontsize(10)
        self.refresh_btn.on_clicked(self.manual_refresh)
        
        # Auto-refresh toggle
        ax_auto = plt.axes([0.90, 0.92, 0.08, 0.04])
        self.auto_btn = Button(ax_auto, 'Auto: ON', color='green', hovercolor='red')
        self.auto_btn.label.set_fontsize(10)
        self.auto_btn.on_clicked(self.toggle_auto_refresh)
        
        # Custom ticker input (initially hidden)
        self.custom_ticker_input = None
        
    def change_ticker(self, ticker):
        """Change the ticker symbol"""
        if ticker == 'CUSTOM':
            # Show input dialog
            custom = input("\nEnter custom ticker symbol: ").upper()
            if custom:
                self.ticker = custom
                print(f"Changed ticker to: {self.ticker}")
        else:
            self.ticker = ticker
            print(f"Changed ticker to: {self.ticker}")
        
        self.manual_refresh(None)
    
    def change_expiration(self, exp_type):
        """Change expiration type"""
        self.expiration_type = exp_type
        print(f"Changed expiration to: {self.expiration_type}")
        self.manual_refresh(None)
    
    def toggle_auto_refresh(self, event):
        """Toggle auto-refresh on/off"""
        self.auto_refresh = not self.auto_refresh
        status = "ON" if self.auto_refresh else "OFF"
        self.auto_btn.label.set_text(f'Auto: {status}')
        self.auto_btn.color = 'green' if self.auto_refresh else 'gray'
        print(f"Auto-refresh: {status}")
        plt.draw()
    
    def manual_refresh(self, event):
        """Manually trigger data refresh"""
        print("\n[Manual Refresh Triggered]")
        self.update(0)
        
    def get_quote(self):
        """Get current stock price"""
        url = f"{self.base_url}/markets/quotes"
        params = {'symbols': self.ticker}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        quote = data['quotes']['quote']
        return quote.get('last') or quote.get('close')
    
    def get_expirations(self):
        """Get available option expirations"""
        url = f"{self.base_url}/markets/options/expirations"
        params = {'symbol': self.ticker}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data['expirations']['date']
    
    def select_expiration(self, expirations):
        """Select appropriate expiration based on type"""
        today = datetime.now().date()
        
        exp_dates = [datetime.strptime(exp, '%Y-%m-%d').date() for exp in expirations]
        
        if self.expiration_type == '0DTE':
            for exp in exp_dates:
                if exp == today:
                    return exp.strftime('%Y-%m-%d')
            return expirations[0]
        
        elif self.expiration_type == '1DTE':
            tomorrow = today + timedelta(days=1)
            for exp in exp_dates:
                if exp == tomorrow:
                    return exp.strftime('%Y-%m-%d')
            return expirations[0]
        
        elif self.expiration_type == 'Weekly':
            week_out = today + timedelta(days=7)
            for exp in exp_dates:
                if today < exp <= week_out:
                    return exp.strftime('%Y-%m-%d')
            return expirations[0]
        
        else:  # Monthly
            month_out = today + timedelta(days=20)
            for exp in exp_dates:
                if exp > month_out:
                    return exp.strftime('%Y-%m-%d')
            return expirations[-1]
    
    def get_options_chain(self, expiration):
        """Get options chain with Greeks"""
        url = f"{self.base_url}/markets/options/chains"
        params = {
            'symbol': self.ticker,
            'expiration': expiration,
            'greeks': 'true'
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data['options']['option']
    
    def calculate_gex(self, options, current_price):
        """Calculate Gamma Exposure for each strike"""
        gex_by_strike = {}
        
        for option in options:
            if not option.get('greeks') or not option['greeks'].get('gamma'):
                continue
            
            strike = option['strike']
            gamma = option['greeks']['gamma']
            oi = option.get('open_interest', 0)
            opt_type = option['option_type']
            
            if oi == 0:
                continue
            
            # GEX = Gamma × OI × 100 × Spot² (in billions)
            multiplier = 1 if opt_type == 'call' else -1
            gex = gamma * oi * 100 * current_price * current_price / 1e9 * multiplier
            
            if strike in gex_by_strike:
                gex_by_strike[strike] += gex
            else:
                gex_by_strike[strike] = gex
        
        return gex_by_strike
    
    def generate_recommendation(self, gex_data, current_price):
        """Generate detailed trading recommendations"""
        if self.ticker != 'SPX' or self.expiration_type != '0DTE':
            return None
        
        df = pd.DataFrame(list(gex_data.items()), columns=['strike', 'gex'])
        df = df.sort_values('strike')
        
        positive_gex = df[df['gex'] > 0].sort_values('gex', ascending=False)
        negative_gex = df[df['gex'] < 0].sort_values('gex')
        total_gex = df['gex'].sum()
        
        recommendation = {
            'total_gex': total_gex,
            'sentiment': 'Strongly Stabilizing' if total_gex > 5 else 
                        'Stabilizing' if total_gex > 0 else 
                        'Neutral' if total_gex > -5 else 'High Volatility',
            'positive_gex': df[df['gex'] > 0]['gex'].sum(),
            'negative_gex': df[df['gex'] < 0]['gex'].sum()
        }
        
        if len(positive_gex) > 0:
            support = positive_gex.iloc[0]['strike']
            recommendation['support'] = support
            support_distance = abs(current_price - support) / current_price * 100
            
            # Find nearest round strikes
            round_strike = round(support / 5) * 5
            
            if current_price > support:
                if total_gex > 5:
                    short_strike = round_strike
                    long_strike = short_strike - 10
                    recommendation['strategy'] = 'Bull Put Credit Spread'
                    recommendation['trade'] = f"Sell ${int(short_strike)} Put / Buy ${int(long_strike)} Put"
                    recommendation['rationale'] = f"Strong positive GEX wall at ${int(support)} ({support_distance:.2f}% below current). Target credit: $2.00-$3.00 (20-30% of width). Max loss: ~$7-8 per spread. High probability as MM will defend this level."
                    recommendation['risk'] = 'Low-Medium'
                    recommendation['win_prob'] = '65-75%'
                elif total_gex > -5:
                    put_short = round((current_price - 15) / 5) * 5
                    put_long = put_short - 10
                    call_short = round((current_price + 15) / 5) * 5
                    call_long = call_short + 10
                    recommendation['strategy'] = 'Iron Condor'
                    recommendation['trade'] = f"Sell ${int(put_short)}P/${int(call_short)}C, Buy ${int(put_long)}P/${int(call_long)}C"
                    recommendation['rationale'] = f"Balanced GEX. Deploy IC outside high gamma zones. Target credit: $3.50-4.50 total."
                    recommendation['risk'] = 'Medium'
                    recommendation['win_prob'] = '60-70%'
                else:
                    recommendation['strategy'] = 'CAUTION: High Volatility Environment'
                    recommendation['trade'] = 'Use 30+ point wings OR avoid trading'
                    recommendation['rationale'] = f"⚠️ Negative net GEX (${total_gex:.2f}B) = HIGH RISK. MM will amplify moves. Expected range: 1-2% intraday. Consider calendar spreads or stay out."
                    recommendation['risk'] = 'HIGH'
                    recommendation['win_prob'] = '40-50%'
            else:
                call_short = round_strike - 5
                call_long = call_short + 10
                recommendation['strategy'] = 'Bear Call Credit Spread'
                recommendation['trade'] = f"Sell ${int(call_short)} Call / Buy ${int(call_long)} Call"
                recommendation['rationale'] = f"Price below GEX resistance at ${int(support)}. Heavy gamma acts as ceiling. Target: $2.00-2.50 credit."
                recommendation['risk'] = 'Medium'
                recommendation['win_prob'] = '60-65%'
        
        if len(negative_gex) > 0:
            recommendation['resistance'] = negative_gex.iloc[0]['strike']
        
        # Timing guidance
        current_hour = datetime.now().hour
        current_min = datetime.now().minute
        
        if current_hour < 10:
            recommendation['timing'] = '⏰ PRE-MARKET: Wait until 10:00 AM EST for volatility to settle'
            recommendation['action'] = 'WAIT'
        elif current_hour == 10 and current_min < 30:
            recommendation['timing'] = '✅ OPTIMAL ENTRY WINDOW (10:00-10:30 AM EST)'
            recommendation['action'] = 'ENTER'
        elif current_hour < 14:
            recommendation['timing'] = '✅ Good entry window - Mid-day session'
            recommendation['action'] = 'ENTER'
        elif current_hour < 15:
            recommendation['timing'] = '⚠️ Afternoon - Gamma pin effects intensifying'
            recommendation['action'] = 'MONITOR'
        elif current_hour < 16:
            recommendation['timing'] = '🔴 LATE SESSION - High risk, avoid new entries'
            recommendation['action'] = 'CLOSE/AVOID'
        else:
            recommendation['timing'] = '🔒 MARKET CLOSED - Plan for next session'
            recommendation['action'] = 'CLOSED'
        
        return recommendation
    
    def draw_stats_panel(self, stats):
        """Draw statistics panel"""
        self.ax_stats.clear()
        self.ax_stats.axis('off')
        
        stats_text = f"""
LIVE MARKET DATA - {self.ticker} | {self.expiration_type} Expiration: {self.current_expiration}
────────────────────────────────────────────────────────────────────────────────────────────────
Current Price: ${self.current_price:.2f}  │  Total GEX: ${stats['total_gex']:.2f}B  │  Positive GEX: ${stats['positive_gex']:.2f}B  │  Negative GEX: ${stats['negative_gex']:.2f}B
Last Update: {self.last_update.strftime('%Y-%m-%d %H:%M:%S')} EST  │  Auto-refresh: {'ON' if self.auto_refresh else 'OFF'} (60s)  │  Data Source: Tradier API
"""
        
        self.ax_stats.text(0.02, 0.5, stats_text, transform=self.ax_stats.transAxes,
                          fontsize=9, verticalalignment='center', family='monospace',
                          bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
    
    def draw_recommendation_panel(self, rec):
        """Draw trading recommendation panel"""
        self.ax_recommendation.clear()
        self.ax_recommendation.axis('off')
        
        if not rec:
            info_text = f"""
SELECT SPX + 0DTE
FOR TRADING
RECOMMENDATIONS

Current: {self.ticker}
Expiration: {self.expiration_type}
"""
            self.ax_recommendation.text(0.1, 0.5, info_text, transform=self.ax_recommendation.transAxes,
                                      fontsize=10, verticalalignment='center', family='monospace',
                                      bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
            return
        
        # Color based on risk
        risk_colors = {
            'Low-Medium': 'lightgreen',
            'Medium': 'lightyellow',
            'Medium-High': 'orange',
            'HIGH': 'lightcoral'
        }
        
        bg_color = risk_colors.get(rec['risk'], 'lightgray')
        
        rec_text = f"""
SPX 0DTE STRATEGY
═══════════════════
{rec['strategy']}

TRADE:
{rec.get('trade', 'N/A')}

RISK: {rec['risk']}
Win Prob: {rec.get('win_prob', 'N/A')}

SENTIMENT:
{rec['sentiment']}
(${rec['total_gex']:.2f}B)

TIMING:
{rec['timing']}
→ {rec['action']}

KEY LEVELS:
Support: ${int(rec.get('support', 0))}
{f"Resist: ${int(rec.get('resistance', 0))}" if 'resistance' in rec else ''}

⚠️ Not financial advice
   Trade at own risk
"""
        
        self.ax_recommendation.text(0.05, 0.95, rec_text, transform=self.ax_recommendation.transAxes,
                                   fontsize=8, verticalalignment='top', family='monospace',
                                   bbox=dict(boxstyle='round', facecolor=bg_color, alpha=0.7))
    
    def update(self, frame):
        """Update function for animation"""
        try:
            print(f"\n{'='*70}")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching {self.ticker} data...")
            
            # Get current price
            self.current_price = self.get_quote()
            print(f"✓ Current Price: ${self.current_price:.2f}")
            
            # Get expirations
            expirations = self.get_expirations()
            self.current_expiration = self.select_expiration(expirations)
            print(f"✓ Expiration: {self.current_expiration} ({self.expiration_type})")
            
            # Get options chain
            options = self.get_options_chain(self.current_expiration)
            print(f"✓ Loaded {len(options)} options contracts")
            
            # Calculate GEX
            gex_data = self.calculate_gex(options, self.current_price)
            
            if not gex_data:
                print("✗ No GEX data available")
                return
            
            # Filter strikes
            price_range = self.current_price * 0.10
            filtered_gex = {k: v for k, v in gex_data.items() 
                          if self.current_price - price_range <= k <= self.current_price + price_range}
            
            df = pd.DataFrame(list(filtered_gex.items()), columns=['strike', 'gex'])
            df = df.sort_values('strike')
            
            # Calculate stats
            total_gex = df['gex'].sum()
            pos_gex = df[df['gex'] > 0]['gex'].sum()
            neg_gex = df[df['gex'] < 0]['gex'].sum()
            
            stats = {
                'total_gex': total_gex,
                'positive_gex': pos_gex,
                'negative_gex': neg_gex
            }
            
            print(f"✓ Total GEX: ${total_gex:.2f}B (Pos: ${pos_gex:.2f}B, Neg: ${neg_gex:.2f}B)")
            
            self.last_update = datetime.now()
            
            # Draw stats panel
            self.draw_stats_panel(stats)
            
            # Clear and draw GEX chart
            self.ax_gex.clear()
            colors = ['green' if x >= 0 else 'red' for x in df['gex']]
            bars = self.ax_gex.bar(df['strike'], df['gex'], color=colors, alpha=0.7, width=2)
            self.ax_gex.axvline(self.current_price, color='blue', linestyle='--', linewidth=2, 
                              label=f'Current: ${self.current_price:.2f}')
            self.ax_gex.axhline(0, color='black', linestyle='-', linewidth=0.5)
            self.ax_gex.set_xlabel('Strike Price', fontsize=11, fontweight='bold')
            self.ax_gex.set_ylabel('GEX (Billions $)', fontsize=11, fontweight='bold')
            self.ax_gex.set_title(f'Gamma Exposure by Strike', fontsize=12, fontweight='bold')
            self.ax_gex.legend(loc='upper right')
            self.ax_gex.grid(True, alpha=0.3)
            
            # Cumulative GEX
            self.ax_cumulative.clear()
            df['cumulative'] = df['gex'].cumsum()
            self.ax_cumulative.plot(df['strike'], df['cumulative'], color='purple', linewidth=2.5)
            self.ax_cumulative.axvline(self.current_price, color='blue', linestyle='--', linewidth=2)
            self.ax_cumulative.axhline(0, color='black', linestyle='-', linewidth=0.5)
            self.ax_cumulative.fill_between(df['strike'], df['cumulative'], alpha=0.3, color='purple')
            self.ax_cumulative.set_xlabel('Strike Price', fontsize=11, fontweight='bold')
            self.ax_cumulative.set_ylabel('Cumulative GEX (Billions $)', fontsize=11, fontweight='bold')
            self.ax_cumulative.set_title('Cumulative Gamma Exposure', fontsize=12, fontweight='bold')
            self.ax_cumulative.grid(True, alpha=0.3)
            
            # Generate and draw recommendation
            recommendation = self.generate_recommendation(filtered_gex, self.current_price)
            self.draw_recommendation_panel(recommendation)
            
            if recommendation:
                print(f"✓ Strategy: {recommendation['strategy']}")
                print(f"  Risk: {recommendation['risk']} | Action: {recommendation['action']}")
            
            plt.draw()
            
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """Run the live dashboard"""
        print(f"\n{'='*70}")
        print("TRADIER GEX DASHBOARD - STARTED")
        print(f"{'='*70}")
        print(f"Initial Ticker: {self.ticker}")
        print(f"Initial Expiration: {self.expiration_type}")
        print(f"Auto-refresh: {'ON' if self.auto_refresh else 'OFF'} (60 seconds)")
        print(f"\nControls:")
        print(f"  • Click ticker buttons (SPX, SPY, QQQ, etc.) to change symbol")
        print(f"  • Click expiration buttons (0DTE, 1DTE, etc.) to change expiration")
        print(f"  • Click 'Refresh Now' for manual update")
        print(f"  • Click 'Auto: ON/OFF' to toggle auto-refresh")
        print(f"  • Close window to exit")
        print(f"{'='*70}\n")
        
        # Initial load
        self.update(0)
        
        # Setup animation
        def animate_wrapper(frame):
            if self.auto_refresh:
                self.update(frame)
        
        anim = FuncAnimation(self.fig, animate_wrapper, interval=self.update_interval, 
                           cache_frame_data=False)
        
        plt.show()


if __name__ == "__main__":
    # ============================================
    # CONFIGURATION
    # ============================================
    
    # Enter your Tradier API key here
    API_KEY = "Clty9DpKMudoRXfh9vYKee9A09r0"
    
    # ============================================
    
    if API_KEY == "YOUR_TRADIER_API_KEY_HERE":
        print("\n" + "="*70)
        print("ERROR: Please configure your Tradier API key!")
        print("="*70)
        print("\n1. Get your FREE API key at: https://developer.tradier.com")
        print("2. Open this Python file in a text editor")
        print("3. Replace 'YOUR_TRADIER_API_KEY_HERE' with your actual key")
        print("4. Save and run again\n")
        exit(1)
    
    # Create and run analyzer
    analyzer = TradierGEXAnalyzer(api_key=API_KEY)
    analyzer.run()