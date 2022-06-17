import urllib.parse, hashlib, hmac, base64, requests

def kMarketPrice(pair):
    resp = requests.get('https://api.kraken.com/0/public/Ticker?pair='+pair).json()
    if 'result' in resp and 'error' in resp and len(resp['error']) == 0:
        return resp['result'][pair]['c'][0]
    else:
        return {"Error": resp['error']}

