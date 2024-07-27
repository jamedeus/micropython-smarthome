import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import { EditConfigContext } from 'root/EditConfigContext';
import { showApiTargetRuleModal } from 'modals/ApiTargetRuleModal';

const DefaultRuleApiTarget = ({ id, instance }) => {
    const {
        handleInputChange,
        getTargetNodeOptions,
        highlightInvalid
    } = useContext(EditConfigContext);

    // Add invalid highlight to button if rule not set after page validated
    const invalid = highlightInvalid && !instance.default_rule;

    // Receives user selection when modal closed, updates default_rule
    const handleSubmit = (newRule) => {
        handleInputChange(id, "default_rule", newRule);
    };

    const openModal = () => {
        // Takes current rule to pre-fill in dropdowns, object with valid
        // options for the current target IP, and handleSubmit callback
        showApiTargetRuleModal(
            instance.default_rule,
            getTargetNodeOptions(instance.ip),
            handleSubmit
        );
    };

    return (
        <>
            <div className="mb-2 pt-3 text-center">
                <Button
                    id={`${id}-default_rule-button`}
                    variant={invalid ? "outline-danger" : "secondary"}
                    onClick={openModal}
                    disabled={!instance.ip}
                >
                    Set rule
                </Button>
            </div>
        </>
    );
};

DefaultRuleApiTarget.propTypes = {
    id: PropTypes.string.isRequired,
    instance: PropTypes.object.isRequired
};

export default DefaultRuleApiTarget;
