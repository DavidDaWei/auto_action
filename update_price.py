import requests
import datetime
import re

# 換算常數
OZ_TO_G = 31.1035  # 1盎司 = 31.1035克
G_TO_TAEL = 37.5   # 1台兩 = 37.5克

def get_data():
    # 1. 抓取台灣數據
    tw_url = "https://pm.shiny.com.tw/ajax_chartupdate.php?w=arw"
    headers = {'User-Agent': 'Mozilla/5.0'}
    tw_html_rows = ""
    try:
        resp = requests.get(tw_url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        raw = resp.text
        
        for label in ["黃金", "白銀", "鉑金", "鈀金", "美匯"]:
            # 改用更強大的正則表達式來抓取
            pattern = label + r'</span>\s*<span style="color: #7129c2">([\d,.]+)</span>/<span style="color: #7129c2">([\d,.]+)</span>'
            match = re.search(pattern, raw)
            if match:
                buy_oz = float(match.group(1).replace(',', ''))
                sell_oz = float(match.group(2).replace(',', ''))
                
                # 數學換算
                buy_g = buy_oz / OZ_TO_G
                sell_g = sell_oz / OZ_TO_G
                buy_tael = buy_g * G_TO_TAEL
                sell_tael = sell_g * G_TO_TAEL
                
                tw_html_rows += f"""
                <tr>
                    <td class="cat-name">{label}</td>
                    <td class="buy-sell">{buy_oz:,.0f} / {sell_oz:,.0f}</td>
                    <td>
                        <span class="converted">每公克：{buy_g:,.2f} / {sell_g:,.2f}</span>
                        <span class="converted">每台兩：{buy_tael:,.0f} / {sell_tael:,.0f}</span>
                    </td>
                </tr>"""
            else:
                tw_html_rows += f"<tr><td>{label}</td><td colspan='2'>解析失敗</td></tr>"
    except Exception as e:
        tw_html_rows = f"<tr><td colspan='3'>連線失敗: {e}</td></tr>"

    # 2. 抓取國際數據 (增加多個備援)
    intl_price = "暫無數據"
    for api in ["https://api.gold-api.com/ge/gold", "https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT"]:
        try:
            r = requests.get(api, timeout=10)
            data = r.json()
            val = data.get('price') or data.get('data', {}).get('amount')
            if val:
                intl_price = f"${float(val):,.2f}"
                break
        except:
            continue
            
    return tw_html_rows, intl_price

def update_file(tw_rows, intl_price):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 精準取代標記之間的內容
    content = re.sub(r'.*?', f'{tw_rows}', content, flags=re.DOTALL)
    content = re.sub(r'.*?', f'{intl_price}', content)
    content = re.sub(r'.*?', f'{now} (UTC)', content)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    tw, intl = get_data()
    update_file(tw, intl)
    print("更新完成")
