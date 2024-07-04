import React from 'react';
import PropTypes from 'prop-types';
import { showApiTargetRuleModal } from 'modals/ApiTargetRuleModal';

// Takes current rule, object returned by getTargetNodeOptions, and callback
// that receives user selection when modal submitted
const ApiTargetRuleButton = ({ currentRule, targetNodeOptions, handleSubmit }) => {
    return (
        <span
            className="form-control"
            onClick={() => showApiTargetRuleModal(
                currentRule, targetNodeOptions, handleSubmit
            )}
        >
            Click to edit
        </span>
    );
};

ApiTargetRuleButton.propTypes = {
    currentRule: PropTypes.object.isRequired,
    targetNodeOptions: PropTypes.object.isRequired,
    handleSubmit: PropTypes.func.isRequired
};

export default ApiTargetRuleButton;
