from flask import Flask, render_template, jsonify, request

# ... imports ...
import requests
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
API_KEY = os.getenv("TRADIER_API_KEY")

if not API_KEY:
    API_KEY = "Clty9DpKMudoRXfh9vYKee9A09r0"

# ... (lines 1-20 unchanged) ...

# --- GEX Logic ---

# --- GEX Logic ---

app = Flask(__name__)

# --- GEX Logic ---
# --- GEX Logic ---
def get_gex_data_json(ticker='SPX', target_date=None):
    print(f"--- Fetching GEX Data for {ticker} (Target: {target_date}) ---")
    base_url = "https://api.tradier.com/v1"
    headers = {'Authorization': f'Bearer {API_KEY}', 'Accept': 'application/json'}
    
    print(f"API Key (first 4): {API_KEY[:4]}...")
    
    # Get Price
    try:
        r = requests.get(f"{base_url}/markets/quotes", params={'symbols': ticker}, headers=headers)
        if r.status_code != 200:
            print(f"Error fetching price: Status {r.status_code} - {r.text}")
            return None
        price = r.json()['quotes']['quote']['last']
        print(f"Price: {price}")
    except Exception as e:
        print(f"Exception fetching price: {e}")
        return None
        
    # Get Expiration
    try:
        r = requests.get(f"{base_url}/markets/options/expirations", 
                        params={'symbol': ticker, 'includeAllRoots': 'true'}, 
                        headers=headers)
        dates = r.json()['expirations']['date']
        today = datetime.now().date().strftime('%Y-%m-%d')
        
        # Validate and Fallback Expiry
        # Ensure dates are sorted for fallback logic
        dates.sort()
        
        if target_date and target_date in dates:
            expiry = target_date
            print(f"Using requested expiry: {expiry}")
        else:
            expiry = today if today in dates else next((d for d in dates if d >= today), dates[0] if dates else None)
            if target_date:
                print(f"Requested date {target_date} invalid/not found. Defaulting to {expiry}")
            else:
                print(f"Using default expiry: {expiry} (Today: {today})")
    except Exception as e:
        print(f"Exception fetching expirations: {e}")
        return None

    if not expiry:
        print("No valid expiration found.")
        return None

    # Get Chain
    try:
        print(f"Fetching chain for {expiry}...")
        r = requests.get(f"{base_url}/markets/options/chains", 
                        params={'symbol': ticker, 'expiration': expiry, 'greeks': 'true'}, 
                        headers=headers)
        data = r.json()
        if 'options' not in data or 'option' not in data['options']:
            print("No options in response.")
            return None
        options = data['options']['option']
        print(f"Options count: {len(options)}")
    except Exception as e:
        print(f"Exception fetching chain: {e}")
        return None

    # Calculate GEX, OI, Volume
    gex = {}
    oi_dict = {}
    vol_dict = {}
    
    for o in options:
        if not o.get('greeks') or not o['greeks'].get('gamma'): continue
        
        strike = o['strike']
        
        # Accumulate GEX (Net)
        if o.get('open_interest', 0) > 0:
            eff = 1 if o['option_type'] == 'call' else -1
            val = (o['greeks']['gamma'] * o['open_interest'] * 100 * (price**2) * eff) / 1e9
            gex[strike] = gex.get(strike, 0) + val

        # Accumulate OI and Volume (Total)
        oi_dict[strike] = oi_dict.get(strike, 0) + o.get('open_interest', 0)
        vol_dict[strike] = vol_dict.get(strike, 0) + o.get('volume', 0)
        
    # Filter for frontend
    range_pct = 0.02 # Tighter range for web view clarity
    filtered_strikes = [k for k in gex.keys() if price*(1-range_pct) <= k <= price*(1+range_pct)]
    filtered_strikes.sort()
    
    chart_labels = filtered_strikes
    chart_data = [gex[k] for k in filtered_strikes]
    chart_oi = [oi_dict.get(k, 0) for k in filtered_strikes]
    chart_vol = [vol_dict.get(k, 0) for k in filtered_strikes] # volume can be 0 or None
    
    print(f"Filtered strikes: {len(filtered_strikes)}")
    
    # Walls
    df = pd.DataFrame(list(gex.items()), columns=['strike', 'gex'])
    try:
        if not df.empty:
            call_wall = float(df[df['gex'] > 0].sort_values('gex', ascending=False).iloc[0]['strike']) if not df[df['gex'] > 0].empty else None
            put_wall = float(df[df['gex'] < 0].sort_values('gex', ascending=True).iloc[0]['strike']) if not df[df['gex'] < 0].empty else None
        else:
            call_wall, put_wall = None, None
    except Exception as e:
        print(f"Error calculating walls: {e}")
        call_wall, put_wall = None, None
        
    # --- MAX OI ---
    max_oi_strike = None
    try:
        # We need to re-iterate options or store them to find Max OI
        # Simplified: find max OI from the options list we already have
        if options:
            # Aggregate OI by strike (summing calls + puts)
            oi_by_strike = {}
            for o in options:
                s = o['strike']
                oi = o.get('open_interest', 0)
                oi_by_strike[s] = oi_by_strike.get(s, 0) + oi
            
            if oi_by_strike:
                max_oi_strike = max(oi_by_strike, key=oi_by_strike.get)
    except Exception as e:
        print(f"Error calculating Max OI: {e}")

    # --- STRATEGY GENERATION ---
    strategy = {
        'name': 'Analyzing...',
        'legs': [],
        'rationale': 'Insufficient data'
    }
    
    total_gex = df['gex'].sum() if not df.empty else 0
    
    # helper for round strikes
    # helper for round strikes
    def round_strike(p):
        if p < 200: return round(p)
        return round(p / 5) * 5
    
    try:
        # Create lookup map for fast access
        opt_map = {}
        for o in options:
            opt_map[(o['strike'], o['option_type'])] = o

        def get_leg_data(strike, otype):
            return opt_map.get((strike, otype))

        if total_gex > 3: # Bullish
            p_target = put_wall if put_wall and put_wall < price else price - 5
            short_strike = round_strike(p_target)
            long_strike = short_strike - 10
            
            # Get Data
            short_opt = get_leg_data(short_strike, 'put')
            long_opt = get_leg_data(long_strike, 'put')
            
            credit = 0
            pop = 0
            if short_opt and long_opt:
                credit = (short_opt.get('bid', 0) - long_opt.get('ask', 0))
                short_delta = short_opt.get('greeks', {}).get('delta', -0.5)
                pop = 1 - abs(short_delta)

            strategy = {
                'name': 'Bull Put Spread',
                'legs': [f"SELL {int(short_strike)} PUT", f"BUY {int(long_strike)} PUT"],
                'rationale': f'Positive GEX (${total_gex:.2f}B). Put Wall Support at {int(put_wall) if put_wall else "N/A"}.',
                'premium': round(credit, 2),
                'pop': round(pop * 100, 1)
            }

        elif total_gex < -3: # Bearish
            c_target = call_wall if call_wall and call_wall > price else price + 5
            short_strike = round_strike(c_target)
            long_strike = short_strike + 10
            
            short_opt = get_leg_data(short_strike, 'call')
            long_opt = get_leg_data(long_strike, 'call')
            
            credit = 0
            pop = 0
            if short_opt and long_opt:
                credit = (short_opt.get('bid', 0) - long_opt.get('ask', 0))
                short_delta = short_opt.get('greeks', {}).get('delta', 0.5)
                pop = 1 - abs(short_delta)

            strategy = {
                'name': 'Bear Call Spread',
                'legs': [f"SELL {int(short_strike)} CALL", f"BUY {int(long_strike)} CALL"],
                'rationale': f'Negative GEX (${total_gex:.2f}B). Call Wall Resistance at {int(call_wall) if call_wall else "N/A"}.',
                'premium': round(credit, 2),
                'pop': round(pop * 100, 1)
            }

        else: # Neutral
            p_target = put_wall if put_wall and put_wall < price else price - 25
            c_target = call_wall if call_wall and call_wall > price else price + 25
            
            p_short = round_strike(p_target)
            c_short = round_strike(c_target)
            
            p_long = p_short - 10
            c_long = c_short + 10
            
            # Iron Condor (Put Spread + Call Spread)
            # Put Side
            ps_opt = get_leg_data(p_short, 'put')
            pl_opt = get_leg_data(p_long, 'put')
            # Call Side
            cs_opt = get_leg_data(c_short, 'call')
            cl_opt = get_leg_data(c_long, 'call')
            
            credit = 0
            pop_p, pop_c = 0.5, 0.5
            
            if ps_opt and pl_opt:
                credit += (ps_opt.get('bid', 0) - pl_opt.get('ask', 0))
                pop_p = 1 - abs(ps_opt.get('greeks', {}).get('delta', -0.5))
            
            if cs_opt and cl_opt:
                credit += (cs_opt.get('bid', 0) - cl_opt.get('ask', 0))
                pop_c = 1 - abs(cs_opt.get('greeks', {}).get('delta', 0.5))

            # Joint probability (assuming independence roughly, or just product of PoPs?)
            # PoP for IC is roughly P(Price between shorts).
            # P(between) = 1 - P(below put) - P(above call)
            # P(below put) = abs(delta_put)
            # P(above call) = abs(delta_call)
            # PoP = 1 - |d_put| - |d_call|
            
            # Let's re-calculate more accurately
            d_put = abs(ps_opt.get('greeks', {}).get('delta', 0) if ps_opt else 0)
            d_call = abs(cs_opt.get('greeks', {}).get('delta', 0) if cs_opt else 0)
            combined_pop = 1 - d_put - d_call
            
            strategy = {
                'name': 'Iron Condor',
                'legs': [
                    f"SELL {int(p_short)}P / {int(c_short)}C",
                    f"BUY {int(p_long)}P / {int(c_long)}C"
                ],
                'rationale': f'Neutral GEX. Range: {int(p_short)}-{int(c_short)}.',
                'premium': round(credit, 2),
                'pop': round(combined_pop * 100, 1)
            }
            
        # --- ENTRY SIGNAL ---
        signal_text = "WAIT"
        signal_color = "#666" # Gray
        dist_threshold = 15 # Points
        
        d_call = (call_wall - price) if call_wall else 999
        d_put = (price - put_wall) if put_wall else 999
        
        if total_gex > 1 and d_put < dist_threshold:
            signal_text = "BUY (Support Bounce)"
            signal_color = "#00ff9d" # Green
        elif total_gex < -1 and d_call < dist_threshold:
            signal_text = "SELL (Resistance Rejection)"
            signal_color = "#ff3366" # Red
        elif -1 <= total_gex <= 1 and min(d_call, d_put) > dist_threshold:
             signal_text = "RANGE (Neutral)"
             signal_color = "#bf00ff" # Purple
        elif total_gex > 3 and d_call < dist_threshold:
            signal_text = "CAUTION (Near Resistance)"
            signal_color = "#ffff00" # Yellow
        elif total_gex < -3 and d_put < dist_threshold:
            signal_text = "CAUTION (Near Support)"
            signal_color = "#ffff00" # Yellow
            
        # --- VOLATILITY REGIME ---
        regime = "Neutral"
        note = "Choppy Action"
        if total_gex > 2:
            regime = "Positive Gamma"
            note = "Mean Reversion (Buy Dips)"
        elif total_gex < -2:
            regime = "Negative Gamma"
            note = "High Volatility (Trend)"
            
        strategy['signal'] = {
            'text': signal_text, 
            'color': signal_color,
            'regime': regime,
            'note': note
        }
        
    except Exception as e:
        print(f"Strategy error: {e}")

    # --- IV & Expected Move (ATM Straddle) ---
    zero_dte_iv = 0
    expected_move = 0
    try:
        atm_strike = round_strike(price)
        atm_call = opt_map.get((atm_strike, 'call'))
        atm_put = opt_map.get((atm_strike, 'put'))
        
        ivs = []
        cost = 0
        if atm_call:
            ivs.append(atm_call.get('greeks', {}).get('mid_iv', 0))
            cost += (atm_call.get('bid', 0) + atm_call.get('ask', 0)) / 2
        if atm_put:
            ivs.append(atm_put.get('greeks', {}).get('mid_iv', 0))
            cost += (atm_put.get('bid', 0) + atm_put.get('ask', 0)) / 2
            
        if ivs:
            zero_dte_iv = sum(ivs) / len(ivs) * 100 # Convert to %
        expected_move = cost
    except Exception as e:
        print(f"IV calc error: {e}")

    print("--- Done ---")

    return {
        'ticker': ticker,
        'price': price,
        'expiry': expiry,
        'total_gex': total_gex,
        'call_wall': call_wall,
        'put_wall': put_wall,
        'max_oi': max_oi_strike,
        'zero_dte_iv': round(zero_dte_iv, 2),
        'expected_move': round(expected_move, 2),
        'strategy': strategy,
        'strikes': chart_labels,
        'gex': chart_data,
        'oi': chart_oi,
        'volume': chart_vol,
        'premium': strategy.get('premium'), # Add direct access if needed, but it's in strategy
        'pop': strategy.get('pop')
    }

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/gex')
def api_gex():
    date_param = request.args.get('date')
    ticker_param = request.args.get('ticker', 'SPX').upper()
    data = get_gex_data_json(ticker_param, date_param)
    if not data:
        return jsonify({'error': 'Failed to fetch data'}), 500
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=8000)
