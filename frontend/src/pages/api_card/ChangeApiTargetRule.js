import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Dropdown from 'react-bootstrap/Dropdown';
import { ApiCardContext } from 'root/ApiCardContext';
import { showApiTargetRuleModal } from 'modals/ApiTargetRuleModal';

// Dropdown option rendered in top right corner of ApiTarget device cards
const ChangeApiTargetRule = ({id, rule}) => {
    const {set_rule, apiTargetOptions} = useContext(ApiCardContext);

    // Receives dropdown selection object when modal submitted
    const handleSubmit = (newRule) => {
        set_rule(id, newRule);
    };

    return (
        <Dropdown.Item onClick={() => {
            showApiTargetRuleModal(rule, apiTargetOptions[id], handleSubmit);
        }}>
            Change rule
        </Dropdown.Item>
    );
};

ChangeApiTargetRule.propTypes = {
    id: PropTypes.string.isRequired,
    rule: PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.object
    ]).isRequired
};

export default ChangeApiTargetRule;
