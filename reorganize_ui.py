import re

# Read the HTML file
with open('webapp/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove AI panel from left sidebar (between <!-- AI Analysis Panel --> and the next </aside>)
pattern = r'(\s+<!-- AI Analysis Panel -->.*?)\s+</aside>(\s+<!-- Main Chart --)'
replacement = r'        </aside>\2'
content = re.sub(pattern, replacement, content, flags=re.DOTALL, count=1)

# Add right sidebar with AI panel before </main>
ai_panel = '''
        <!-- Right Sidebar - AI Analysis -->
        <aside class="sidebar" style="width: 320px; min-width: 320px;">
            <!-- AI Analysis Panel -->
            <div class="panel" style="background: linear-gradient(135deg, rgba(138, 43, 226, 0.1), rgba(75, 0, 130, 0.1)); border: 1px solid #8a2be2;">
                <h3 style="margin: 0 0 10px 0; color: #bf00ff; font-size: 1rem; text-transform: uppercase; display: flex; align-items: center; gap: 5px;">
                    <span>🤖</span> AI Trade Analysis
                </h3>
                
                <div style="margin-bottom: 10px;">
                    <div style="color: #888; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 3px;">PIN Recommendation</div>
                    <div id="ai-pin" style="color: #00ff9d; font-weight: bold; font-size: 0.9rem; line-height: 1.4;">--</div>
                </div>

                <div style="margin-bottom: 10px;">
                    <div style="color: #888; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 3px;">Trade Setup</div>
                    <div id="ai-trade" style="color: #00e5ff; font-family: 'Roboto Mono', monospace; font-size: 0.85rem; line-height: 1.4;">--</div>
                </div>

                <div style="display: flex; gap: 15px; margin-bottom: 10px;">
                    <div style="flex: 1;">
                        <div style="color: #888; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 3px;">Probability</div>
                        <div id="ai-probability" style="color: #ffcc00; font-weight: bold; font-size: 1.1rem;">--%</div>
                    </div>
                    <div style="flex: 1;">
                        <div style="color: #888; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 3px;">R/R Ratio</div>
                        <div id="ai-rr" style="color: #ff6699; font-weight: bold; font-size: 1.1rem;">--</div>
                    </div>
                </div>

                <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #444;">
                    <div style="color: #888; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 3px;">Market Context</div>
                    <div id="ai-context" style="color: #aaa; font-size: 0.85rem; line-height: 1.4; font-style: italic;">--</div>
                </div>
            </div>
        </aside>
    </main>'''

content = content.replace('    </main>', ai_panel)

# Update version to v36
content = content.replace('v=35', 'v=36')

# Write back
with open('webapp/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("HTML reorganized successfully - AI panel moved to right sidebar")
