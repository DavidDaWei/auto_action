import requests
import datetime
import re

def get_taiwan_data():
    url = "https://pm.shiny.com.tw/ajax_chartupdate.php?w=arw"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8' # 強制設定編碼
        raw_html = response.text
        
        # 修正後的 Regex：考慮到 </span> 標籤與可能的空格
        def extract(label):
            # 匹配模式：標籤名稱</span> 接著任意空格 接著 買價/賣價 的 span
            pattern = label + r'</span>\s*<span style="color: #7129c2">([\d,.]+)</span>/<span style="color: #7129c2">([\d,.]+)</span>'
            match = re.search(pattern, raw_html)
            if match:
                return f"<b>{label}</b>: {match.group(1)} / {match.group(2)}"
            return f"<b>{label}</b>: 解析失敗"

        results = [extract("黃金"), extract("白銀"), extract("鉑金"), extract("鈀金"), extract("美匯")]
        return "<br>".join(results)
    except Exception as e:
        return f"台灣來源連線失敗: {e}"

def get_international_price():
    # 換一個對 GitHub Actions 較友善的 API (Gold-API)
    url = "https://api.gold-api.com/ge/gold"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        # 取得金價並格式化
        price = float(data['price'])
        return f"${price:,.2f} USD"
    except:
        # 如果上面失敗，備援回 Binance
        try:
            r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=5)
            return f"${float(r.json()['price']):,.2f} USD"
        except:
            return "國際來源獲取失敗"

def update_html(tw_data, int_price):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 使用 .replace 或 re.sub 更新內容
    # 這裡確保匹配時不被換行符號干擾
    content = re.sub(r'id="taiwan-data">.*?</div>', f'id="taiwan-data">{tw_data}</div>', content, flags=re.DOTALL)
    content = re.sub(r'id="gold-price">.*?</div>', f'id="gold-price">{int_price}</div>', content, flags=re.DOTALL)
    content = re.sub(r'id="update-time">.*?</span>', f'id="update-time">{now} (UTC)</span>', content)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    print("開始獲取數據...")
    tw = get_taiwan_data()
    print(f"台灣數據: {tw}")
    bn = get_international_price()
    print(f"國際數據: {bn}")
    update_html(tw, bn)
    print("HTML 更新完成")
