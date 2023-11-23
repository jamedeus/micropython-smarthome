import React, { useContext } from 'react';
import Button from 'react-bootstrap/Button';
import { Range, getTrackBackground } from 'react-range';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';
import { get_instance_metadata } from './../metadata';
import RuleSlider from './RuleSlider';
import { average, convert_temperature } from './../thermostat_util';


function DefaultRuleThermostat({ key, id }) {
    // Get instance section from config (state) object
    const { config } = useContext(ConfigContext);
    const instance = config[id];

    // Get metadata object for selected type (contains slider min/max)
    const category = id.replace(/[0-9]/g, '');
    const instanceMetadata = get_instance_metadata(category, instance._type);
    const min_rule = parseFloat(instanceMetadata.rule_limits[0], 10);
    const max_rule = parseFloat(instanceMetadata.rule_limits[1], 10);

    // Replace empty default_rule when new card added (causes NaN on slider)
    if (!instance.default_rule) {
        instance.default_rule = average(min_rule, max_rule);
    };

    // Instantiate slider, convert metadata min/max (celsius) to configured units
    return (
        <RuleSlider
            key={key}
            id={id}
            rule_value={instance.default_rule}
            slider_min={convert_temperature(min_rule, "celsius", instance.units)}
            slider_max={convert_temperature(max_rule, "celsius", instance.units)}
            slider_step={0.1}
            button_step={0.5}
            display_type={"float"}
        />
    );
}

export default DefaultRuleThermostat;
