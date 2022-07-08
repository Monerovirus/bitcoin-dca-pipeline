import urllib.parse, requests, time, logging, json
import json_io
from simplejson.errors import JSONDecodeError

API_URL = "http://localhost:28088/json_rpc"

def tryParseResponse(resp):
    try:
        result = resp.json()
        if 'error' in result:
            return {"Error": result['error']}
        return result
    except JSONDecodeError as e:
        logging.error(f"Failed to parse monero-rpc response: {resp}")
        return {"Error": "Failed to parse monero-rpc response."}

def postRequest(data):
    data['jsonrpc'] = "2.0"
    data['id'] = "0"
    return requests.post(API_URL, data=json.dumps(data))

def moneroToAtomic(moneroAmount):
    return int(moneroAmount * 1_000_000_000_000)

def atomicToMonero(atomicAmount):
    return atomicAmount / 1_000_000_000_000

def mGetBalances():
    data = {'method': "get_accounts"}
    resp = tryParseResponse(postRequest(data))
    if 'Error' in resp:
        return resp

    return {"balance": resp['result']['total_balance'], "unlocked_balance": resp['result']['total_unlocked_balance']}

def mVerifyBalance(requiredBalance, retryCount, waitSeconds):
    atomicRequiredBalance = moneroToAtomic(requiredBalance)
    tryCount = 0
    result = None
    while tryCount < retryCount:
        logging.debug(f"Attempting verify unlocked balance is {requiredBalance} or higher.")
        result = mGetBalances()
        if 'Error' in result:
            return result
        balance = result['unlocked_balance']
        logging.debug(f"Unlocked balance was {atomicToMonero(balance)}.")
        if balance >= atomicRequiredBalance:
            return { "Balance" : balance }
        tryCount += 1
        time.sleep(waitSeconds)
    return {"Error": f"Could not verify unlocked balance was {requiredBalance} after {retryCount} tries.\n{result}"}

def mTransfer(address, amount):
    params = {
        'destinations': [{'amount': moneroToAtomic(amount), 'address': address}],
        'priority': 1,
        'unlock_time': 10
        }
    data = {
        'method': "transfer",
        'params': params
        }
    resp = tryParseResponse(postRequest(data))
    if 'Error' in resp:
        return resp

    return True
