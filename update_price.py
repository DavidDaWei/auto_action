import requests
import datetime
import re

# 轉換常數
OZ_TO_G = 31.1034768
G_TO_TAEL = 37.5

def get_taiwan_data():
    url = "https://pm.shiny.com.tw/ajax_chartupdate.php?w=arw"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        raw_html = response.text
        
        items = ["黃金", "白銀", "鉑金", "鈀金", "美匯"]
        rows_html = ""
        
        for label in items:
            # 匹配 買價/賣價
            pattern = label + r'</span>\s*<span style="color: #7129c2">([\d,.]+)</span>/<span style="color: #7129c2">([\d,.]+)</span>'
            match = re.search(pattern, raw_html)
            
            if match:
                buy_oz = float(match.group(1).replace(',', ''))
                sell_oz = float(match.group(2).replace(',', ''))
                
                # 計算每公克
                buy_g = buy_oz / OZ_TO_G
                sell_g = sell_oz / OZ_TO_G
                
                # 計算每台兩
                buy_tael = buy_g * G_TO_TAEL
                sell_tael = sell_g * G_TO_TAEL
                
                rows_html += f"""
                <tr>
                    <td class="cat-name">{label}</td>
                    <td class="buy-sell">{buy_oz:,.0f} / {sell_oz:,.0f}</td>
                    <td>
                        <span class="converted">每公克：{buy_g:,.2f} / {sell_g:,.2f}</span>
                        <span class="converted">每台兩：{buy_tael:,.0f} / {sell_tael:,.0f}</span>
                    </td>
                </tr>
                """
            else:
                rows_html += f"<tr><td class='cat-name'>{label}</td><td colspan='2'>解析失敗</td></tr>"
        
        return rows_html
    except Exception as e:
        return f"<tr><td colspan='3'>連線失敗: {e}</td></tr>"

def get_intl_price():
    # 優先使用 GoldAPI，備援 Binance
    try:
        r = requests.get("https://api.gold-api.com/ge/gold", timeout=10)
        return f"${float(r.json()['price']):,.2f}"
    except:
        try:
            r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=5)
            return f"${float(r.json()['price']):,.2f}"
        except:
            return "暫無數據"

def update_html(tw_rows, int_price):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 替換邏輯
    content = re.sub(r'<tbody id="taiwan-data">.*?</tbody>', f'<tbody id="taiwan-data">{tw_rows}</tbody>', content, flags=re.DOTALL)
    content = re.sub(r'id="gold-price">.*?</div>', f'id="gold-price">{int_price}</div>', content)
    content = re.sub(r'id="update-time">.*?</span>', f'id="update-time">{now}</span>', content)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    tw = get_taiwan_data()
    bn = get_intl_price()
    update_html(tw, bn)
    print("數據轉換與更新完成！")
