import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import { ConfigContext } from 'root/ConfigContext';
import PinSelectDropdown from './PinSelectDropdown';

function DevicePinSelect({ id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange, highlightInvalid } = useContext(ConfigContext);

    // Skip if config section is empty
    if (!config[id]) {
        return null;
    }

    const devicePins = [
        '4',
        '13',
        '16',
        '17',
        '18',
        '19',
        '21',
        '22',
        '23',
        '25',
        '26',
        '27',
        '32',
        '33'
    ];

    return (
        <PinSelectDropdown
            id={id}
            config={config}
            selected={config[id]["pin"]}
            onChange={(value) => handleInputChange(id, "pin", value)}
            options={devicePins}
            isInvalid={(highlightInvalid && !config[id]["pin"])}
        />
    );
}

DevicePinSelect.propTypes = {
    id: PropTypes.string,
};

export default DevicePinSelect;
