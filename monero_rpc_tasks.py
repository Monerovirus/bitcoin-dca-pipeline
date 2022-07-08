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

def mPostRequest(data):
    data['jsonrpc'] = "2.0"
    data['id'] = "0"
    return requests.post(API_URL, data=json.dumps(data))

def mGetBalances():
    data = {'method': "get_accounts"}
    resp = tryParseResponse(mPostRequest(data))
    if 'Error' in resp:
        return resp

    return {"balance": resp['result']['total_balance'], "unlocked_balance": resp['result']['total_unlocked_balance']}

def mTransfer(address, atomicAmount):
    params = {
        'destinations': [{'amount': atomicAmount, 'address': address}],
        'priority': 1,
        'unlock_time': 10
        }
    data = {
        'method': "transfer",
        'params': params
        }
    resp = tryParseResponse(mPostRequest(data))
    if 'Error' in resp:
        return resp

    return True
