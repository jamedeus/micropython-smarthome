#!/usr/bin/python3

# Tool for converting IR hex codes to array of pulse/space durations (microseconds).
# Address, start pulse, and end pulse are added automatically.
#
# Hex codes can be recorded from any remote using LIRC + IR receiver on a raspberry pi.
# Record each key and pass the hex code to this script as an argument.
#
# See lib/samsung-codes.json for example output.

# Usage: To convert the code 0x40BF:
# ./convert-ir-codes.py 40 BF
#
# Output:
# [4500, 4500, 547, 1687, 547, 1687, 547, 1687, 547, 567, 547, 567, 547, 567, 547, 567, 547, 567, 547,
# 1687, 547, 1687, 547, 1687, 547, 567, 547, 567, 547, 567, 547, 567, 547, 567, 547, 567, 547, 1687,
# 547, 567, 547, 567, 547, 567, 547, 567, 547, 567, 547, 567, 547, 1687, 547, 567, 547, 1687, 547,
# 1687, 547, 1687, 547, 1687, 547, 1687, 547, 1687, 545]

from sys import argv

# Samsung hex address
address = 0xe0

# Hex code, inverse hex code
code = int("0x" + argv[1], 16)
inverse_code = int("0x" + argv[2], 16)


# Takes hex int as arg
def convert(code):
    if not type(code) == int:
        print(f"ERROR: Must be int, received {type(code)}")
        return False

    # Convert to binary string, keep leading 0s
    binary = format(code, "08b")

    pulses = []

    for i in binary:
        # Pulse is always same length
        pulses.append(547)

        # Data is encoded in space length
        if i == "1":
            pulses.append(1687)
        elif i == "0":
            pulses.append(567)

    return pulses


# Create array with starting pulse/space (4.5ms each)
result = [4500, 4500]

# Convert address
adr = convert(address)

# Address is sent twice (first 2 bytes)
result.extend(adr)
result.extend(adr)

# Add command (3rd byte)
result.extend(convert(code))

# Add inverse command (4th byte)
result.extend(convert(inverse_code))

# Add end pulse
result.append(545)

print(result)
