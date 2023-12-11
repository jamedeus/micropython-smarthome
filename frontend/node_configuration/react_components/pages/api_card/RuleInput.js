import React, { useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import Collapse from 'react-bootstrap/Collapse';
import { ScheduleRulesTable } from './ScheduleRules';
import { ApiCardContext } from 'root/ApiCardContext';
import RuleSlider from 'inputs/RuleSlider';


const RuleInput = ({ id, params }) => {
    // Get callback to change rule in status context
    const {set_rule} = useContext(ApiCardContext);

    // Create local state for prompt type (not included in
    // status updates, will remove input if allowed to update)
    const [prompt, setPrompt] = useState(params.prompt);

    let category;
    if (id.startsWith("device")) {
        category = "devices";
    } else {
        category = "sensors";
    }

    // Handler for slider move events
    const onSliderMove = (value) => {
        set_rule(id, category, value);
    };

    // Handler for slider + and - buttons
    const onButtonClick = (step, direction, min_rule, max_rule) => {
        let new_rule;
        if (direction === "up") {
            new_rule = parseFloat(params.current_rule) + parseFloat(step);
        } else {
            new_rule = parseFloat(params.current_rule) - parseFloat(step);
        }

        // Enforce rule limits
        if (new_rule < parseFloat(min_rule)) {
            new_rule = parseFloat(min_rule);
        } else if (new_rule > parseFloat(max_rule)) {
            new_rule = parseFloat(max_rule);
        }

        set_rule(id, category, new_rule);
    };

    switch(prompt) {
        case("float_range"):
            // Create local state for rule limits (not included in
            // status updates, will break slider if allowed to update)
            const [min_rule, setMinRule] = useState(params.min_rule);
            const [max_rule, setMaxRule] = useState(params.max_rule);
            return (
                <div className="my-4 pb-2">
                    <RuleSlider
                        rule_value={String(params.current_rule)}
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
        case("int_or_fade"):
            return (
                <div className="my-4 pb-2">
                    <RuleSlider
                        rule_value={String(params.current_rule)}
                        slider_min={parseInt(params.min_rule)}
                        slider_max={parseInt(params.max_rule)}
                        slider_step={1}
                        button_step={1}
                        display_type={"int"}
                        onButtonClick={onButtonClick}
                        onSliderMove={onSliderMove}
                    />
                </div>
            );
        case("api_target"):
            return <input type="text" value={params.current_rule} className="d-none" />;
    }
}

export default RuleInput;
