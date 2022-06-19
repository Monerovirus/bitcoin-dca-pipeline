import urllib.parse, hashlib, hmac, base64, requests, time, logging
import json_io

API_URL = "https://api.kraken.com"

def successfulKrakenResponse(resp):
    if 'result' in resp and 'error' in resp and len(resp['error']) == 0:
        return True
    return False

def kMarketPrice(pair):
    resp = requests.get(API_URL + '/0/public/Ticker?pair=' + pair).json()
    if successfulKrakenResponse(resp):
        return resp['result'][pair]['c'][0]
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

def kGetBalance(asset):
    resp = kAuthReq('/0/private/Balance').json()
    if successfulKrakenResponse(resp):
        return resp['result'][asset]
    return {"Error": resp['error']}

def kVerifyBalance(asset, requiredBalance, retryCount, waitSeconds):
    tryCount = 0
    result = None
    while tryCount < retryCount:
        logging.debug(f"Attempting verify balance is {requiredBalance} or higher.")
        result = kGetBalance(asset)
        if 'Error' in result:
            return result
        balance = float(result)
        if balance >= requiredBalance:
            return True
        tryCount += 1
        time.sleep(waitSeconds)
    return {"Error": f"Could not verify balance was {requiredBalance} after {retryCount} tries.\n{result}"}

def kCreateMarketBuyOrder(buyAsset, sellAsset, amount):
    data = {
        "ordertype": "market",
        "type": "buy",
        "pair": buyAsset + sellAsset,
        "volume": str(amount)
        }
    resp = kAuthReq('/0/private/AddOrder', data).json()
    if successfulKrakenResponse:
        return resp['result']['descr']['order']
    return {"Error": resp['error']}

def kWithdrawCrypto(name, amount, addressName):
    data = {
        "asset": name,
        "key": addressName,
        "amount": str(amount)
        }
    resp = kAuthReq('/0/private/Withdraw', data).json()
    if successfulKrakenResponse(resp):
        return resp['result']['refid']
    return {"Error": resp['error']}
