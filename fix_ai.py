import re

# Read the file
with open('webapp/app1.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the broken analyze_trade_with_ai function
# Simple approach: replace everything from "def analyze_trade_with_ai" to the next "# --- GEX Logic ---"
pattern = r'(def analyze_trade_with_ai\(market_data\):.*?)(# --- GEX Logic ---)'
replacement = r'''def analyze_trade_with_ai(market_data):
    """Use AI to analyze market data and provide trade recommendations"""
    
    # Using Hugging Face Inference API (FREE)
    HF_API_KEY = os.getenv("HF_API_KEY", "")
    
    if not HF_API_KEY:
        return {
            'pin_recommendation': 'AI Disabled',
            'trade_setup': 'Get free HuggingFace API key at huggingface.co/settings/tokens',
            'probability': 0,
            'risk_reward': 'N/A',
            'context': 'Free AI analysis available! Just add HF_API_KEY to .env file'
        }
    
    try:
        # Format prompt
        prompt = f"""Analyze this 0DTE SPX options data and provide trade recommendation:
Price: ${market_data.get('price', 0):.2f}
Total GEX: ${market_data.get('total_gex', 0):.2f}B
Call Wall: {market_data.get('call_wall', 'N/A')}
Put Wall: {market_data.get('put_wall', 'N/A')}
P/C Ratio: {market_data.get('put_call_ratio', 0):.2f}
Signal: {market_data.get('strategy', {}).get('signal', {}).get('text', 'N/A')}

Provide:
PIN: Best strike to anchor short leg
TRADE: Specific trade (e.g., "Sell 6820P / Buy 6810P")
PROBABILITY: Success chance %
R/R: Risk/reward ratio
CONTEXT: Why this trade now (1 sentence)"""

        # Call Hugging Face API
        url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 250, "temperature": 0.7}}
        
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        print(f"HuggingFace API Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"HF API Error: {response.text}")
            raise Exception(f"HF API error: {response.status_code}")
        
        # Parse response
        result = response.json()
        ai_text = result[0]['generated_text'].replace(prompt, '').strip()
        
        # Extract sections
        lines = ai_text.split('\\n')
        analysis = {
            'pin_recommendation': '',
            'trade_setup': '',
            'probability': 0,
            'risk_reward': '',
            'context': ''
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith('PIN:'):
                analysis['pin_recommendation'] = line.replace('PIN:', '').strip()
            elif line.startswith('TRADE:'):
                analysis['trade_setup'] = line.replace('TRADE:', '').strip()
            elif line.startswith('PROBABILITY:'):
                prob_str = line.replace('PROBABILITY:', '').strip().replace('%', '')
                try:
                    analysis['probability'] = int(prob_str.split()[0])
                except:
                    analysis['probability'] = 0
            elif line.startswith('R/R:'):
                analysis['risk_reward'] = line.split(':', 1)[1].strip() if ':' in line else line
            elif line.startswith('CONTEXT:'):
                analysis['context'] = line.replace('CONTEXT:', '').strip()
        
        # Fallback if parsing fails
        if not analysis['pin_recommendation']:
            analysis['pin_recommendation'] = 'Check response below'
            analysis['trade_setup'] = ai_text[:100]
            analysis['context'] = 'Raw AI output shown in trade setup'
        
        return analysis
        
    except Exception as e:
        print(f"AI Analysis error: {e}")
        return {
            'pin_recommendation': 'Analysis Failed',
            'trade_setup': str(e)[:80],
            'probability': 0,
            'risk_reward': 'N/A',
            'context': 'Check terminal for error details'
        }

\2'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open('webapp/app1.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed and integrated Hugging Face AI (FREE)")
