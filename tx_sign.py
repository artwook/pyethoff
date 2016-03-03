"""Sign a transaction (generated online) using your offline machine.

This module enables you to sign a transaction created offline using tx_prepare
it should be run on your offline machine (the one that has your keys on). You
will then need to transfer this signed transaction back to your online machine.

It is likely the second script you need to run if generating a new transaction.

Example:
    ::
        $ python tx_sign.py <path to wallet> ethoff.tx

Attributes:
    parser (argpase.ArgumentParser): Helper to provide CLI.
    tx_hex (bytes): Unsigned transaction in hex.
    tx (ethereum.transactions.Transaction): Object to build signed transaction.
    tx_wei (bytes): Transaction ammount in wei.
    tx_eth (bytes): Transaction ammount in eth.
    tx_hex_signed (bytes): Signed transaction in hex.
"""
import argparse
import base64
from decimal import Decimal
from getpass import getpass
import json

from ethereum.keys import decode_keystore_json
from ethereum.transactions import Transaction, UnsignedTransaction
from ethereum.utils import sha3
from rlp.utils import decode_hex, encode_hex, str_to_bytes
from rlp import encode, decode

parser = argparse.ArgumentParser()
parser.add_argument('--keytype', choices=['file', 'dongle'], default='file')
parser.add_argument('keyfile')
parser.add_argument('txfile')
args = parser.parse_args()

# Load unsigned transaction from file
tx_hex = open(args.txfile).read()
tx = decode(decode_hex(tx_hex[2:]), Transaction)
tx_wei = str_to_bytes(str(tx.value))
tx_eth = str_to_bytes(str(Decimal(tx.value) / 10**18))

# Output some transaction information
print('======================================================')
print('Unsigned transaction is: ' + tx_hex)
print('======================================================')
print('Transaction amount (in wei): ' + tx_wei)
print('Transaction amount (in eth): ' + tx_eth)
print('              Destination: Ox' + encode_hex(tx.to))
print('======================================================')

# Using file wallet to sign transaction
if args.keytype == 'file':
    json = json.loads(open(args.keyfile).read())
    print("Enter password of keyfile or ctrl+c to cancel")
    pw = getpass()
    print("Applying hard key derivation function. Wait a little")
    k = decode_keystore_json(json, pw)
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

tx_hex_signed = '0x' + encode_hex(encode(tx))
open(args.txfile + ".signed", 'w').write(tx_hex_signed)
print('======================================================')
print('Signed transaction is: ' + tx_hex_signed)
print('Signed transaction saved as file: ' + args.txfile + ".signed")
print('Transaction signed by: 0x' + encode_hex(tx.sender))
print('======================================================')
