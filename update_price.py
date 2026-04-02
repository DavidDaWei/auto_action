import requests
import datetime
import re

# 1. 換算常數
OZ_TO_G = 31.1035
G_TO_TAEL = 37.5

# 2. 定義 HTML 模板 (將 HTML 直接寫在 Python 裡)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>貴金屬實時監報</title>
    <style>
        body {{ font-family: -apple-system, "Microsoft JhengHei", sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; color: #333; }}
        .container {{ max-width: 800px; margin: auto; background: white; padding: 25px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }}
        h2 {{ border-left: 5px solid #d4af37; padding-left: 15px; margin-bottom: 20px; font-size: 1.5em; }}
        .price-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 0.95em; }}
        .price-table th {{ background: #f8f9fa; color: #666; font-weight: 600; text-align: left; padding: 12px; border-bottom: 2px solid #eee; }}
        .price-table td {{ padding: 12px; border-bottom: 1px solid #eee; }}
        .cat-name {{ font-weight: bold; color: #34006e; width: 70px; }}
        .buy-sell {{ color: #7129c2; font-family: monospace; font-weight: 600; font-size: 1.1em; }}
        .converted {{ font-size: 0.85em; color: #555; background: #fdf6e3; padding: 4px 8px; border-radius: 4px; display: block; margin-top: 4px; line-height: 1.5; }}
        .intl-box {{ text-align: center; background: #333; color: #d4af37; padding: 20px; border-radius: 12px; margin-top: 20px; }}
        .intl-price {{ font-size: 2.5em; font-weight: bold; margin: 5px 0; }}
        .footer {{ text-align: center; font-size: 0.8em; color: #999; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>🇹🇼 台灣實時行情 (自動換算)</h2>
        <table class="price-table">
            <thead>
                <tr>
                    <th>項目</th>
                    <th>原始報價 (盎司/台幣)</th>
                    <th>單位換算 (買入 / 賣出)</th>
                </tr>
            </thead>
            <tbody>
                {tw_rows}
            </tbody>
        </table>
        <div class="intl-box">
            <div style="font-size: 0.9em; color: #aaa;">🌍 國際黃金現貨 (USD)</div>
            <div class="intl-price">{intl_price}</div>
            <div style="font-size: 0.8em; color: #888;">最後更新：{update_time} (UTC)</div>
        </div>
        <div class="footer">資料來源：絢麗、GoldAPI / 自動更新</div>
    </div>
</body>
</html>
"""

def get_data():
    tw_url = "https://pm.shiny.com.tw/ajax_chartupdate.php?w=arw"
    headers = {'User-Agent': 'Mozilla/5.0'}
    tw_rows = ""
    intl_price = "暫無數據"
    
    try:
        # 抓取台灣數據
        resp = requests.get(tw_url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        raw = resp.text
        for label in ["黃金", "白銀", "鉑金", "鈀金", "美匯"]:
            pattern = label + r'</span>\s*<span style="color: #7129c2">([\d,.]+)</span>/<span style="color: #7129c2">([\d,.]+)</span>'
            match = re.search(pattern, raw)
            if match:
                buy_oz = float(match.group(1).replace(',', ''))
                sell_oz = float(match.group(2).replace(',', ''))
                buy_g, sell_g = buy_oz/OZ_TO_G, sell_oz/OZ_TO_G
                buy_t, sell_t = buy_g*G_TO_TAEL, sell_g*G_TO_TAEL
                tw_rows += f"<tr><td class='cat-name'>{label}</td><td class='buy-sell'>{buy_oz:,.0f} / {sell_oz:,.0f}</td><td><span class='converted'>每公克：{buy_g:,.2f} / {sell_g:,.2f}</span><span class='converted'>每台兩：{buy_t:,.0f} / {sell_t:,.0f}</span></td></tr>"
            else:
                tw_rows += f"<tr><td>{label}</td><td colspan='2'>解析失敗</td></tr>"

        # 抓取國際數據
        r = requests.get("https://api.gold-api.com/ge/gold", timeout=10)
        intl_price = f"${float(r.json()['price']):,.2f}"
    except Exception as e:
        print(f"Error: {e}")
        
    return tw_rows, intl_price

if __name__ == "__main__":
    tw, intl = get_data()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 填充模板
    final_html = HTML_TEMPLATE.format(tw_rows=tw_rows, intl_price=intl, update_time=now)
    
    # 直接覆蓋寫入檔案 (這會清空原本 3GB 的檔案，變回 幾 KB)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    print("HTML 已重新生成！")
