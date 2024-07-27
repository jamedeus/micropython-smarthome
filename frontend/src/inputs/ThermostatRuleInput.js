import React from 'react';
import PropTypes from 'prop-types';
import RuleSlider from 'inputs/RuleSlider';
import { convert_temperature } from 'util/thermostat_util';

const ThermostatRuleInput = ({
    rule,
    setRule,
    min,
    max,
    displayMin=18,
    displayMax=27,
    scaleDisplayValue=false,
    units,
    sliderStep=0.1,
    onBlur=() => {}
}) => {
    return (
        <RuleSlider
            rule={rule}
            setRule={setRule}
            min={convert_temperature(min, "celsius", units)}
            max={convert_temperature(max, "celsius", units)}
            displayMin={displayMin}
            displayMax={displayMax}
            scaleDisplayValue={scaleDisplayValue}
            sliderStep={sliderStep}
            buttonStep={0.5}
            displayType={"float"}
            onBlur={onBlur}
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
    displayMin: PropTypes.number,
    displayMax: PropTypes.number,
    scaleDisplayValue: PropTypes.bool,
    units: PropTypes.oneOf([
        'celsius',
        'fahrenheit',
        'kelvin'
    ]).isRequired,
    sliderStep: PropTypes.number,
    onBlur: PropTypes.func
};

export default ThermostatRuleInput;
