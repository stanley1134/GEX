# GEX PRO — FINAL, 0DTE/1DTE NOW SHOW CORRECT SHORT-TERM EXP (Dec 2025)
# Fixed for days without daily expirations (e.g., Monday → next available, usually Wednesday)

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("TRADIER_API_KEY")
if not API_KEY:
    print("ERROR: Set TRADIER_API_KEY in .env!")
    exit(1)

app = dash.Dash(__name__, title="GEX PRO")
app.css.append_css({"external_url": "https://cdn.jsdelivr.net/npm/bootswatch@5.3.0/dist/darkly/bootstrap.min.css"})

# PERFECT DARK DROPDOWNS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .Select-control { background-color: #111 !important; border: 2px solid #0ff !important; color: white !important; }
            .Select-placeholder, .Select--single > .Select-control .Select-value { color: #0ff !important; }
            .Select-input > input { color: white !important; background: transparent !important; }
            .Select-menu-outer, .Select-menu { background-color: #111 !important; border: 2px solid #0ff !important; }
            .Select-option { background-color: #111 !important; color: white !important; }
            .Select-option.is-focused { background-color: #0ff !important; color: black !important; }
            .Select-noresults { color: #aaa !important; }
            .Select-arrow { border-top-color: #0ff !important; }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

POPULAR_TICKERS = ['SPX','SPY','QQQ','IWM','NDX','AAPL','NVDA','TSLA','AMD','META','MSFT','GOOGL','AMZN','COIN','SMCI']

app.layout = html.Div(style={'backgroundColor':'#000','color':'#ccc','fontFamily':'Consolas','padding':'20px'}, children=[
    html.H1("GEX PRO — Real-Time Gamma Exposure", style={'textAlign':'center','color':'#0ff','marginBottom':'10px'}),
    html.H5("0DTE/1DTE Fixed • Short-term expirations now correct", style={'textAlign':'center','color':'#0af','marginBottom':'30px'}),

    html.Div([
        html.Div([
            html.Label("Ticker", style={'color':'#0ff','fontWeight':'bold','fontSize':'18px'}),
            dcc.Dropdown(options=[{'label':t,'value':t} for t in POPULAR_TICKERS], value='SPX', id='ticker', searchable=True, clearable=False, placeholder="SPX, NVDA...")
        ], style={'width':'38%','display':'inline-block','marginRight':'4%'}),

        html.Div([
            html.Label("Expiration", style={'color':'#0ff','fontWeight':'bold','fontSize':'18px'}),
            dcc.Dropdown(options=['0DTE','1DTE','Week','Month'], value='0DTE', id='exp', clearable=False)
        ], style={'width':'25%','display':'inline-block'}),

        html.Button("Refresh", id='refresh-btn', n_clicks=0,
                    style={'marginLeft':'30px','marginTop':'28px','backgroundColor':'#ff8800','color':'white','height':'50px','fontSize':'16px','borderRadius':'8px','fontWeight':'bold'})
    ], style={'textAlign':'center','marginBottom':'20px'}),

    dcc.Loading(dcc.Graph(id='gex-chart', style={'height':'460px','marginTop':'20px'}), type="circle", color="#0ff"),
    dcc.Loading(dcc.Graph(id='cum-chart', style={'height':'460px'}), type="circle", color="#0ff"),
    html.Div(id='info-panel', style={'textAlign':'center','margin':'40px'}),
    dcc.Interval(id='interval', interval=60*1000, n_intervals=0)
])

def get_gex_data(ticker, exp_mode):
    try:
        s = requests.Session()
        s.headers = {'Authorization': f'Bearer {API_KEY}', 'Accept': 'application/json'}
        ticker = ticker.upper()

        # Price
        quote = s.get("https://api.tradier.com/v1/markets/quotes", params={'symbols': ticker}).json()
        if not quote.get('quotes'): return None, "Invalid ticker", None, None, None
        price = quote['quotes']['quote'].get('last') or quote['quotes']['quote'].get('bid') or 5000

        # Expirations
        exp_resp = s.get("https://api.tradier.com/v1/markets/options/expirations", params={'symbol': ticker}).json()
        if not exp_resp.get('expirations'): return None, "No expirations", None, None, None
        dates = exp_resp['expirations']['date']
        exp_dates = sorted([datetime.strptime(d, '%Y-%m-%d').date() for d in dates])
        today = datetime.now().date()

        # FIXED SHORT-TERM LOGIC
        future_dates = [d for d in exp_dates if d >= today]
        if not future_dates:
            return None, "No future expirations", None, None, None

        if exp_mode in ['0DTE', '1DTE']:
            # Always pick the absolute closest future expiration for 0DTE/1DTE
            selected_exp = min(future_dates, key=lambda x: (x - today).days)
        elif exp_mode == 'Week':
            # Closest weekly (usually Friday)
            weekly_candidates = [d for d in future_dates if (d - today).days <= 14]
            selected_exp = min(weekly_candidates, key=lambda x: abs((x - today).days - 7)) if weekly_candidates else future_dates[0]
        else:  # Month
            selected_exp = max(d for d in future_dates if d.month == (today.month if today.day <= 15 else (today.month % 12 + 1)))

        print(f"{ticker} | {exp_mode} → {selected_exp} ({selected_exp.strftime('%A %b %d')})")

        # Chain
        chain = s.get("https://api.tradier.com/v1/markets/options/chains",
                     params={'symbol': ticker, 'expiration': selected_exp.strftime('%Y-%m-%d'), 'greeks': 'true'}).json()
        options = chain.get('options', {}).get('option', [])
        if not options: return None, "No chain", None, None, None

        gex = {}
        for o in options:
            gamma = o.get('greeks', {}).get('gamma') or 0
            oi = o.get('open_interest') or 0
            if gamma > 0 and oi > 0:
                sign = 1 if o['option_type'] == 'call' else -1
                gex[o['strike']] = gex.get(o['strike'], 0) + sign * gamma * oi * 100 * price / 10_000

        df = pd.DataFrame([(k,v) for k,v in gex.items() if abs(k-price)/price <= 0.15],
                         columns=['strike','gex']).sort_values('strike')
        if df.empty: return None, "No GEX", None, None, None

        df['cum'] = df.gex.cumsum()
        flip = df.iloc[df['cum'].abs().idxmin()]['strike']
        total = df.gex.sum()

        return df, price, flip, total, selected_exp
    except Exception as e:
        print("ERROR:", e)
        return None, f"Error: {e}", None, None, None

@app.callback(
    [Output('gex-chart','figure'), Output('cum-chart','figure'), Output('info-panel','children')],
    [Input('interval','n_intervals'), Input('ticker','value'), Input('exp','value'), Input('refresh-btn','n_clicks')]
)
def update_dashboard(n, ticker, exp_mode, clicks):
    df, price, flip, total, exp = get_gex_data(ticker, exp_mode)

    if df is None:
        error = price if isinstance(price, str) else "No data"
        return (
            go.Figure().update_layout(template='plotly_dark', title=error),
            go.Figure().update_layout(template='plotly_dark'),
            html.H2(error, style={'color':'#ff0066','textAlign':'center','fontSize':'40px'})
        )

    title = f"{ticker.upper()} • {exp.strftime('%b %d (%A)')} • GEX {total:+.2f}B"

    fig1 = go.Figure()
    fig1.add_bar(x=df.strike, y=df.gex,
                 marker_color=['#00ff88' if x >= 0 else '#ff4444' for x in df.gex])
    fig1.add_vline(x=price, line=dict(color='yellow', width=4))
    fig1.add_vline(x=flip, line=dict(color='magenta', width=4, dash='dash'))
    fig1.update_layout(title=title, template='plotly_dark', height=460)

    fig2 = go.Figure()
    fig2.add_scatter(x=df.strike, y=df.cum, line=dict(color='#00ffff', width=5))
    fig2.add_hline(y=0, line_color='#666')
    fig2.add_vline(x=price, line_color='yellow', line_width=4)
    fig2.update_layout(title="Cumulative GEX • Flip = Zero Crossing", template='plotly_dark', height=460)

    regime = ("STRONG BULL" if total > 18 else "BULL" if total > 8 else
              "STRONG BEAR" if total < -18 else "BEAR" if total < -8 else "CHOP")
    regime_color = '#00ff00' if 'BULL' in regime else '#ff0066' if 'BEAR' in regime else '#ffff00'

    atm = round(price / 5) * 5
    wing = 20 if abs(total) > 15 else 35
    if total > 18: trade = f"SHORT PUT SPREAD\nSell {atm-10}P   Buy {atm-10-wing}P"
    elif total > 8: trade = f"PUT CREDIT\nSell {atm-15}P   Buy {atm-15-wing}P"
    elif total < -8: trade = f"CALL CREDIT\nSell {atm+15}C   Buy {atm+15+wing}C"
    else: trade = f"IRON CONDOR\nSell {atm-20}P/{atm+20}C\nBuy wings {wing} out"

    info = html.Div([
        html.H1(regime, style={'color':regime_color,'margin':'20px','fontSize':'70px'}),
        html.Div(f"Price ${price:,.0f} • Flip ${flip:,.0f} • GEX {total:+.2f}B", style={'fontSize':'26px'}),
        html.H3("Trade Idea", style={'color':'#00ffaa','marginTop':'30px'}),
        html.Pre(trade, style={'background':'#111','padding':'30px','borderRadius':'15px',
                               'fontSize':'28px','border':'3px solid #0ff'})
    ], style={'textAlign':'center'})

    return fig1, fig2, info

if __name__ == '__main__':
    print("GEX PRO — 0DTE/1DTE FIXED (uses closest short-term exp) — STARTING!")
    print("Open → http://127.0.0.1:8050")
    app.run(debug=False)