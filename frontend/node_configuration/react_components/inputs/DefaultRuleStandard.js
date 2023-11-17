import React from 'react';

function DefaultRuleStandard({ key, id, param, value, onChange }) {
    return (
        <div className="mb-2">
            <label className="w-100">
                <b>Default Rule:</b>
                <select className="form-select" value={value} autoComplete="off" onChange={(e) => onChange(param, e.target.value)} required>
                    <option disabled>Select default rule</option>
                    <option value="enabled">Enabled</option>
                    <option value="disabled">Disabled</option>
                </select>
            </label>
        </div>
    );
}

export default DefaultRuleStandard;
