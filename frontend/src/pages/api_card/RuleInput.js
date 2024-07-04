import React, { useContext, useState } from 'react';
import PropTypes from 'prop-types';
import { ApiCardContext } from 'root/ApiCardContext';
import IntRangeRuleInput from 'inputs/IntRangeRuleInput';
import FloatRangeRuleInput from 'inputs/FloatRangeRuleInput';


const RuleInput = ({ id, params }) => {
    // Get callback to change rule in status context
    const {set_rule} = useContext(ApiCardContext);

    // Create local state for prompt type (not included in
    // status updates, will remove input if allowed to update)
    const [prompt] = useState(params.prompt);

    let category;
    if (id.startsWith("device")) {
        category = "devices";
    } else {
        category = "sensors";
    }

    switch(prompt) {
        case("float_range"):
            // Create local state for rule limits (not included in
            // status updates, will break slider if allowed to update)
            const [min_rule] = useState(params.min_rule);
            const [max_rule] = useState(params.max_rule);
            return (
                <div className="my-4 pb-2">
                    <FloatRangeRuleInput
                        rule={String(params.current_rule)}
                        setRule={value => set_rule(id, category, value)}
                        min={min_rule}
                        max={max_rule}
                    />
                </div>
            );
        case("int_or_fade"):
            return (
                <div className="my-4 pb-2">
                    <IntRangeRuleInput
                        rule={String(params.current_rule)}
                        setRule={value => set_rule(id, category, value)}
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
