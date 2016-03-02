import json
import argparse
import decimal

import requests
import json
from ethereum import transactions as t
from rlp.utils import decode_hex, encode_hex, str_to_bytes
import rlp

parser = argparse.ArgumentParser()
parser.add_argument('amount')
parser.add_argument('from_addr')
parser.add_argument('to_addr')
parser.add_argument('--geth_rpc', default="http://localhost:8545")
parser.add_argument('--output', default="ethoff.tx")
parser.add_argument('--ether', default=False, action='store_true')
args = parser.parse_args()

# Fetch nonce from the blockchain
r = requests.post(args.geth_rpc,data='{"jsonrpc":"2.0","method":"eth_getTransactionCount","params":["' + args.from_addr + '","latest"],"id":1}')
tx_count = int(r.json()[u'result'], 16)

# Fetch gasprice from the blockchain
r = requests.post(args.geth_rpc,data='{"jsonrpc":"2.0","method":"eth_gasPrice","params":[],"id":73}')
tx_gasprice = int(r.json()[u'result'], 16)

if args.ether:
    amount = decimal.Decimal(args.amount) * 10**18
else:
    amount = decimal.Decimal(args.amount)

# Creation transaction, value in wei
tx = t.Transaction(nonce=tx_count, gasprice=tx_gasprice, startgas=21000, to=decode_hex(args.to_addr[2:]), value=int(amount), data='')
tx_hex = '0x' + encode_hex(rlp.encode(tx))

# Output some transaction information
print('======================================================')
print('                  Gas Price: ' + str(tx_gasprice))
print('Transaction amount (in wei): ' + str_to_bytes(str(tx.value)))
print('Transaction amount (in eth): ' + str_to_bytes(str(decimal.Decimal(tx.value)/10**18)))
print('                       From: ' + args.from_addr)
print('                 From Nonce: ' + str(tx_count))
print('                Destination: Ox' + encode_hex(tx.to))
print('======================================================')

# Write unsigned transaction to file
open(args.output, 'w').write(tx_hex)
print('Unsigned transaction saved as file: ' + args.output)
print('Unsigned transaction is: ' + tx_hex)
print('======================================================')
