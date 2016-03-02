import argparse
import decimal

import requests
from ethereum import transactions as t
from rlp.utils import decode_hex, encode_hex, str_to_bytes
import rlp

parser = argparse.ArgumentParser()
parser.add_argument('txfile')
parser.add_argument('--geth_rpc', default="http://localhost:8545")
args = parser.parse_args()

tx_hex = open(args.txfile).read()
tx = rlp.decode(decode_hex(tx_hex[2:]), t.Transaction)

# Output some transaction information
print('======================================================')
print('Signed transaction: ' + tx_hex)
print('======================================================')
print('                  Signed By: 0x' + encode_hex(tx.sender))
print('Transaction amount (in wei): ' + str_to_bytes(str(tx.value)))
print('Transaction amount (in eth): ' + str_to_bytes(str(decimal.Decimal(tx.value)/10**18)))
print('                Destination: Ox' + encode_hex(tx.to))
print('======================================================')
print('Copy and paste : curl -X POST --data \'{"jsonrpc":"2.0","method":"eth_sendRawTransaction","params":["' + tx_hex + '"],"id":67}\' ' + args.geth_rpc)
