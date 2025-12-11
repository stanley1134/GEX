with open('webapp/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

news_panel = '''
            <!-- Market News Panel -->
            <div class="panel" style="background: linear-gradient(135deg, rgba(255, 102, 0, 0.1), rgba(204, 82, 0, 0.1)); border: 1px solid #ff6600;">
                <h3 style="margin: 0 0 10px 0; color: #ff9933; font-size: 1rem; text-transform: uppercase; display: flex; align-items: center; gap: 5px;">
                    <span>📰</span> Market News
                </h3>
                
                <div id="news-container" style="max-height: 400px; overflow-y: auto;">
                    <div style="color: #888; font-size: 0.85rem; font-style: italic;">Loading news...</div>
                </div>
            </div>
'''

# Find the closing </aside> for right sidebar and insert news panel before it
import re
pattern = r'(</div>\s+</div>\s+</aside>\s+</main>)'
replacement = news_panel + r'        </aside>\n    </main>'
content = re.sub(pattern, replacement, content)

# Update version
content = content.replace('v=41', 'v=42')

with open('webapp/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ News panel added!")
