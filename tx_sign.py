"""Prepare transaction on a network connected machine."""

import json
import argparse
import base64
import decimal

from ethereum import transactions as t
from ethereum import utils
from rlp.utils import decode_hex, encode_hex, str_to_bytes
import rlp

import getpass
import ethereum.keys as keys

parser = argparse.ArgumentParser()
parser.add_argument('--keytype', choices=['file', 'dongle'], default='file')
parser.add_argument('keyfile')
parser.add_argument('txfile')
args = parser.parse_args()

# Load unsigned transaction from file
tx_hex = open(args.txfile).read()
tx = rlp.decode(decode_hex(tx_hex[2:]), t.Transaction)

# Output some transaction information
print('======================================================')
print('Unsigned transaction is: ' + tx_hex)
print('======================================================')
print('Transaction amount (in wei): ' + str_to_bytes(str(tx.value)))
print('Transaction amount (in eth): ' + str_to_bytes(str(decimal.Decimal(tx.value)/10**18)))
print('                Destination: Ox' + encode_hex(tx.to))
print('======================================================')

# Using file wallet to sign transaction
if args.keytype == 'file':
    json = json.loads(open(args.keyfile).read())
    print("Enter password of keyfile or ctrl+c to cancel")
    pw = getpass.getpass()
    print("Applying hard key derivation function. Wait a little")
    k = keys.decode_keystore_json(json, pw)
    tx.sign(k)

# Using Ledger HW1 in DEV mode (SIGNVERIFY_IMMEDIATE)
if args.keytype == 'dongle':
    from btchip.btchip import getDongle, btchip
    from bitcoin import decode_sig as bitcoin_decode_sig
    dongle = getDongle(True)
    app = btchip(dongle)
    print("Enter pin of dongle or ctrl+c to cancel")
    pin = getpass.getpass('Pin:')
    app.verifyPin(pin)

    # Sign with dongle
    rawhash = utils.sha3(rlp.encode(tx, t.UnsignedTransaction))
    signature = app.signImmediate(bytearray(decode_hex(args.keyfile)), rawhash)

    # ASN.1 Decoding inspired from electrum
    rLength = signature[3]
    r = signature[4 : 4 + rLength]
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
    tx = t.Transaction(tx.nonce, tx.gasprice, tx.startgas, tx.to, tx.value, tx.data, v, r, s)

tx_hex = '0x' + encode_hex(rlp.encode(tx))
open(args.txfile + ".signed", 'w').write(tx_hex)
print('======================================================')
print('Signed transaction is: ' + tx_hex)
print('Signed transaction saved as file: ' + args.txfile + ".signed")
print('Transaction signed by: 0x' + encode_hex(tx.sender))
print('======================================================')
