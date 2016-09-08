"""
Produce an encoded function call to pass as data in a transaction

ex. python fn_prepare.py erc20.json approve "0x0123456789abcdef000000000000000000000001 int:5"
"""
import argparse
import json

from ethereum import abi as eth_abi
from web3 import Web3

parser = argparse.ArgumentParser()
parser.add_argument('abi_json_file')
parser.add_argument('method')
parser.add_argument('args_string')
args = parser.parse_args()

abi = json.load(open(args.abi_json_file))
web3 = Web3(None) # web3 init without provider
contract = eth_abi.ContractTranslator(abi)

params = []
for p in args.args_string.split():
    if p[:2] == '0x':
        if not web3.isAddress(p):
            raise Exception('Invalid address %s' % p)
        params.append(web3.toAscii(p))
    elif p[:4] == 'int:':
        params.append(int(p[4:]))
    elif p[:5] == 'bool:':
        params.append(bool(p[5:].lower()=='true'))
    else:
        params.append(p)
tx_data = contract.encode_function_call(args.method, params)

# Output some transaction information
print('======================================================')
print('                     Method: ' + str(args.method))
print('                  Arguments: ' + str(args.args_string))
print('           Transaction Data: ' + web3.toHex(tx_data))
print('======================================================')
