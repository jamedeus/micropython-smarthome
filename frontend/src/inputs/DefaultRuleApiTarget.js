import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import { ConfigContext } from 'root/ConfigContext';
import { ApiTargetModalContext } from 'modals/ApiTargetRuleModal';

function DefaultRuleApiTarget({ id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange, highlightInvalid } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    // Get callback to open rule modal
    const { handleShow } = useContext(ApiTargetModalContext);

    // Add invalid highlight to set rule button if not set after page validated
    let invalid = false;
    if (highlightInvalid && !instance.default_rule) {
        invalid = true;
    }

    return (
        <>
            <div className="mb-2 pt-3 text-center">
                <Button
                    id={`${id}-default_rule-button`}
                    variant={invalid ? "outline-danger" :"secondary"}
                    onClick={() => handleShow(id, "default_rule")}
                    disabled={!instance.ip}
                >
                    Set rule
                </Button>
            </div>

            <div className="d-none">
                <Form.Control
                    type="text"
                    value={instance.default_rule}
                    onChange={(e) => handleInputChange(id, "default_rule", e.target.value)}
                />
            </div>
        </>
    );
}

DefaultRuleApiTarget.propTypes = {
    id: PropTypes.string,
};

export default DefaultRuleApiTarget;
