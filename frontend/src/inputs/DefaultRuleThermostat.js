import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import { ConfigContext } from 'root/ConfigContext';
import { convert_temperature } from 'util/thermostat_util';
import FloatRangeRuleInput from 'inputs/FloatRangeRuleInput';

const DefaultRuleThermostat = ({ id, instance, metadata }) => {
    const { handleInputChange } = useContext(ConfigContext);

    // Get slider limits from metadata object
    const min_rule = parseFloat(metadata.rule_limits[0], 10);
    const max_rule = parseFloat(metadata.rule_limits[1], 10);

    // Handler for slider move events
    const onSliderMove = (value) => {
        handleInputChange(id, "default_rule", value);
    };

    // Instantiate slider, convert metadata min/max (celsius) to configured units
    return (
        <div className="mb-2">
            <label className="w-100 fw-bold">
                Default Rule
            </label>
            <FloatRangeRuleInput
                rule={String(instance.default_rule)}
                setRule={onSliderMove}
                min={convert_temperature(min_rule, "celsius", instance.units)}
                max={convert_temperature(max_rule, "celsius", instance.units)}
                sliderStep={0.1}
            />
        </div>
    );
};

DefaultRuleThermostat.propTypes = {
    id: PropTypes.string.isRequired,
    instance: PropTypes.object.isRequired,
    metadata: PropTypes.object.isRequired
};

export default DefaultRuleThermostat;
