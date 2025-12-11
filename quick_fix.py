import re

with open('webapp/app1.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix the analyze_trade_with_ai function
output = []
skip_until_if = False
found_function = False

for i, line in enumerate(lines):
    if 'def analyze_trade_with_ai(market_data):' in line:
        found_function = True
        output.append(line)
        output.append('    """Use Gemini AI to analyze market data and provide trade recommendations"""\n')
        # Skip the broken early return and go straight to the if statement
        skip_until_if = True
        continue
    
    if skip_until_if:
        if 'if not GEMINI_API_KEY:' in line:
            skip_until_if = False
            output.append(line)
        continue
    
    # Fix the Gemini model endpoint
    if 'gemini-1.0-pro:generateContent' in line or 'gemini-1.5-flash' in line or 'gemini-pro:generateContent' in line:
        output.append('        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}"\n')
        continue
    
    output.append(line)

with open('webapp/app1.py', 'w', encoding='utf-8') as f:
    f.writelines(output)

print("Fixed! Using gemini-2.0-flash-exp model")
