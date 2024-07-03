import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import { ApiTargetModalContext } from 'modals/ApiTargetRuleModal';

// Takes id (device1, sensor3, etc) and rule key (either default_rule or
// schedule rule timestamp/keyword)
const ApiTargetRuleButton = ({ instance, ruleKey }) => {
    // Get callback to open ApiTarget rule modal
    const { handleShow } = useContext(ApiTargetModalContext);

    return (
        <span
            className="form-control"
            onClick={() => handleShow(instance, ruleKey)}
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
