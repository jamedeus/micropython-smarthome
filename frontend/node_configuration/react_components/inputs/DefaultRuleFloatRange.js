import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import { ConfigContext } from './../ConfigContext';
import { get_instance_metadata } from './../metadata';
import RuleSlider from './RuleSlider';


// Takes 2 numbers (int, float, or string) and returns average
function average(a, b) {
    try {
        return parseInt((parseFloat(a) + parseFloat(b)) / 2);
    } catch(err) {
        console.log(err);
    }
}


function DefaultRuleFloatRange({ id }) {
    // Get curent state + callback functions from context
    const { config, handleSliderButton, handleInputChange } = useContext(ConfigContext);

    // Get instance section from config (state) object
    const instance = config[id];

    // Get metadata object for selected type (contains slider min/max)
    const category = id.replace(/[0-9]/g, '');
    const instanceMetadata = get_instance_metadata(category, instance._type);
    const min_rule = parseInt(instanceMetadata.rule_limits[0], 10);
    const max_rule = parseInt(instanceMetadata.rule_limits[1], 10);

    // Replace empty default_rule when new card added (causes NaN on slider)
    if (!instance.default_rule) {
        instance.default_rule = average(min_rule, max_rule);
    }

    // Handler for slider + and - buttons
    const onButtonClick = (step, direction, min_rule, max_rule) => {
        handleSliderButton(id, step, direction, min_rule, max_rule);
    };

    // Handler for slider move events
    const onSliderMove = (value) => {
        handleInputChange(id, "default_rule", value);
    };

    return (
        <div className="mb-2">
            <label className="w-100"><b>Default Rule</b></label>
            <RuleSlider
                rule_value={instance.default_rule}
                slider_min={min_rule}
                slider_max={max_rule}
                slider_step={0.5}
                button_step={0.5}
                display_type={"float"}
                onButtonClick={onButtonClick}
                onSliderMove={onSliderMove}
            />
        </div>
    );
}

DefaultRuleFloatRange.propTypes = {
    id: PropTypes.string,
}

export default DefaultRuleFloatRange;
