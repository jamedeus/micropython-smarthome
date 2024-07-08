import React, { useContext, useState } from 'react';
import PropTypes from 'prop-types';
import { ApiCardContext } from 'root/ApiCardContext';
import { get_instance_metadata } from 'util/metadata';
import IntRangeRuleInput from 'inputs/IntRangeRuleInput';
import FloatRangeRuleInput from 'inputs/FloatRangeRuleInput';
import ThermostatRuleInput from 'inputs/ThermostatRuleInput';

const RuleInput = ({ id, params }) => {
    // Get callback to change rule in status context
    const {set_rule} = useContext(ApiCardContext);

    // Get metadata containing rule_prompt and slider range limits
    const [metadata] = useState(get_instance_metadata(
        id.startsWith("device") ? "device" : "sensor",
        params.type
    ));

    // Thermostat: Render correct input (matches generic float in switch below)
    if (['si7021', 'dht22'].includes(params.type)) {
        return (
            <ThermostatRuleInput
                rule={String(params.current_rule)}
                setRule={value => set_rule(id, value)}
                min={metadata.rule_limits[0]}
                max={metadata.rule_limits[1]}
                units={params.units}
            />
        );
    }

    switch(metadata.rule_prompt) {
        case("float_range"):
            return (
                <div className="my-4 pb-2">
                    <FloatRangeRuleInput
                        rule={String(params.current_rule)}
                        setRule={value => set_rule(id, value)}
                        min={metadata.rule_limits[0]}
                        max={metadata.rule_limits[1]}
                    />
                </div>
            );
        case("int_or_fade"):
            return (
                <div className="my-4 pb-2">
                    <IntRangeRuleInput
                        rule={String(params.current_rule)}
                        setRule={value => set_rule(id, value)}
                        min={parseInt(params.min_rule)}
                        max={parseInt(params.max_rule)}
                    />
                </div>
            );
    }
};

RuleInput.propTypes = {
    id: PropTypes.string,
    params: PropTypes.object
};

export default RuleInput;
