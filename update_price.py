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

HTML_TEMPLATE = """... (保持你原有的 HTML_TEMPLATE 不變) ..."""

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
