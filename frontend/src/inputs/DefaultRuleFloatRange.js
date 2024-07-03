import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import { ConfigContext } from 'root/ConfigContext';
import { get_instance_metadata } from 'util/metadata';
import { average } from 'util/helper_functions';
import FloatRangeRuleInput from 'inputs/FloatRangeRuleInput';


function DefaultRuleFloatRange({ id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get instance section from config (state) object
    const instance = config[id];

    // Get metadata object for selected type (contains slider min/max)
    const category = id.replace(/[0-9]/g, '');
    const instanceMetadata = get_instance_metadata(category, instance._type);
    const min_rule = parseInt(instanceMetadata.rule_limits[0], 10);
    const max_rule = parseInt(instanceMetadata.rule_limits[1], 10);

    // Replace empty default_rule when new card added (causes NaN on slider)
    if (instance.default_rule === '') {
        instance.default_rule = average(min_rule, max_rule);
    }

    // Handler for slider move events
    const onSliderMove = (value) => {
        handleInputChange(id, "default_rule", value);
    };

    return (
        <div className="mb-2">
            <label className="w-100 fw-bold">
                Default Rule
            </label>
            <FloatRangeRuleInput
                rule={String(instance.default_rule)}
                setRule={onSliderMove}
                min={min_rule}
                max={max_rule}
            />
        </div>
    );
}

DefaultRuleFloatRange.propTypes = {
    id: PropTypes.string,
};

export default DefaultRuleFloatRange;
