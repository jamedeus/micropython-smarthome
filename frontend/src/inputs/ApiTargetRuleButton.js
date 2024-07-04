import React from 'react';
import PropTypes from 'prop-types';
import { showApiTargetRuleModal } from 'modals/ApiTargetRuleModal';

// Takes id (device1, sensor3, etc) and rule key (either default_rule or
// schedule rule timestamp/keyword)
const ApiTargetRuleButton = ({ instance, ruleKey }) => {
    return (
        <span
            className="form-control"
            onClick={() => showApiTargetRuleModal(instance, ruleKey)}
        >
            Click to edit
        </span>
    );
};

ApiTargetRuleButton.propTypes = {
    instance: PropTypes.string,
    ruleKey: PropTypes.string,
};

export default ApiTargetRuleButton;
