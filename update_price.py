import requests
import datetime
import re
import json
import os

# --- 參數調整區 ---
MAX_HISTORY = 1000  # 保存最近 100 筆資料 (約 8 小時的數據，若每 5 分鐘抓一次)
# ----------------

OZ_TO_G = 31.1035
G_TO_TAEL = 37.5

# 內建 HTML 模板 (包含 Chart.js)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>貴金屬歷史監報</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: -apple-system, "Microsoft JhengHei", sans-serif; background: #f0f2f5; margin: 0; padding: 20px; color: #333; }}
        .container {{ max-width: 900px; margin: auto; background: white; padding: 25px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }}
        h2 {{ border-left: 5px solid #d4af37; padding-left: 15px; margin-bottom: 20px; }}
        .price-table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
        .price-table th, .price-table td {{ padding: 12px; border-bottom: 1px solid #eee; text-align: left; }}
        .price-table th {{ background: #fafafa; color: #666; }}
        .chart-box {{ margin-top: 40px; padding: 20px; background: #fff; border: 1px solid #eee; border-radius: 12px; }}
        .chart-container {{ position: relative; height: 300px; width: 100%; }}
        .footer {{ text-align: center; font-size: 0.8em; color: #999; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>🇹🇼 台灣實時行情與走勢</h2>
        <table class="price-table">
            <thead>
                <tr><th>項目</th><th>原始 (盎司/台幣)</th><th>換算 (公克 / 台兩)</th></tr>
            </thead>
            <tbody>
                {tw_rows}
            </tbody>
        </table>

        <div class="chart-box">
            <h3>📈 黃金走勢 (TWD/oz)</h3>
            <div class="chart-container"><canvas id="goldChart"></canvas></div>
        </div>
        <div class="chart-box">
            <h3>📈 白銀走勢 (TWD/oz)</h3>
            <div class="chart-container"><canvas id="silverChart"></canvas></div>
        </div>
        <div class="chart-box">
            <h3>📈 美元匯率 (TWD)</h3>
            <div class="chart-container"><canvas id="usdChart"></canvas></div>
        </div>

        <div class="footer">
            最後更新：{update_time} (UTC) | 保存筆數：{history_count}
        </div>
    </div>

    <script>
        const rawData = {history_json};
        const labels = rawData.map(d => d.time);

        function draw(id, label, data, color) {{
            new Chart(document.getElementById(id), {{
                type: 'line',
                data: {{
                    labels: labels,
                    datasets: [{{ 
                        label: label, 
                        data: data, 
                        borderColor: color, 
                        backgroundColor: color + '22',
                        fill: true, 
                        tension: 0.3,
                        pointRadius: 2
                    }}]
                }},
                options: {{ 
                    responsive: true, 
                    maintainAspectRatio: false,
                    interaction: {{ intersect: false, mode: 'index' }},
                    scales: {{ y: {{ beginAtZero: false }} }}
                }}
            }});
        }}

        draw('goldChart', '黃金', rawData.map(d => d.gold), '#d4af37');
        draw('silverChart', '白銀', rawData.map(d => d.silver), '#999999');
        draw('usdChart', '美元匯率', rawData.map(d => d.usd), '#2ecc71');
    </script>
</body>
</html>
"""

def get_current():
    url = "https://pm.shiny.com.tw/ajax_chartupdate.php?w=arw"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        raw = resp.text
        point = {"time": datetime.datetime.now().strftime("%H:%M")}
        
        for label, key in [("黃金", "gold"), ("白銀", "silver"), ("美匯", "usd")]:
            pattern = label + r'</span>\s*<span style="color: #7129c2">([\d,.]+)</span>'
            match = re.search(pattern, raw)
            if match:
                point[key] = float(match.group(1).replace(',', ''))
        return point
    except:
        return None

def update_db_and_html():
    file_json = 'data.json'
    history = []
    
    # 1. 讀取
    if os.path.exists(file_json):
        with open(file_json, 'r', encoding='utf-8') as f:
            try: history = json.load(f)
            except: history = []

    # 2. 抓取新數據並加入
    new_p = get_current()
    if new_p:
        history.append(new_p)
    
    # 3. 裁切歷史
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    # 4. 存回 JSON
    with open(file_json, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    # 5. 生成表格內容
    last = history[-1] if history else {}
    rows = ""
    for label, key in [("黃金", "gold"), ("白銀", "silver"), ("美匯", "usd")]:
        val = last.get(key, 0)
        if key == "usd":
            rows += f"<tr><td>{label}</td><td>{val}</td><td>--</td></tr>"
        else:
            g = val / OZ_TO_G
            t = g * G_TO_TAEL
            rows += f"<tr><td>{label}</td><td>{val:,.0f}</td><td>{g:,.2f} / {t:,.0f}</td></tr>"

    # 6. 生成 HTML
    final_html = HTML_TEMPLATE.format(
        tw_rows=rows,
        history_json=json.dumps(history),
        update_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        history_count=len(history)
    )
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(final_html)

if __name__ == "__main__":
    update_db_and_html()
    print("數據與圖表網頁更新完成！")
