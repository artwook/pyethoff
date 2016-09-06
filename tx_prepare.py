"""Prepare an ethereum transaction on a network connected machine.

This module enables you to create a transaction that can then be transferred
to an offline machine which has your ethereum wallet safely stored offline.

It is the first script you need to run if you are creating a new transaction.

Example:
    ::
        $ python tx_prepare.py --ether 2.5 <from> <to>

Attributes:
    parser (argpase.ArgumentParser): Helper to provide CLI.
    nonce_payload (dict): Request body when fetching nonce from blockchain.
    nonce_response (requests.Response): Response object for nonce request.
    tx_count (int): Number of previous transactions from sender wallet (nonce).
    gas_payload (dict): Request body when fetching gas from blockchain.
    gas_response (requests.Response): Response object for gas request.
    tx_gasprice (int): Current gas price fetched from blockchain.
    tx (ethereum.transactions.Transaction): Object to build transaction.
    tx_wei (bytes): Transaction ammount in wei.
    tx_eth (bytes): Transaction ammount in eth.
    tx_hex (bytes): Unsigned transaction in hex.
"""
import argparse
from decimal import Decimal
import json

from ethereum.transactions import Transaction
import requests
from rlp import encode
from rlp.utils import decode_hex, encode_hex, str_to_bytes

parser = argparse.ArgumentParser()
parser.add_argument('amount')
parser.add_argument('from_addr')
parser.add_argument('to_addr')
parser.add_argument('--geth_rpc', default="http://localhost:8545")
parser.add_argument('--output', default="ethoff.tx")
parser.add_argument('--ether', default=False, action='store_true')
parser.add_argument('--nonce', default=-1, type=int)
parser.add_argument('--gas', default=21000, type=int)
parser.add_argument('--data', default='')
args = parser.parse_args()

# Fetch nonce from the blockchain
if args.nonce < 0:
    nonce_payload = {
        'jsonrpc': '2.0',
        'method': 'eth_getTransactionCount',
        'params': [args.from_addr, 'latest'],
        'id': 1
    }
    nonce_response = requests.post(
        args.geth_rpc,
        data=json.dumps(nonce_payload)
    )

    tx_count = int(nonce_response.json()[u'result'], 16)
else:
    tx_count = args.nonce

# Fetch gasprice from the blockchain
gas_payload = {
    'jsonrpc': '2.0',
    'method': 'eth_gasPrice',
    'params': [],
    'id': 73
}
gas_response = requests.post(
    args.geth_rpc,
    data=json.dumps(gas_payload)
)
tx_gasprice = int(gas_response.json()[u'result'], 16)

if args.ether:
    amount = Decimal(args.amount) * 10**18
else:
    amount = Decimal(args.amount)

# Creation transaction, value in wei
tx = Transaction(
    nonce=tx_count,
    gasprice=tx_gasprice,
    startgas=args.gas,
    to=decode_hex(args.to_addr[2:]),
    value=int(amount),
    data=decode_hex(args.data[2:])
)
tx_wei = str_to_bytes(str(tx.value))
tx_eth = str_to_bytes(str(Decimal(tx.value) / 10**18))

# Output some transaction information
print('======================================================')
print('                  Gas Price: ' + str(tx_gasprice))
print('Transaction amount (in wei): ' + tx_wei)
print('Transaction amount (in eth): ' + tx_eth)
print('                       From: ' + args.from_addr)
print('                 From Nonce: ' + str(tx_count))
print('                Destination: Ox' + encode_hex(tx.to))
print('======================================================')

# Write unsigned transaction to file
tx_hex = '0x' + encode_hex(encode(tx))
open(args.output, 'w').write(tx_hex)
print('Unsigned transaction saved as file: ' + args.output)
print('Unsigned transaction is: ' + tx_hex)
print('======================================================')
