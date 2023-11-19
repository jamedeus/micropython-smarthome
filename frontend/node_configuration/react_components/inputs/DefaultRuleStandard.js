import React, { useContext } from 'react';
import { ConfigContext } from './../ConfigContext';

function DefaultRuleStandard({ key, id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    return (
        <div className="mb-2">
            <label className="w-100">
                <b>Default Rule:</b>
                <select className="form-select" value={instance.default_rule} autoComplete="off" onChange={(e) => handleInputChange(id, "default_rule", e.target.value)} required>
                    <option disabled>Select default rule</option>
                    <option value="enabled">Enabled</option>
                    <option value="disabled">Disabled</option>
                </select>
            </label>
        </div>
    );
}

export default DefaultRuleStandard;
