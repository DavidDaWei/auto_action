import requests
import datetime
import os

def get_price():
    # 這裡以 Binance API 獲取 PAXG (掛鉤黃金的代幣) 作為示範，因為它不需要 API Key
    try:
        response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT")
        data = response.json()
        price = float(data['price'])
        return f"${price:,.2f} USD"
    except Exception as e:
        return "獲取失敗"

def update_html(price):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 讀取 index.html 並替換內容
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 簡單的取代邏輯
    import re
    content = re.sub(r'id="gold-price">.*?</div>', f'id="gold-price">{price}</div>', content)
    content = re.sub(r'id="update-time">.*?</span>', f'id="update-time">{now} (UTC)</span>', content)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    current_price = get_price()
    update_html(current_price)
    print(f"更新成功: {current_price}")
