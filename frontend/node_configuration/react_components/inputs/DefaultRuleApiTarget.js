import React, { useContext } from 'react';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import { ConfigContext } from './../ConfigContext';

function DefaultRuleApiTarget({ id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    return (
        <>
            <div className="mb-2 pt-3 text-center">
                <Button
                    id={`${id}-default_rule-button`}
                    variant="secondary"
                    /*onClick="open_rule_modal(this);"*/
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

export default DefaultRuleApiTarget;
