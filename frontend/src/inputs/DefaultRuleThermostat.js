import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import { ConfigContext } from 'root/ConfigContext';
import { get_instance_metadata } from 'util/metadata';
import { average } from 'util/helper_functions';
import { convert_temperature } from 'util/thermostat_util';
import FloatRangeRuleInput from 'inputs/FloatRangeRuleInput';

const DefaultRuleThermostat = ({ id }) => {
    // Get instance section from config (state) object
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get instance section from config (state) object
    const instance = config[id];

    // Get metadata object for selected type (contains slider min/max)
    const category = id.replace(/[0-9]/g, '');
    const instanceMetadata = get_instance_metadata(category, instance._type);
    const min_rule = parseFloat(instanceMetadata.rule_limits[0], 10);
    const max_rule = parseFloat(instanceMetadata.rule_limits[1], 10);

    // Replace empty default_rule when new card added (causes NaN on slider)
    if (instance.default_rule === '') {
        instance.default_rule = average(min_rule, max_rule);
    }
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
    id: PropTypes.string,
};

export default DefaultRuleThermostat;
