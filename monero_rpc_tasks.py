import urllib.parse, requests, time, logging
import json_io
from simplejson.errors import JSONDecodeError

API_URL = "http://localhost:28088/json_rpc"

def tryParseResponse(resp):
    try:
        return resp.json()
    except JSONDecodeError as e:
        logging.error(f"Failed to parse monero-rpc response: {resp}")
        return False

def mPostRequest(data):
    data['jsonrpc'] = "2.0"
    data['id'] = "0"
    headers = {}
    headers['Content-Type'] = "application/json"
    return requests.post(API_URL, headers=headers, data=data)

def mGetBalances(asset):
    data = {'method': "get_accounts"}
    resp = tryParseResponse(mPostRequest(data))
    if resp == False:
        return {"Error": "Failed to parse monero-rpc response."}

    return {"balance": resp['result']['total_balance'], "unlocked_balance": resp['result']['total_unlocked_balance']}