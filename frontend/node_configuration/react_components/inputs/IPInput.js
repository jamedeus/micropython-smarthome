import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';

function IPInput({ id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    // Format IP address as user types in field
    const formatIp = (value) => {
        // Backspace and delete bypass formatting
        if (value.length < instance.ip.length) {
            handleInputChange(id, "ip", value);
            return;
        }

        // Remove everything except digits and period, 15 char max
        const input = value.replace(/[^\d.]/g, '').substring(0, 15);
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

        // Update state object
        handleInputChange(id, "ip", output);
    };

    return (
        <InputWrapper label="IP">
            <Form.Control
                type="text"
                value={instance.ip}
                pattern="^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
                onChange={(e) => formatIp(e.target.value)}
            />
        </InputWrapper>
    );
}

IPInput.propTypes = {
    id: PropTypes.string,
}

export default IPInput;
