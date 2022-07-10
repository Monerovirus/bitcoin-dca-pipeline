import math, os, sys, logging
import json_io
from kraken_tasks import kMarketPrice, kCreateMarketBuyOrder, kVerifyBalance, kWithdrawCrypto
from monero_rpc_tasks import mVerifyBalance, mTransfer
from fixedfloat_tasks import ffCreateFloatOrder, ffVerifyOrderComplete
#from history_tasks import writeHistory

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__)) + "/"

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.FileHandler(SCRIPT_PATH + 'log.txt', 'w', 'utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(handler)
logger.addHandler(logging.StreamHandler(sys.stdout))

def succeeded(data):
    if "Error" in data and data["Error"] != None:
        logging.error(data["Error"])
        return False
    return True

def runTasks(amount):
    settings = json_io.getJsonFile("settings.json")
    krakenCrypto = settings['kraken_crypto']
    fixedfloatFromCrypto = settings['fixedfloat_from_crypto']
    fixedfloatToCrypto = settings['fixedfloat_to_crypto']
    finalCryptoAddress = setting['final_crypto_address_key']
    fiat = settings['kraken_fiat']

    pair = krakenCrypto + fiat

    # get the crypto price
    result = kMarketPrice(pair)
    if not succeeded(result):
        return

    volume = amount / float(result)

    # create an order for the crypto
    result = kCreateMarketBuyOrder(krakenCrypto, fiat, volume)
    if not succeeded(result):
        return

    # verify the order went through (1 minute intervals, 30 attempts)
    result = kVerifyBalance(krakenCrypto, volume - 0.001, 30, 60)
    if not succeeded(result):
        return

    tCryptoBalance = result["Balance"]

    # withdraw the crypto to transitory wallet
    result = kWithdrawCrypto(krakenCrypto, tCryptoBalance, settings['transfer_crypto_address_key'])
    if not succeeded(result):
        return

    # verify the crypto made it to the wallet (1 minute intervals, 30 attempts)
    result = mVerifyBalance(tCryptoBalance - 0.001, 30, 60)
    if not succeeded(result):
        return

    mBalance = float(result['Balance'])

    # create a fixedfloat order
    ffOrderData = ffCreateFloatOrder(fixedfloatFromCrypto, fixedFloatToCrypto, mBalance, finalCryptoAddress)
    if not succeeded(ffOrderData):
        return

    ffOrderId = ffOrderData['id']
    ffOrderToken = ffOrderData['token']
    ffOrderAddress = ffOrderData['from']['address']

    # transfer to fixedfloat
    result = mTransfer(fixedfloatAddress, mBalance)
    if not succeeded(result):
        return

    # wait for fixedfloat order to complete (1 minute intervals, 30 attempts)
    result = ffVerifyOrderComplete(ffOrderId, ffOrderToken, 30, 60)
    if not succeeded(result):
        return

    logging.info("Finished tasks successfully.")
    return

#start
if len(sys.argv) != 2:
    print("Usage: python dca_pipeline.py [fiat amount]")
else:
    try:
        runTasks(int(sys.argv[1]))
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}.")
