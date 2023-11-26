import React, { useContext } from 'react';
import { ConfigContext } from './../ConfigContext';
import PinSelectDropdown from './PinSelectDropdown';


function DevicePinSelect({ id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

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
        />
    );
}

export default DevicePinSelect;
