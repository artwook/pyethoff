"""Send a transaction (generated offline) using your online machine.

This module enables you to take a file (or USB device) with a transaction
that was generated using the other scripts in this project and push it
to the ethereum network.

It is likely the third script you need to run if generating a new transaction.

Example:
    ::
        $ python tx_push.py ethoff.tx.signed

Attributes:
    parser (argpase.ArgumentParser): Helper to provide CLI.
    tx_hex_signed (bytes): Signed transaction in hex.
    tx (ethereum.transactions.Transaction): Object to build signed transaction.
    tx_wei (bytes): Transaction ammount in wei.
    tx_eth (bytes): Transaction ammount in eth.
"""
import argparse
from decimal import Decimal
import json

# import requests
from ethereum.transactions import Transaction
from rlp.utils import decode_hex, encode_hex, str_to_bytes
from rlp import decode

parser = argparse.ArgumentParser()
parser.add_argument('txfile')
parser.add_argument('--geth_rpc', default='http://localhost:8545')
args = parser.parse_args()

tx_hex_signed = open(args.txfile).read()
tx = decode(decode_hex(tx_hex_signed[2:]), Transaction)
tx_wei = str_to_bytes(str(tx.value))
tx_eth = str_to_bytes(str(Decimal(tx.value) / 10**18))

payload = {
    'jsonrpc': '2.0',
    'method': 'eth_sendRawTransaction',
    'params': [tx_hex_signed],
    'id': 67
}

# Output some transaction information
print('======================================================')
print('Signed transaction: ' + tx_hex_signed)
print('======================================================')
print('                  Signed By: 0x' + encode_hex(tx.sender))
print('Transaction amount (in wei): ' + tx_wei)
print('Transaction amount (in eth): ' + tx_eth)
print('                Destination: Ox' + encode_hex(tx.to))
print('======================================================')
print('Copy&paste: curl -X POST --data \'' + json.dumps(payload) + '\' ' + args.geth_rpc)
