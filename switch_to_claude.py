import re

with open('webapp/app1.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the entire analyze_trade_with_ai function
new_function = '''# AI Analysis using Claude API
def analyze_trade_with_ai(market_data):
    """Use Claude AI to analyze market data and provide trade recommendations"""
    
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
    
    if not CLAUDE_API_KEY:
        return {
            'pin_recommendation': 'AI Disabled',
            'trade_setup': 'Add CLAUDE_API_KEY to .env (get free key at console.anthropic.com)',
            'probability': 0,
            'risk_reward': 'N/A',
            'context': 'Claude Sonnet 4.5 ready! Just add API key to .env file.'
        }
    
    try:
        prompt = f"""Analyze this 0DTE SPX options data:
Price: ${market_data.get('price', 0):.2f}, GEX: ${market_data.get('total_gex', 0):.2f}B
Call Wall: {market_data.get('call_wall')}, Put Wall: {market_data.get('put_wall')}
P/C: {market_data.get('put_call_ratio', 0):.2f}, Signal: {market_data.get('strategy', {}).get('signal', {}).get('text', 'N/A')}

Provide trade recommendation in this EXACT format:
PIN: <strike and reason>
TRADE: <specific setup>
PROBABILITY: <number>%
R/R: <ratio>
CONTEXT: <one sentence>"""

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"Claude API Status: {response.status_code}")
        
        if response.status_code != 200:
            raise Exception(f"Claude error: {response.status_code}")
        
        ai_text = response.json()['content'][0]['text'].strip()
        
        # Parse response
        analysis = {'pin_recommendation': '', 'trade_setup': '', 'probability': 0, 'risk_reward': '', 'context': ''}
        for line in ai_text.split('\\n'):
            line = line.strip()
            if line.startswith('PIN:'): analysis['pin_recommendation'] = line[4:].strip()
            elif line.startswith('TRADE:'): analysis['trade_setup'] = line[6:].strip()
            elif line.startswith('PROBABILITY:'):
                try: analysis['probability'] = int(line[12:].replace('%', '').strip().split()[0])
                except: pass
            elif line.startswith('R/R:'): analysis['risk_reward'] = line[4:].strip()
            elif line.startswith('CONTEXT:'): analysis['context'] = line[8:].strip()
        
        if not analysis['pin_recommendation']:
            analysis['pin_recommendation'] = 'See below'
            analysis['trade_setup'] = ai_text[:120]
        
        return analysis
    except Exception as e:
        print(f"AI error: {e}")
        return {'pin_recommendation': 'Failed', 'trade_setup': str(e)[:80], 'probability': 0, 'risk_reward': 'N/A', 'context': 'Check terminal'}
'''

# Find and replace the function
pattern = r'# AI Analysis.*?(?=\n# ---|def get_gex_data_json)'
content = re.sub(pattern, new_function + '\n', content, flags=re.DOTALL)

with open('webapp/app1.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Switched to Claude Sonnet 4.5!")
