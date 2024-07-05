import React from 'react';
import PropTypes from 'prop-types';
import RuleSlider from 'inputs/RuleSlider';
import { convert_temperature } from 'util/thermostat_util';

const ThermostatRuleInput = ({ rule, setRule, min, max, units, sliderStep=0.1 }) => {
    return (
        <RuleSlider
            rule={rule}
            setRule={setRule}
            min={convert_temperature(min, "celsius", units)}
            max={convert_temperature(max, "celsius", units)}
            sliderStep={sliderStep}
            buttonStep={0.5}
            displayType={"float"}
        />
    );
};

ThermostatRuleInput.propTypes = {
    rule: PropTypes.oneOfType([
        PropTypes.number,
        PropTypes.string
    ]).isRequired,
    setRule: PropTypes.func.isRequired,
    min: PropTypes.number.isRequired,
    max: PropTypes.number.isRequired,
    units: PropTypes.oneOf([
        'celsius',
        'fahrenheit',
        'kelvin'
    ]).isRequired,
    sliderStep: PropTypes.number
};

export default ThermostatRuleInput;
