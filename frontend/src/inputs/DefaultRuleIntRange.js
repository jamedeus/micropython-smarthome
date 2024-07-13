import React, { useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import Collapse from 'react-bootstrap/Collapse';
import { ConfigContext } from 'root/ConfigContext';
import InputWrapper from './InputWrapper';
import IntRangeRuleInput from 'inputs/IntRangeRuleInput';

const DefaultRuleIntRange = ({ id, instance, metadata }) => {
    const { handleInstanceUpdate, handleInputChange } = useContext(ConfigContext);

    // Get slider limits from metadata object
    const metadata_min = parseInt(metadata.rule_limits[0], 10);
    const metadata_max = parseInt(metadata.rule_limits[1], 10);

    // Handler for slider move events
    const onSliderMove = (value) => {
        handleInputChange(id, "default_rule", value);
    };

    // Handler for rule limit inputs
    const setRuleLimits = (param, value) => {
        // Remove non-numeric characters, cast to int
        value = parseInt(value.replace(/[^0-9.]/g, ''));
        // Default to 1 when input is completely empty
        if (isNaN(value)) {
            value = 1;
        }

        // Enforce absolute rule limits
        value = Math.max(metadata_min, Math.min(value, metadata_max));

        // Copy state object, add new limit
        const update = { ...instance, [param]: value };

        // Prevent max lower than min, min higher than max, default_rule out of range
        if (param === "min_rule") {
            update.max_rule = Math.max(update.max_rule, value);
            update.default_rule = Math.max(update.default_rule, value);
        } else if (param === "max_rule") {
            update.min_rule = Math.min(update.min_rule, value);
            update.default_rule = Math.min(update.default_rule, value);
        }

        handleInstanceUpdate(id, update);
    };

    // Set default state for advanced settings collapse
    const [open, setOpen] = useState(false);

    return (
        <>
            <div className="mb-2">
                <label className="w-100 fw-bold">
                    Default Rule
                </label>
                <IntRangeRuleInput
                    rule={String(instance.default_rule)}
                    setRule={onSliderMove}
                    min={parseInt(instance.min_rule)}
                    max={parseInt(instance.max_rule)}
                />
            </div>

            <div className="mt-3 text-center">
                <a className="text-decoration-none text-dim" role="button" onClick={() => setOpen(!open)}>
                    Advanced
                </a>
            </div>

            <Collapse in={open}>
                <div>
                    <InputWrapper label="Min brightness">
                        <Form.Control
                            type="text"
                            value={instance.min_rule}
                            onChange={(e) => setRuleLimits("min_rule", e.target.value)}
                        />
                    </InputWrapper>

                    <InputWrapper label="Max brightness">
                        <Form.Control
                            type="text"
                            value={instance.max_rule}
                            onChange={(e) => setRuleLimits("max_rule", e.target.value)}
                        />
                    </InputWrapper>
                </div>
            </Collapse>
        </>
    );
};

DefaultRuleIntRange.propTypes = {
    id: PropTypes.string.isRequired,
    instance: PropTypes.object.isRequired,
    metadata: PropTypes.object.isRequired
};

export default DefaultRuleIntRange;
