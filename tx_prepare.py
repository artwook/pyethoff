"""
Prepare an ethereum transaction on a network connected machine.

This module enables you to create a transaction that can then be transferred
to an offline machine which has your ethereum wallet safely stored offline.

It is the first script you need to run if you are creating a new transaction.

Example:
    ::
        $ python tx_prepare.py --ether 2.5 <from> <to>

"""
import argparse

from ethereum.transactions import Transaction
from rlp import encode
from web3 import Web3, RPCProvider

parser = argparse.ArgumentParser()
parser.add_argument('amount')
parser.add_argument('from_addr')
parser.add_argument('to_addr')
parser.add_argument('--host', default="localhost")
parser.add_argument('--port', default="8545")
parser.add_argument('--output', default="ethoff.tx")
parser.add_argument('--ether', default=False, action='store_true')
parser.add_argument('--nonce', default=-1, type=int)
parser.add_argument('--gas', type=int)
parser.add_argument('--data', default='')
args = parser.parse_args()

web3 = Web3(RPCProvider(host=args.host, port=args.port))

# Check address validity
if not web3.isAddress(args.from_addr):
    raise Exception('Invalid address %s' % args.from_addr)
if not web3.isAddress(args.to_addr):
    raise Exception('Invalid address %s' % args.to_addr)

# Fetch nonce from the blockchain
if args.nonce < 0:
    tx_count = web3.eth.getTransactionCount(args.from_addr)
else:
    tx_count = args.nonce

# Fetch gasprice from the blockchain
tx_gasprice = web3.eth.gasPrice

if args.ether:
    amount = web3.toWei(args.amount, 'ether')
else:
    amount = args.amount

# Estimate startgas if necessary
if args.gas:
    tx_startgas = args.gas
elif args.data != '' :
    tx_startgas = web3.eth.estimateGas({
        'to': args.to_addr,
        'from': args.from_addr,
        'value': amount,
        'data': args.data,
    })
else:
    tx_startgas = 21000

# Create transaction, value in wei
tx = Transaction(
    nonce=tx_count,
    gasprice=tx_gasprice,
    startgas=tx_startgas,
    to=web3.toAscii(args.to_addr),
    value=int(amount),
    data=web3.toAscii(args.data)
)

# Output some transaction information
print('======================================================')
print('                        Gas: ' + str(tx.startgas))
print('                  Gas Price: ' + str(tx.gasprice))
print('Transaction amount (in wei): ' + str(tx.value))
print('Transaction amount (in eth): ' + str(web3.fromWei(tx.value, 'ether')))
print('               From Address: ' + args.from_addr)
print('                 From Nonce: ' + str(tx.nonce))
print('                 To Address: ' + web3.toHex(tx.to))
print('           Transaction Data: ' + web3.toHex(tx.data))
print('======================================================')

# Write unsigned transaction to file
tx_hex = web3.toHex(encode(tx))
open(args.output, 'w').write(tx_hex)
print('Unsigned transaction saved as file: ' + args.output)
print('Unsigned transaction is: ' + tx_hex)
print('======================================================')
