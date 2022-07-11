import math, os, sys, logging
import json_io
from kraken_tasks import kMarketPrice, kCreateMarketBuyOrder, kVerifyOrder, kWithdrawCrypto
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
    finalCryptoAddress = settings['final_crypto_address']
    fiat = settings['kraken_fiat']

    pair = krakenCrypto + fiat

    # get the crypto price
    result = kMarketPrice(pair)
    if not succeeded(result):
        return

    logging.info(f"Price of {krakenCrypto} is {result}{fiat}.")

    volume = amount / float(result)

    # create an order for the crypto
    logging.info(f"Attempting to buy {volume} {krakenCrypto}.")
    result = kCreateMarketBuyOrder(krakenCrypto, fiat, volume)
    if not succeeded(result):
        return

    # verify the order went through (1 minute intervals, 20 attempts)
    logging.info(f"Verifying order...")
    result = kVerifyOrder(result, 20, 60)
    if not succeeded(result):
        return

    volume = float(result["vol_exec"])
    logging.info(f"Successfully purchased {volume} {krakenCrypto}.")

    # withdraw the crypto to transitory wallet
    logging.info(f"Attempting to withdraw {volume} {krakenCrypto}.")
    result = kWithdrawCrypto(krakenCrypto, volume, settings['transfer_crypto_address_key'])
    if not succeeded(result):
        return

    # verify the crypto made it to the wallet (2 minute intervals, 60 attempts)
    logging.info(f"Verifying deposit...")
    result = mVerifyBalance(volume - 0.001, 60, 120)
    if not succeeded(result):
        return

    mBalance = float(result['Balance'])
    logging.info(f"Successfully deposited {volume} {krakenCrypto}, {mBalance} {krakenCrypto} available in wallet.")

    # create a fixedfloat order
    logging.info("Opening an order on FixedFloat.")
    ffOrderAmount = mBalance - 0.01 # accounting for transfer fee
    ffOrderData = ffCreateFloatOrder(fixedfloatFromCrypto, fixedFloatToCrypto, ffOrderAmount, finalCryptoAddress)
    if not succeeded(ffOrderData):
        return

    ffOrderId = ffOrderData['id']
    ffOrderToken = ffOrderData['token']
    ffOrderAddress = ffOrderData['from']['address']

    logging.info(f"Order {ffOrderId} created.")

    # transfer to fixedfloat
    logging.info(f"Transferring {ffOrderAmount} to FixedFloat.")
    result = mTransfer(fixedfloatAddress, ffOrderAmount)
    if not succeeded(result):
        return

    # wait for fixedfloat order to complete (1 minute intervals, 30 attempts)
    logging.info("Verifying order...")
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
