"""
Prepare an ethereum transaction on a network connected machine.

This module enables you to create a transaction that can then be transferred
to an offline machine which has your ethereum wallet safely stored offline.

It is the first script you need to run if you are creating a new transaction.

Examples:
    ::
        $ python tx_prepare.py --ether 2.5 <from> <to>
        $ python tx_prepare.py --keytype nanos max "44'/60'/0'/0" <to>
        $ python tx_prepare.py --keytype nanos max "44'/60'/160720'/0'/0" <to>

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
parser.add_argument('--keytype', choices=['file', 'nanos'], default='file')
args = parser.parse_args()

web3 = Web3(RPCProvider(host=args.host, port=args.port))

if args.keytype == 'nanos':
    # Fetch public address from nanos
    from ledgerblue.comm import getDongle
    import struct

    path = args.from_addr
    donglePath = b''
    for pathElement in path.split('/'):
        element = pathElement.split('\'')
        if len(element) == 1:
            donglePath += struct.pack(">I", int(element[0]))
        else:
            donglePath += struct.pack(">I", 0x80000000 | int(element[0]))
    apdu =  bytes.fromhex('e0020000')
    apdu += bytes([len(donglePath) + 1])
    apdu += bytes([len(donglePath) // 4])
    apdu += donglePath

    result = getDongle(True).exchange(apdu)
    offset = 1 + result[0]
    address = result[offset + 1 : offset + 1 + result[offset]]
    from_addr = "0x" + str(address.decode('ascii')).lower()

if args.keytype == 'file':
    from_addr = args.from_addr

# Check address validity
if not web3.isAddress(from_addr):
    raise Exception('Invalid address %s' % from_addr)
if not web3.isAddress(args.to_addr):
    raise Exception('Invalid address %s' % args.to_addr)

# Fetch nonce from the blockchain
if args.nonce < 0:
    tx_count = web3.eth.getTransactionCount(from_addr)
else:
    tx_count = args.nonce

# Fetch gasprice from the blockchain
tx_gasprice = web3.eth.gasPrice

# Check if amount is max
if args.amount == 'max':
    amount = web3.eth.getBalance(from_addr)
else:
    if args.ether:
        amount = web3.toWei(args.amount, 'ether')
    else:
        amount = int(args.amount)

# Estimate startgas if necessary
if args.gas:
    tx_startgas = args.gas
elif args.data != '' :
    tx_startgas = web3.eth.estimateGas({
        'to': args.to_addr,
        'from': from_addr,
        'value': amount,
        'data': args.data,
    })
else:
    tx_startgas = 21000

# If amount is max, deduce transaction fee
if args.amount == 'max':
    amount -= tx_gasprice * tx_startgas

if amount < 0:
    raise Exception('Not enought fund at address %s' % from_addr)

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
print('               From Address: ' + from_addr)
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
