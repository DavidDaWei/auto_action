import requests
import datetime
from zoneinfo import ZoneInfo
import json
import os
import sys

# --- 參數調整區 ---
MAX_HISTORY = 2000  # 保存最近歷史筆數
# ----------------

# 換算常數
OZ_TO_G = 31.1035   # 1 盎司 = 31.1035 公克
G_TO_TAEL = 37.5    # 1 台兩 = 37.5 公克

HTML_TEMPLATE =  """

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

    """從網站抓取 當前數據"""

    url = "https://pm.shiny.com.tw/ajax_chartupdate.php?w=arw"

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    try:

        resp = requests.get(url, headers=headers, timeout=15)

        resp.encoding = 'utf-8'

        raw = resp.text

        # 以目前時間 (時:分) 作為 X 軸標籤

        point = {"time": datetime.datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M")}

        

        # 解析數據 (抓取標籤後的第一個數值)

        for label, key in [("黃金", "gold"), ("白銀", "silver"), ("美匯", "usd")]:

            pattern = label + r'</span>\s*<span style="color: #7129c2">([\d,.]+)</span>'

            match = re.search(pattern, raw)

            if match:

                # 網站抓到的數字 (4,500 左右) 實際上是台幣/公克

                val = float(match.group(1).replace(',', ''))

                point[key] = val

        

        # 確保必要的數據都有抓到

        if "gold" in point:

            return point

        return None

    except Exception as e:

        print(f"抓取數據發生錯誤: {e}")

        return None



def process_and_save():

    """讀取、更新歷史紀錄並生成網頁"""

    file_json = 'data.json'

    history = []

    

    # 1. 讀取現有的歷史數據

    if os.path.exists(file_json):

        with open(file_json, 'r', encoding='utf-8') as f:

            try:

                history = json.load(f)

            except:

                history = []



    # 2. 獲取新數據並加入歷史紀錄

    new_data = get_current_data()

    if new_data:

        history.append(new_data)

        print(f"成功加入新數據: {new_data}")

    

    # 3. 限制歷史紀錄筆數

    if len(history) > MAX_HISTORY:

        history = history[-MAX_HISTORY:]



    # 4. 存回 JSON 檔案 (data.json)

    with open(file_json, 'w', encoding='utf-8') as f:

        json.dump(history, f, ensure_ascii=False, indent=2)



    # 5. 準備表格顯示內容 (使用最後一筆數據)

    last_point = history[-1] if history else {}

    tw_rows_html = ""

    

    for label, key in [("黃金", "gold"), ("白銀", "silver"), ("美匯", "usd")]:

        val = last_point.get(key, 0)

        if key == "usd":

            tw_rows_html += f"<tr><td class='cat-name'>{label}</td><td class='main-price'>{val}</td><td>--</td></tr>"

        else:

            # 換算邏輯：val 是公克價

            g_price = val

            tael_price = g_price * G_TO_TAEL

            oz_price = g_price * OZ_TO_G

            

            tw_rows_html += f"""

            <tr>

                <td class='cat-name'>{label}</td>

                <td class='main-price'>{g_price:,.0f} 元/g</td>

                <td>

                    <span class='converted'>每台兩：{tael_price:,.0f} 元</span>

                    <span class='converted'>每盎司：{oz_price:,.0f} 元</span>

                </td>

            </tr>

            """

def get_current_data():
    """從新版 JSON API 抓取當前數據"""
    url = "https://api.shiny.com.tw/frontend/quotations/scrolling-banner"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://pm.shiny.com.tw/',
        'Accept': 'application/json'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"API 連線失敗，HTTP 狀態碼: {resp.status_code}")
            return None
            
        res_json = resp.json()
        if not res_json.get("success"):
            print("API 回傳失敗訊息:", res_json.get("message"))
            return None

        # 取得報價清單
        items = res_json.get("data", {}).get("data", [])
        point = {
            "time": datetime.datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M")
        }

        # 欄位對應（預設抓取 sell 賣出價）
        key_map = {
            "黃金": "gold",
            "白銀": "silver",
            "美匯": "usd"
        }

        for item in items:
            title = item.get("title")
            if title in key_map:
                key = key_map[title]
                # 轉為浮點數，此處使用賣出價 (sell)
                point[key] = float(item.get("sell", 0))

        # 驗證必要欄位是否齊全
        if "gold" in point and "silver" in point and "usd" in point:
            return point

        print("數據不完整，抓取到的內容:", point)
        return None

    except Exception as e:
        print(f"抓取數據發生例外錯誤: {e}")
        return None

def process_and_save():
    """讀取、更新歷史紀錄並生成網頁"""
    file_json = 'data.json'
    history = []
    
    # 1. 讀取現有的歷史數據
    if os.path.exists(file_json):
        with open(file_json, 'r', encoding='utf-8') as f:
            try:
                history = json.load(f)
            except Exception:
                history = []

    # 2. 獲取新數據
    new_data = get_current_data()
    if not new_data:
        print("錯誤：無法取得新報價，中斷本次工作以防靜默失敗。")
        sys.exit(1)

    history.append(new_data)
    print(f"成功加入新數據: {new_data}")
    
    # 3. 限制歷史紀錄筆數
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    # 4. 存回 JSON 檔案
    with open(file_json, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    # 5. 準備表格顯示內容
    last_point = history[-1] if history else {}
    tw_rows_html = ""
    
    for label, key in [("黃金", "gold"), ("白銀", "silver"), ("美匯", "usd")]:
        val = last_point.get(key, 0)
        if key == "usd":
            tw_rows_html += f"<tr><td class='cat-name'>{label}</td><td class='main-price'>{val:.2f}</td><td>--</td></tr>"
        else:
            g_price = val
            tael_price = g_price * G_TO_TAEL
            oz_price = g_price * OZ_TO_G
            
            tw_rows_html += f"""
            <tr>
                <td class='cat-name'>{label}</td>
                <td class='main-price'>{g_price:,.2f} 元/g</td>
                <td>
                    <span class='converted'>每台兩：{tael_price:,.0f} 元</span>
                    <span class='converted'>每盎司：{oz_price:,.0f} 元</span>
                </td>
            </tr>
            """

    # 6. 生成最終的 index.html
    now_str = datetime.datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M:%S")
    final_content = HTML_TEMPLATE.format(
        tw_rows=tw_rows_html,
        history_json=json.dumps(history),
        update_time=now_str,
        history_count=len(history)
    )
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(final_content)

if __name__ == "__main__":
    process_and_save()
    print("更新任務順利完成！")
