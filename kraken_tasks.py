import urllib.parse, hashlib, hmac, base64, requests, time
import json_io

API_URL = "https://api.kraken.com"

def kMarketPrice(pair):
    resp = requests.get(API_URL + '/0/public/Ticker?pair=' + pair).json()
    if 'result' in resp and 'error' in resp and len(resp['error']) == 0:
        return resp['result'][pair]['c'][0]
    else:
        return {"Error": resp['error']}

def getSig(path, data, secret):
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = path.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()

def kAuthReq(path, data = {}):
    data['nonce'] = str(int(1000*time.time()))
    auth_info = json_io.getJsonFile("auth.json")['kraken']
    headers = {}
    headers['API-Key'] = auth_info['key']
    headers['API-Sign'] = getSig(path, data, auth_info['secret'])
    return requests.post(API_URL + path, headers=headers, data=data)

def kGetBalances():
    return kAuthReq('/0/private/Balance').json()

def kCreateMarketBuyOrder(buyAsset, sellAsset, amount):
    data = {
        "ordertype": "market",
        "type": "buy",
        "pair": buyAsset+sellAsset,
        "volume": str(amount)
        }
    resp = kAuthReq('/0/private/AddOrder', data).json()
    return resp

def kWithdrawCrypto(name, amount, addressName):
    data = {
        "asset": name,
        "key": addressName,
        "amount": str(amount)
        }
    return kAuthReq('/0/private/Withdraw', data).json()
