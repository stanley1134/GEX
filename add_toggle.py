with open('webapp/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the closing </div> before </header> and add toggle before it
toggle_html = '''            <div class="stat-item">
                <span class="stat-label">Alerts</span>
                <label class="toggle-switch">
                    <input type="checkbox" id="alert-toggle" checked>
                    <span class="toggle-slider"></span>
                </label>
            </div>
'''

# Insert before the closing stats-container div
content = content.replace('        </div>\r\n    </header>', toggle_html + '        </div>\r\n    </header>')

with open('webapp/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Alert toggle added to HTML!")
