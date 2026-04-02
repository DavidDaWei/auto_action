import requests
import datetime
import re

def get_taiwan_data():
    url = "https://pm.shiny.com.tw/ajax_chartupdate.php?w=arw"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        # 移除多餘的 HTML 標籤以便解析，或直接抓關鍵字
        raw_html = response.text
        
        # 使用正則表達式抓取各項數值 (抓取 買/賣 價格)
        def extract(label):
            pattern = label + r' <span style="color: #7129c2">(.*?)</span>/<span style="color: #7129c2">(.*?)</span>'
            match = re.search(pattern, raw_html)
            if match:
                return f"<b>{label}</b>: {match.group(1)} / {match.group(2)}"
            return f"<b>{label}</b>: 獲取失敗"

        results = [extract("黃金"), extract("白銀"), extract("鉑金"), extract("鈀金"), extract("美匯")]
        return "<br>".join(results)
    except Exception as e:
        return f"台灣來源更新失敗: {e}"

def get_binance_price():
    # 這是原本的國際價格來源
    url = "https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT"
    try:
        r = requests.get(url, timeout=10)
        return f"${float(r.json()['price']):,.2f} USD"
    except:
        return "國際來源獲取失敗"

def update_html(tw_data, binance_price):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 替換台灣數據
    content = re.sub(r'id="taiwan-data">.*?</div>', f'id="taiwan-data">{tw_data}</div>', content)
    # 替換國際數據
    content = re.sub(r'id="gold-price">.*?</div>', f'id="gold-price">{binance_price}</div>', content)
    # 替換更新時間
    content = re.sub(r'id="update-time">.*?</span>', f'id="update-time">{now} (UTC)</span>', content)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    tw = get_taiwan_data()
    bn = get_binance_price()
    update_html(tw, bn)
    print("更新完成！")
