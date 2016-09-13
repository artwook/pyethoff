"""
Sign a transaction (generated online) using your offline machine.

This module enables you to sign a transaction created offline using tx_prepare
it should be run on your offline machine (the one that has your keys on). You
will then need to transfer this signed transaction back to your online machine.

It is likely the second script you need to run if generating a new transaction.

Example:
    ::
        $ python tx_sign.py <path to wallet> ethoff.tx
        $ python tx_sign.py --keytype nanos "44'/60'/0'/0" ethoff.tx
        $ python tx_sign.py --keytype nanos "44'/60'/160720'/0'/0" ethoff.tx

"""
import argparse
import base64
from getpass import getpass
import json

from ethereum.keys import decode_keystore_json
from ethereum.transactions import Transaction, UnsignedTransaction
from ethereum.utils import sha3
from rlp.utils import decode_hex
from rlp import encode, decode
from web3 import Web3

parser = argparse.ArgumentParser()
parser.add_argument('--keytype', choices=['file', 'dongle', 'nanos'], default='file')
parser.add_argument('keyfile')
parser.add_argument('txfile')
args = parser.parse_args()

web3 = Web3(None) # web3 init without provider

# Load unsigned transaction from file
tx_hex = open(args.txfile).read()
tx = decode(decode_hex(tx_hex[2:]), Transaction)

# Output some transaction information
print('======================================================')
print('Unsigned transaction is: ' + tx_hex)
print('======================================================')
print('                        Gas: ' + str(tx.startgas))
print('                  Gas Price: ' + str(tx.gasprice))
print('Transaction amount (in wei): ' + str(tx.value))
print('Transaction amount (in eth): ' + str(web3.fromWei(tx.value, 'ether')))
print('                 From Nonce: ' + str(tx.nonce))
print('                 To Address: ' + web3.toHex(tx.to))
print('           Transaction Data: ' + web3.toHex(tx.data))
print('======================================================')

# Using file wallet to sign transaction
if args.keytype == 'file':
    json = json.loads(open(args.keyfile).read())
    print("Enter password of keyfile or ctrl+c to cancel")
    pw = getpass()
    print("Applying hard key derivation function. Wait a little")
    k = decode_keystore_json(json, pw)

    # Prepare a new transaction (decoded transaction seems immutable...)
    tx = Transaction(
        tx.nonce, tx.gasprice, tx.startgas, tx.to, tx.value, tx.data
    )
    tx.sign(k)

# Using Ledger HW1 in DEV mode (SIGNVERIFY_IMMEDIATE)
if args.keytype == 'dongle':
    from btchip.btchip import getDongle, btchip
    from bitcoin import decode_sig as bitcoin_decode_sig
    dongle = getDongle(True)
    app = btchip(dongle)
    print("Enter pin of dongle or ctrl+c to cancel")
    pin = getpass('Pin:')
    app.verifyPin(pin)

    # Sign with dongle
    rawhash = sha3(encode(tx, UnsignedTransaction))
    signature = app.signImmediate(bytearray(decode_hex(args.keyfile)), rawhash)

    # ASN.1 Decoding inspired from electrum
    rLength = signature[3]
    r = signature[4: 4 + rLength]
    sLength = signature[4 + rLength + 1]
    s = signature[4 + rLength + 2:]
    if rLength == 33:
        r = r[1:]
    if sLength == 33:
        s = s[1:]
    r = str(r)
    s = str(s)
    sig = base64.b64encode(chr(27 + (signature[0] & 0x01)) + r + s)

    # Retrieve VRS from sig
    v, r, s = bitcoin_decode_sig(sig)

    # Build new transaction with valid sig
    tx = Transaction(
        tx.nonce, tx.gasprice, tx.startgas, tx.to, tx.value, tx.data, v, r, s
    )

# Using Ledger Nano S
if args.keytype == 'nanos':
    #TODO
    from ledgerblue.comm import getDongle
    import struct

    path = args.keyfile
    donglePath = b''
    for pathElement in path.split('/'):
        element = pathElement.split('\'')
        if len(element) == 1:
            donglePath += struct.pack(">I", int(element[0]))
        else:
            donglePath += struct.pack(">I", 0x80000000 | int(element[0]))

    encodedTx = encode(tx, UnsignedTransaction)

    apdu =  bytes.fromhex('e0040000')
    apdu += bytes([len(donglePath) + 1 + len(encodedTx)])
    apdu += bytes([len(donglePath) // 4])
    apdu += donglePath
    apdu += encodedTx

    # Sign with dongle
    result = getDongle(True).exchange(apdu, timeout=60)

    # Retrieve VRS from sig
    v = result[0]
    r = int.from_bytes(result[1:1 + 32], 'big')
    s = int.from_bytes(result[1 + 32: 1 + 32 + 32], 'big')

    # Build new transaction with valid sig
    tx = Transaction(
        tx.nonce, tx.gasprice, tx.startgas, tx.to, tx.value, tx.data, v, r, s
    )

tx_hex_signed = web3.toHex(encode(tx))
open(args.txfile + ".signed", 'w').write(tx_hex_signed)
print('======================================================')
print('Signed transaction is: ' + tx_hex_signed)
print('Signed transaction saved as file: ' + args.txfile + ".signed")
print('Transaction signed by: ' + web3.toHex(tx.sender))
print('======================================================')
