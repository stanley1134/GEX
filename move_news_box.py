with open('webapp/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove news panel from inside aside (right sidebar)
import re
news_pattern = r'\s*<!-- Market News Panel -->.*?</div>\s*</div>'
content = re.sub(news_pattern, '', content, flags=re.DOTALL)

# Add news as floating box before closing body tag
floating_news = '''
    <!-- Floating Market News Box -->
    <div id="news-box" style="position: fixed; bottom: 20px; right: 20px; width: 350px; max-height: 400px; background: linear-gradient(135deg, rgba(20, 20, 25, 0.95), rgba(30, 30, 35, 0.95)); border: 1px solid #ff6600; border-radius: 8px; padding: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); z-index: 1000; backdrop-filter: blur(10px);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h3 style="margin: 0; color: #ff9933; font-size: 0.9rem; text-transform: uppercase; display: flex; align-items: center; gap: 5px;">
                <span>📰</span> Market News
            </h3>
            <button onclick="document.getElementById('news-box').style.display='none'" style="background: none; border: none; color: #888; cursor: pointer; font-size: 1.2rem; padding: 0; line-height: 1;">&times;</button>
        </div>
        
        <div id="news-container" style="max-height: 320px; overflow-y: auto; padding-right: 5px;">
            <div style="color: #888; font-size: 0.85rem; font-style: italic;">Loading news...</div>
        </div>
    </div>

</body>'''

content = content.replace('</body>', floating_news)

# Update version
content = content.replace('v=42', 'v=43')

with open('webapp/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ News moved to floating bottom-right box!")
