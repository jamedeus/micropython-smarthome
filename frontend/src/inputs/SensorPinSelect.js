import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import { ConfigContext } from 'root/ConfigContext';
import PinSelectDropdown from './PinSelectDropdown';

const SensorPinSelect = ({ id }) => {
    // Get curent state + callback functions from context
    const { config, handleInputChange, highlightInvalid } = useContext(ConfigContext);

    // Skip if config section is empty
    if (!config[id]) {
        return null;
    }

    const sensorPins = [
        '4',
        '5',
        '13',
        '14',
        '15',
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
        '33',
        '34',
        '35',
        '36',
        '39'
    ];

    return (
        <PinSelectDropdown
            id={id}
            config={config}
            selected={config[id]["pin"]}
            onChange={(value) => handleInputChange(id, "pin", value)}
            options={sensorPins}
            isInvalid={(highlightInvalid && !config[id]["pin"])}
        />
    );
};

SensorPinSelect.propTypes = {
    id: PropTypes.string,
};

export default SensorPinSelect;
