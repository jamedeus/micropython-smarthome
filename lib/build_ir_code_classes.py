#!/usr/bin/env python3
'''
This script is called by firmware/build.sh, do not upload it to ESP32s.
Generates a mapping dict used to dynamically import IR Blaster code classes.
Output is frozen into firmware, automatically updates when metadata changes.
'''

import os
import json


def get_ir_code_classes():
    '''Iterates all modules in lib/ir_codes and builds a mapping dict with IR
    target names as keys, module containing key names and timings as values.
    Used by IrBlaster.py to determine the correct codes to import based target
    names in ir_blaster section of config file.
    '''
    output = {}

    # Resolve path to lib/ir_codes
    ir_codes_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'ir_codes'
    )

    # Add name of each target as key, name of module containing codes as value
    for i in os.listdir(ir_codes_path):
        if i.endswith('_ir_codes.py'):
            target_name = i.replace('_ir_codes.py', '')
            module_name = i.replace('.py', '')

            output[target_name] = module_name

    return output


if __name__ == '__main__':
    # Generate mapping dict
    ir_code_classes = get_ir_code_classes()

    # Create single-line python file with variable containing mapping dict
    output_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'ir_code_classes.py'
    )
    with open(output_path, 'w') as file:
        file.write(f'ir_code_classes = {json.dumps(ir_code_classes)}')
