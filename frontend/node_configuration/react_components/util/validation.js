// Format IP address as user types in field
const formatIp = (oldIP, newIP) => {
    // Backspace and delete bypass formatting
    if (newIP.length < oldIP.length) {
        return newIP;
    }

    // Remove everything except digits and period, 15 char max
    const input = newIP.replace(/[^\d.]/g, '').substring(0, 15);
    let output = '';
    let block = '';

    // Iterate input and format character by character
    for (let i = 0; i < input.length; i++) {
        const char = input[i];

        // Delimiter character handling
        if (char === '.') {
            // Drop if first char is delim, otherwise add to end of current block + start new block
            if (block.length > 0) {
                output += block + '.';
                block = '';
            }

            // Numeric character handling
        } else {
            // Add to current block
            block += char;
            // If current block reached limit, add to output + start new block
            if (block.length === 3) {
                output += block + '.';
                block = '';
            }
        }
    }

    // Add final block
    output += block;

    // Prevent >4 blocks (char limit may not be reached if single-digit blocks present)
    output = output.split('.').slice(0, 4).join('.');

    // Return formatted IP
    return output;
};

export { formatIp };
