import React, { useState, useContext } from 'react';
import PropTypes from 'prop-types';
import { MetadataContext } from 'root/MetadataContext';
import IntRangeRuleInput from 'inputs/IntRangeRuleInput';
import FloatRangeRuleInput from 'inputs/FloatRangeRuleInput';
import ThermostatRuleInput from 'inputs/ThermostatRuleInput';

const RuleInput = ({ id, params, setRule, onBlur }) => {
    // Get metadata containing rule_prompt and slider range limits
    const { get_instance_metadata } = useContext(MetadataContext);
    const [metadata] = useState(get_instance_metadata(
        id.startsWith("device") ? "device" : "sensor",
        params.type
    ));

    // Thermostat: Render correct input (matches generic float in switch below)
    if (['si7021', 'dht22'].includes(params.type)) {
        return (
            <div className="my-4 pb-2">
                <ThermostatRuleInput
                    rule={String(params.current_rule)}
                    setRule={setRule}
                    min={metadata.rule_limits[0]}
                    max={metadata.rule_limits[1]}
                    units={params.units}
                    onBlur={onBlur}
                />
            </div>
        );
    }

    switch(metadata.rule_prompt) {
        case("float_range"):
            return (
                <div className="my-4 pb-2">
                    <FloatRangeRuleInput
                        rule={String(params.current_rule)}
                        setRule={setRule}
                        min={metadata.rule_limits[0]}
                        max={metadata.rule_limits[1]}
                        onBlur={onBlur}
                    />
                </div>
            );
        case("int_or_fade"):
            return (
                <div className="my-4 pb-2">
                    <IntRangeRuleInput
                        rule={String(params.current_rule)}
                        setRule={setRule}
                        min={parseInt(params.min_rule)}
                        max={parseInt(params.max_rule)}
                        displayMin={metadata.rule_limits[0]}
                        onBlur={onBlur}
                    />
                </div>
            );
    }
};

RuleInput.propTypes = {
    id: PropTypes.string.isRequired,
    params: PropTypes.object.isRequired,
    setRule: PropTypes.func.isRequired,
    onBlur: PropTypes.func.isRequired
};

export default RuleInput;
