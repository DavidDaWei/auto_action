import requests
import datetime
import re

def get_price():
    # 準備多個 API 來源與模擬瀏覽器的 Header
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 來源 1: Binance (PAXG 價格)
    # 來源 2: Coinbase (PAXG 價格)
    # 來源 3: Gate.io (PAXG 價格)
    sources = [
        ("Binance", "https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT"),
        ("Coinbase", "https://api.coinbase.com/v2/prices/PAXG-USD/spot"),
        ("Gate.io", "https://data.gateapi.io/api2/1/ticker/paxg_usdt")
    ]
    
    for name, url in sources:
        try:
            print(f"正在嘗試從 {name} 獲取數據...")
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"{name} 回傳錯誤碼: {response.status_code}")
                continue
                
            data = response.json()
            
            if name == "Binance":
                price = float(data['price'])
            elif name == "Coinbase":
                price = float(data['data']['amount'])
            elif name == "Gate.io":
                price = float(data['last'])
                
            print(f"成功獲取價格: {price}")
            return f"${price:,.2f} USD"
            
        except Exception as e:
            print(f"{name} 請求發生異常: {e}")
            continue
            
    return "獲取失敗 (所有來源皆失效)"

def update_html(price):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 使用正則表達式替換內容
        content = re.sub(r'id="gold-price">.*?</div>', f'id="gold-price">{price}</div>', content)
        content = re.sub(r'id="update-time">.*?</span>', f'id="update-time">{now} (UTC)</span>', content)
        
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("HTML 檔案已更新")
    except Exception as e:
        print(f"更新 HTML 失敗: {e}")

if __name__ == "__main__":
    current_price = get_price()
    update_html(current_price)
