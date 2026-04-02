import requests
import datetime
import re
import json
import os

# --- 參數調整區 ---
MAX_HISTORY = 100  # 你想要保存多少筆資料？(例如：100 筆)
# ----------------

OZ_TO_G = 31.1035
G_TO_TAEL = 37.5

def get_current_data():
    tw_url = "https://pm.shiny.com.tw/ajax_chartupdate.php?w=arw"
    headers = {'User-Agent': 'Mozilla/5.0'}
    data_point = {"time": datetime.datetime.now().strftime("%H:%M")}
    
    try:
        resp = requests.get(tw_url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        raw = resp.text
        
        # 抓取數值
        for label, key in [("黃金", "gold"), ("白銀", "silver"), ("美匯", "usd")]:
            pattern = label + r'</span>\s*<span style="color: #7129c2">([\d,.]+)</span>'
            match = re.search(pattern, raw)
            if match:
                val = float(match.group(1).replace(',', ''))
                data_point[key] = val
        return data_point
    except Exception as e:
        print(f"抓取失敗: {e}")
        return None

def save_history(new_point):
    file_path = 'data.json'
    history = []
    
    # 1. 讀取舊資料
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                history = json.load(f)
            except:
                history = []
    
    # 2. 加入新資料
    if new_point:
        history.append(new_point)
    
    # 3. 根據參數裁切筆數 (保留最後 N 筆)
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
    
    # 4. 存回 JSON
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    return history

def generate_html(history):
    # 這裡將 HTML 模板抽離，並把 JSON 資料嵌入到 JS 變數中
    with open('template.html', 'r', encoding='utf-8') as f:
        template = f.read()
    
    # 計算最後一筆的詳細資料供表格顯示
    last = history[-1] if history else {}
    
    # 格式化表格內容 (與之前邏輯相同)
    tw_rows = ""
    for label, key in [("黃金", "gold"), ("白銀", "silver"), ("美匯", "usd")]:
        val = last.get(key, 0)
        if key == "usd":
             tw_rows += f"<tr><td>{label}</td><td>{val}</td><td>--</td></tr>"
        else:
            g_val = val / OZ_TO_G
            t_val = g_val * G_TO_TAEL
            tw_rows += f"<tr><td>{label}</td><td>{val:,.0f}</td><td>{g_val:,.2f} / {t_val:,.0f}</td></tr>"

    # 替換 HTML 內容
    final_html = template.replace("{tw_content}", tw_rows)
    final_html = final_html.replace("{history_json}", json.dumps(history))
    final_html = final_html.replace("{update_time}", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(final_html)

if __name__ == "__main__":
    point = get_current_data()
    all_history = save_history(point)
    generate_html(all_history)
