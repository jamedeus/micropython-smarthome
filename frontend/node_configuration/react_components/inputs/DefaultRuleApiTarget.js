import React from 'react';

function DefaultRuleApiTarget({ key, id, param, value, onChange }) {
    return (
        <>
            <div className="mb-2 text-center">
                <button id={`${id}-default_rule-button`} className="btn btn-secondary mt-3" /*onClick="open_rule_modal(this);"*/ type="button">Set rule</button>
            </div>

            <div className="d-none">
                <input type="text" id={`${id}-default_rule-button`} value={value} onChange={(e) => onChange(id, e.target.value)} required />
            </div>
        </>
    );
}

export default DefaultRuleApiTarget;
