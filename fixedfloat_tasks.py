import hashlib, hmac, base64, requests, time, logging, json
import json_io
from urllib.parse import urlencode

API_URL = "https://fixedfloat.com/api/v1"

def successfulFixedFloatResponse(resp):
    if 'code' in resp and int(resp['code']) == 0:
        return True
    return False

def getSignature(secret, data):
    secretBytes = secret.encode('utf-8')
    dataBytes = data.encode('utf-8')
    return hmac.new(secretBytes, dataBytes, digestmod=hashlib.sha256).hexdigest()

def ffAuthReq(path, isGet, data = ""):
    auth_info = json_io.getJsonFile("auth.json")['fixedfloat']
    headers = {
        'X-API-KEY': auth_info['key'],
        'X-API-SIGN': getSignature(auth_info['secret'], data),
        "Content-Type": "application/x-www-form-urlencoded"
        }
    if isGet:
        return requests.get(API_URL + path + '?' + data, headers=headers)
    else:
        return requests.post(API_URL + path, headers=headers, data=data)

def ffCreateFloatOrder(fromCurrency, toCurrency, fromAmount, toAddress):
    data = urlencode({
        "fromCurrency": fromCurrency,
        "toCurrency": toCurrency,
        "fromQty": float(fromAmount),
        "toAddress": toAddress,
        "type": "float"
        })
    resp = ffAuthReq('/createOrder', False, data).json()
    if successfulFixedFloatResponse(resp):
        return resp['data']
    return {"Error": resp['msg']}

def getOrder(id_, token):
    data = urlencode({
        "id": id_,
        "token": token
        })
    resp = ffAuthReq('/getOrder', True, data).json()
    if successfulFixedFloatResponse(resp):
        return resp['data']
    return {"Error": resp['msg']}

def ffVerifyOrderComplete(id_, token, retryCount, waitSeconds):
    tryCount = 0
    result = None
    while tryCount < retryCount:
        logging.debug(f"Attempting verify order {id_} is complete.")
        result = getOrder(id_, token)
        if 'Error' in result:
            return result
        status = int(result['status'])
        logging.debug(f"Order status was {status}.")
        if status == 5:
            return {"Error": f"Order {id_} expired!"}
        if status == 7:
            return {"Error": f"Order {id_} requires a decision.\n{result}"}
        if status == 4:
            return { "Status" : status }
        tryCount += 1
        time.sleep(waitSeconds)
    return {"Error": f"Could not verify order {id_} was complete after {retryCount} tries.\n{result}"}
