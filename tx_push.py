"""
Send a transaction (generated offline) using your online machine.

This module enables you to take a file (or USB device) with a transaction
that was generated using the other scripts in this project and push it
to the ethereum network.

It is likely the third script you need to run if generating a new transaction.

Example:
    ::
        $ python tx_push.py ethoff.tx.signed

"""
import argparse
import json

from ethereum.transactions import Transaction
from rlp.utils import decode_hex
from rlp import decode
from web3 import Web3, RPCProvider

parser = argparse.ArgumentParser()
parser.add_argument('txfile')
parser.add_argument('--host', default="localhost")
parser.add_argument('--port', default="8545")
args = parser.parse_args()

web3 = Web3(RPCProvider(host=args.host, port=args.port))

tx_hex_signed = open(args.txfile).read()
tx = decode(decode_hex(tx_hex_signed[2:]), Transaction)

# Output some transaction information
print('======================================================')
print('Signed transaction: ' + tx_hex_signed)
print('======================================================')
print('                        Gas: ' + str(tx.startgas))
print('                  Gas Price: ' + str(tx.gasprice))
print('Transaction amount (in wei): ' + str(tx.value))
print('Transaction amount (in eth): ' + str(web3.fromWei(tx.value, 'ether')))
print('               From Address: ' + web3.toHex(tx.sender))
print('                 From Nonce: ' + str(tx.nonce))
print('                 To Address: ' + web3.toHex(tx.to))
print('           Transaction Data: ' + web3.toHex(tx.data))
print('======================================================')

input('Push transaction ? (Ctrl+c to cancel) ')

tx_id = web3.eth.sendRawTransaction(tx_hex_signed)
print('           Transaction Hash: ' + tx_id)
