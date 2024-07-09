import React, { useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import Collapse from 'react-bootstrap/Collapse';
import { ConfigContext } from 'root/ConfigContext';
import InputWrapper from './InputWrapper';
import { get_instance_metadata } from 'util/metadata';
import { average } from 'util/helper_functions';
import IntRangeRuleInput from 'inputs/IntRangeRuleInput';

const DefaultRuleIntRange = ({ id }) => {
    // Get curent state + callback functions from context
    const { config, handleInstanceUpdate, handleInputChange } = useContext(ConfigContext);

    // Get instance section from config (state) object
    const instance = config[id];

    // Get metadata object for selected type (contains slider min/max)
    const category = id.replace(/[0-9]/g, '');
    const instanceMetadata = get_instance_metadata(category, instance._type);

    // Replace empty params with defaults (slider component requires all)
    if (!instance.min_rule) {
        instance.min_rule = instanceMetadata.rule_limits[0];
    }
    if (!instance.max_rule) {
        instance.max_rule = instanceMetadata.rule_limits[1];
    }
    if (instance.default_rule === '') {
        instance.default_rule = average(instance.min_rule, instance.max_rule);
    }

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
        const metadata_min = parseInt(instanceMetadata.rule_limits[0], 10);
        const metadata_max = parseInt(instanceMetadata.rule_limits[1], 10);
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
    id: PropTypes.string.isRequired
};

export default DefaultRuleIntRange;
