#!/usr/bin/env python3
import requests
import json

codes = ['512480', '512000', '516010', '515980']
names = {'512480': '半导体ETF', '512000': '券商ETF', '516010': '游戏ETF', '515980': '人工智能ETF'}

print("=" * 60)
print("ETF上午行情总结")
print("=" * 60)

for code in codes:
    market = '1' if code.startswith('5') or code.startswith('51') else '0'
    secid = f'{market}.{code}'
    url = 'http://push2.eastmoney.com/api/qt/stock/get'
    params = {
        'secid': secid,
        'fields': 'f43,f44,f45,f46,f47,f48,f50,f51,f52,f58,f60,f169,f170,f57'
    }
    
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        
        if data.get('data'):
            d = data['data']
            name = d.get('f57', names[code])
            latest = round(d.get('f43', 0) / 100, 3) if d.get('f43') else None
            change_pct = round(d.get('f170', 0) / 100, 2) if d.get('f170') else None
            open_price = round(d.get('f46', 0) / 100, 3) if d.get('f46') else None
            high = round(d.get('f44', 0) / 100, 3) if d.get('f44') else None
            low = round(d.get('f45', 0) / 100, 3) if d.get('f45') else None
            prev_close = round(d.get('f60', 0) / 100, 3) if d.get('f60') else None
            
            print(f"\n【{name} ({code})】")
            print(f"  开盘价: {open_price}")
            print(f"  最高价: {high}")
            print(f"  最低价: {low}")
            print(f"  当前价: {latest}")
            print(f"  涨跌幅: {change_pct}%")
            print(f"  昨收价: {prev_close}")
    except Exception as e:
        print(f"Error for {code}: {e}")

print("\n" + "=" * 60)
