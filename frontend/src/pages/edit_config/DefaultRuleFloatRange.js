import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import { EditConfigContext } from 'root/EditConfigContext';
import FloatRangeRuleInput from 'inputs/FloatRangeRuleInput';

const DefaultRuleFloatRange = ({ id, instance, metadata }) => {
    const { handleInputChange } = useContext(EditConfigContext);

    // Get slider limits from metadata object
    const min_rule = parseInt(metadata.rule_limits[0], 10);
    const max_rule = parseInt(metadata.rule_limits[1], 10);

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
};

DefaultRuleFloatRange.propTypes = {
    id: PropTypes.string.isRequired,
    instance: PropTypes.object.isRequired,
    metadata: PropTypes.object.isRequired
};

export default DefaultRuleFloatRange;
