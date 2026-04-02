import requests
import datetime
import re
import json
import os

# --- 參數調整區 ---
MAX_HISTORY = 1000  # 保存最近 100 筆資料 (若每 5 分鐘執行一次，約可保存 8 小時走勢)
# ----------------

# 換算常數
OZ_TO_G = 31.1035   # 1 盎司 = 31.1035 公克
G_TO_TAEL = 37.5    # 1 台兩 = 37.5 公克

# 內建 HTML 模板 (包含 CSS 與 Chart.js 邏輯)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>貴金屬實時走勢監報</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: -apple-system, "Microsoft JhengHei", sans-serif; background: #f0f2f5; margin: 0; padding: 20px; color: #333; }}
        .container {{ max-width: 900px; margin: auto; background: white; padding: 25px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }}
        h2 {{ border-left: 5px solid #d4af37; padding-left: 15px; margin-bottom: 20px; color: #444; }}
        .price-table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
        .price-table th, .price-table td {{ padding: 12px; border-bottom: 1px solid #eee; text-align: left; }}
        .price-table th {{ background: #fafafa; color: #666; font-weight: 600; }}
        .cat-name {{ font-weight: bold; color: #34006e; }}
        .main-price {{ font-family: monospace; font-weight: bold; color: #7129c2; font-size: 1.1em; }}
        .converted {{ font-size: 0.85em; color: #555; background: #fdf6e3; padding: 4px 8px; border-radius: 4px; display: block; margin-top: 4px; line-height: 1.5; }}
        .chart-box {{ margin-top: 30px; padding: 20px; background: #fff; border: 1px solid #eee; border-radius: 12px; }}
        .chart-container {{ position: relative; height: 250px; width: 100%; }}
        .footer {{ text-align: center; font-size: 0.8em; color: #999; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>🇹🇼 台灣實時行情與走勢 (台幣計價)</h2>
        <table class="price-table">
            <thead>
                <tr>
                    <th>項目</th>
                    <th>原始報價 (每公克)</th>
                    <th>單位換算 (每盎司 / 每台兩)</th>
                </tr>
            </thead>
            <tbody>
                {tw_rows}
            </tbody>
        </table>

        <div class="chart-box">
            <h3>📈 黃金走勢 (TWD/g)</h3>
            <div class="chart-container"><canvas id="goldChart"></canvas></div>
        </div>
        <div class="chart-box">
            <h3>📈 白銀走勢 (TWD/g)</h3>
            <div class="chart-container"><canvas id="silverChart"></canvas></div>
        </div>
        <div class="chart-box">
            <h3>📈 美元匯率 (USD/TWD)</h3>
            <div class="chart-container"><canvas id="usdChart"></canvas></div>
        </div>

        <div class="footer">
            最後更新時間：{update_time} (UTC) | 已保存數據：{history_count} 筆
            <br>資料來源：絢麗貴金屬自動抓取
        </div>
    </div>

    <script>
        const rawData = {history_json};
        const labels = rawData.map(d => d.time);

        function drawChart(id, label, data, color) {{
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
                    scales: {{ y: {{ beginAtZero: false, ticks: {{ precision: 2 }} }} }}
                }}
            }});
        }}

        drawChart('goldChart', '黃金 (公克)', rawData.map(d => d.gold), '#d4af37');
        drawChart('silverChart', '白銀 (公克)', rawData.map(d => d.silver), '#999999');
        drawChart('usdChart', '美元匯率', rawData.map(d => d.usd), '#2ecc71');
    </script>
</body>
</html>
"""

def get_current_data():
    """
