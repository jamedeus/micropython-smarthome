import React, { useContext } from 'react';
import { ConfigContext } from './../ConfigContext';

function DefaultRuleApiTarget({ key, id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    return (
        <>
            <div className="mb-2 text-center">
                <button
                    id={`${id}-default_rule-button`}
                    className="btn btn-secondary mt-3" /*onClick="open_rule_modal(this);"*/
                    type="button"
                >
                    Set rule
                </button>
            </div>

            <div className="d-none">
                <input
                    type="text"
                    id={`${id}-default_rule-button`}
                    value={instance.default_rule}
                    onChange={(e) => handleInputChange(id, "default_rule", e.target.value)}
                    required
                />
            </div>
        </>
    );
}

export default DefaultRuleApiTarget;
