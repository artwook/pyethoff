"""
Produce an encoded function call to pass as data in a transaction

ex. python fn_prepare.py erc20.json approve "0x0123456789abcdef000000000000000000000001 int:5"
"""
import argparse
import json

from ethereum import abi
from rlp.utils import decode_hex, encode_hex, str_to_bytes

parser = argparse.ArgumentParser()
parser.add_argument('abi_json_file')
parser.add_argument('method')
parser.add_argument('args_string')
args = parser.parse_args()

abi_desc = json.load(open(args.abi_json_file))
contract = abi.ContractTranslator(abi_desc)

params = []
for p in args.args_string.split():
    if p[:2] == '0x':
        params.append(decode_hex(p[2:]))
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
print('           Transaction Data: 0x' + encode_hex(tx_data))
print('======================================================')
