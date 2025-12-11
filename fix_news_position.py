with open('webapp/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the floating news box
import re
floating_pattern = r'\s*<!-- Floating Market News Box -->.*?</div>\s*</body>'
content = re.sub(floating_pattern, '\n</body>', content, flags=re.DOTALL)

# Add news panel back to right sidebar, before closing </aside>
news_panel = '''
            <!-- Market News Panel -->
            <div class="panel" style="background: linear-gradient(135deg, rgba(255, 102, 0, 0.1), rgba(204, 82, 0, 0.1)); border: 1px solid #ff6600; margin-top: 20px;">
                <h3 style="margin: 0 0 10px 0; color: #ff9933; font-size: 1rem; text-transform: uppercase; display: flex; align-items: center; gap: 5px;">
                    <span>📰</span> Market News
                </h3>
                
                <div id="news-container" style="max-height: 350px; overflow-y: auto; padding-right: 5px;">
                    <div style="color: #888; font-size: 0.85rem; font-style: italic;">Loading news...</div>
                </div>
            </div>
        </aside>
    </main>'''

# Replace closing tags of right sidebar
content = re.sub(r'</aside>\s*</main>', news_panel, content)

# Update version
content = content.replace('v=43', 'v=44')

with open('webapp/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ News panel added to right sidebar!")
