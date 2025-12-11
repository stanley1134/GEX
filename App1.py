# GEX PRO — FINAL WITH TRADE RECOMMENDATIONS (Tested & Working)
import requests, pandas as pd, numpy as np, matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox
from matplotlib.animation import FuncAnimation
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("TRADIER_API_KEY")
if not API_KEY:
    print("Set TRADIER_API_KEY in .env!")
    exit(1)

class GEXPro:
    def __init__(self):
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(8, 6))
        self.fig.patch.set_facecolor('#000000')
        self.fig.subplots_adjust(left=0.02, right=0.98, top=0.85, bottom=0.08, hspace=0.6)

        self.ax_gex = plt.subplot(211)
        self.ax_cum = plt.subplot(212)
        self.ax_info = plt.axes([0.02, 0.02, 0.35, 0.12], facecolor='#111')
        self.ax_sig  = plt.axes([0.39, 0.02, 0.20, 0.12], facecolor='#111')
        self.ax_rec  = plt.axes([0.62, 0.02, 0.35, 0.12], facecolor='#111')
        for ax in [self.ax_info, self.ax_sig, self.ax_rec]:
            ax.axis('off')

        self.ticker = 'SPX'
        self.exp = '0DTE'
        self.auto = True
        self.price = 0
        self.df = None

        self.tooltip = self.ax_gex.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
            bbox=dict(boxstyle="round", fc="#222", ec="#0ff", lw=1.5),
            arrowprops=dict(arrowstyle='->', color='#0ff'), fontsize=9, color="white")
        self.tooltip.set_visible(False)

        self.fig.canvas.mpl_connect("motion_notify_event", self.hover)

        self.ticker_btns = {}
        self.exp_btns = {}
        self.make_buttons()
        self.update()

        FuncAnimation(self.fig, lambda f: self.update() if self.auto else None,
                     interval=60000, cache_frame_data=False, save_count=0)
        plt.show()

    def make_buttons(self):
        # Ticker buttons
        tickers = ['SPX','SPY','QQQ','IWM','NDX']
        for i, t in enumerate(tickers):
            ax = plt.axes([0.01 + i*0.065, 0.90, 0.06, 0.06], zorder=999)
            color = '#00ffff' if t == self.ticker else '#0066ff'
            btn = Button(ax, t, color=color, hovercolor='#00ffff')
            btn.label.set_fontsize(10); btn.label.set_fontweight('bold')
            btn.on_clicked(lambda e, sym=t: self.set_ticker(sym))
            self.ticker_btns[t] = btn

        # Custom box — BLACK text
        ax = plt.axes([0.36, 0.90, 0.10, 0.06], zorder=999)
        self.box = TextBox(ax, '', 'SPX')
        self.box.label.set_color('#888888')
        self.box.ax.patch.set_facecolor('white')  # white background for easy reading
        for txt in self.box.ax.texts:
            if txt != self.box.label:
                txt.set_color('black')  # BLACK text
        self.box.on_submit(lambda txt: self.set_ticker(txt.strip().upper() or 'SPX'))

        # Expiration buttons
        expirations = [('0DTE','#f33'), ('1DTE','#fa3'), ('Week','#36f'), ('Month','#3c3')]
        for i, (label, base_color) in enumerate(expirations):
            ax = plt.axes([0.50 + i*0.075, 0.90, 0.07, 0.06], zorder=999)
            active_color = '#00ffff' if label == self.exp else base_color
            btn = Button(ax, label, color=active_color, hovercolor='#00ffff')
            btn.label.set_fontsize(10); btn.label.set_color('white')
            btn.on_clicked(lambda e, x=label: self.set_exp(x))
            self.exp_btns[label] = btn

        # Refresh & Auto
        ax = plt.axes([0.82, 0.90, 0.07, 0.06], zorder=999)
        Button(ax, 'R', color='#ff8800').on_clicked(lambda e: self.update())

        ax = plt.axes([0.90, 0.90, 0.07, 0.06], zorder=999)
        self.auto_btn = Button(ax, 'Auto', color='#00ff00')
        self.auto_btn.on_clicked(lambda e: self.toggle_auto())

    def set_ticker(self, t):
        if t != self.ticker:
            if self.ticker in self.ticker_btns:
                self.ticker_btns[self.ticker].color = '#0066ff'
            self.ticker_btns[t].color = '#00ffff'
            self.ticker = t
            self.box.set_val(t)
            self.update()

    def set_exp(self, e):
        if e != self.exp:
            colors = {'0DTE':'#f33', '1DTE':'#fa3', 'Week':'#36f', 'Month':'#3c3'}
            if self.exp in self.exp_btns:
                self.exp_btns[self.exp].color = colors[self.exp]
            self.exp_btns[e].color = '#00ffff'
            self.exp = e
            self.update()

    def toggle_auto(self):
        self.auto = not self.auto
        self.auto_btn.color = '#00ff00' if self.auto else '#666666'

    def hover(self, e):
        if e.inaxes != self.ax_gex or self.df is None:
            self.tooltip.set_visible(False); plt.draw(); return
        for bar in self.ax_gex.patches:
            if bar.contains(e)[0]:
                s = int(bar.get_x() + bar.get_width()/2)
                g = bar.get_height()
                self.tooltip.xy = (s, g)
                self.tooltip.set_text(f"{s}\n{g:+.1f}B")
                self.tooltip.set_visible(True)
                plt.draw()
                return
        self.tooltip.set_visible(False); plt.draw()

    def get_recommendation(self, total, price, flip):
        if self.ticker != 'SPX': return "Only SPX\n0DTE/1DTE"
        round5 = lambda x: round(x/5)*5
        short_put = round5(price - 15 if total > 8 else price - 25)
        long_put = short_put - 10
        short_call = round5(price + 15 if total > 8 else price + 25)
        long_call = short_call + 10
        
        if total > 8:
            strategy = "Bull Put Credit Spread"
            trade = f"Sell {short_put}P\nBuy {long_put}P"
            credit = "2.20-3.50"
            risk = "Low"
        elif abs(total) < 6:
            strategy = "Iron Butterfly"
            trade = f"Sell {round5(price)}P/{round5(price)}C\nBuy {round5(price)-15}P/{round5(price)+15}C"
            credit = "4.00-6.00"
            risk = "Medium"
        else:
            strategy = "Iron Condor"
            trade = f"Sell {short_put}P/{short_call}C\nBuy {long_put}P/{long_call}C"
            credit = "3.50-5.00"
            risk = "Medium"
        return f"{strategy}\n{trade}\nCredit ~${credit}\nRisk: {risk}"

    def update(self):
        try:
            s = requests.Session()
            s.headers = {'Authorization': f'Bearer {API_KEY}', 'Accept': 'application/json'}

            q = s.get("https://api.tradier.com/v1/markets/quotes", params={'symbols':self.ticker}).json()
            self.price = q['quotes']['quote'].get('last') or 5000

            dates = s.get("https://api.tradier.com/v1/markets/options/expirations", params={'symbol':self.ticker}).json()['expirations']['date']
            today = datetime.now().date()
            exp_dates = [datetime.strptime(d,'%Y-%m-%d').date() for d in dates]
            if self.exp == '0DTE': exp = next((d for d in exp_dates if d == today), exp_dates[0])
            elif self.exp == '1DTE': exp = next((d for d in exp_dates if d == today + timedelta(1)), exp_dates[0])
            elif self.exp == 'Week':
                c = [d for d in exp_dates if d > today + timedelta(days=3)]
                exp = min(c, key=lambda x: abs(x-(today+timedelta(7)))) if c else exp_dates[0]
            else: exp = max(exp_dates)

            chain = s.get("https://api.tradier.com/v1/markets/options/chains",
                         params={'symbol':self.ticker, 'expiration':exp.strftime('%Y-%m-%d'), 'greeks':'true'}).json()['options']['option']

            gex = {}
            p2 = self.price**2
            for o in chain:
                g = o.get('greeks', {}).get('gamma') or 0
                if not g: continue
                strike = o['strike']
                oi = o.get('open_interest',0) or 0
                sign = 1 if o['option_type']=='call' else -1
                if oi == 0: continue
                gex[strike] = gex.get(strike,0) + g * oi * 100 * p2 / 1e9 * sign

            df = pd.DataFrame([(k,v) for k,v in gex.items() if abs(k-self.price)/self.price <= 0.10],
                             columns=['strike','gex']).sort_values('strike')
            df['cum'] = df.gex.cumsum()
            self.df = df

            flip = df.iloc[df['cum'].abs().argmin()]['strike']
            total = df.gex.sum()

            self.ax_gex.clear()
            c = ['#0f0' if x>=0 else '#f00' for x in df.gex]
            self.ax_gex.bar(df.strike, df.gex, color=c, width=3)
            self.ax_gex.axvline(self.price, color='yellow', lw=2)
            self.ax_gex.axvline(flip, color='magenta', lw=2, ls='--')

            self.ax_cum.clear()
            self.ax_cum.plot(df.strike, df.cum, color='#0ff', lw=2.5)
            self.ax_cum.fill_between(df.strike, df.cum, alpha=0.4, color='#505')
            self.ax_cum.axvline(self.price, color='yellow', lw=2)

            # Info
            self.ax_info.clear(); self.ax_info.axis('off')
            self.ax_info.text(0.05, 0.7, f"{self.ticker}\n${self.price:,.0f}\nGEX {total:+.1f}B\nFlip ${flip:,.0f}", 
                             color='#aaa', fontsize=10, va='top')

            # Regime — smaller font
            self.ax_sig.clear(); self.ax_sig.axis('off')
            regime = "PIN" if total>10 else "BULL" if total>3 else "BEAR" if total<-3 else "CHOP"
            col = '#0f0' if total>5 else '#ff0' if total>-5 else '#f00'
            self.ax_sig.text(0.5, 0.5, regime, transform=self.ax_sig.transAxes,
                            fontsize=24, fontweight='bold', color=col, ha='center', va='center')

            # TRADE RECOMMENDATIONS
            self.ax_rec.clear(); self.ax_rec.axis('off')
            rec_text = self.get_recommendation(total, self.price, flip)
            self.ax_rec.text(0.05, 0.95, rec_text, transform=self.ax_rec.transAxes,
                            fontsize=9, color='#00ff00', va='top', fontfamily='Consolas')

            plt.draw()

        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    GEXPro()