import React from 'react';
import InputWrapper from './InputWrapper';

function DefaultRuleIntRange({ key, id, param, value, min, max, metadata, onChange }) {
    return (
        <>
            <InputWrapper label="Default Rule">
                <div className="d-flex flex-row align-items-center my-2">
                    <button className="btn btn-sm me-1" /*onClick="rule_slider_increment(this);"*/ data-direction="down" data-stepsize="1"><i className="bi-dash-lg"></i></button>
                    <input type="range" className="mx-auto" min={metadata.rule_limits[0]} max={metadata.rule_limits[1]} data-displaymin="1" data-displaymax="100" data-displaytype="int" step="1" value={value} onChange={(e) => onChange(param, e.target.value)} autoComplete="off" />
                    <button className="btn btn-sm ms-1" /*onClick="rule_slider_increment(this);"*/ data-direction="up" data-stepsize="1"><i className="bi-plus-lg"></i></button>
                </div>
            </InputWrapper>

            <div className="mt-3 text-center">
                <a className="text-decoration-none text-dim" data-bs-toggle="collapse" href={`#${id}-advanced_settings`} role="button" aria-expanded="false" aria-controls={`${id}-advanced_settings`}>Advanced</a>
            </div>

            <div id={`${id}-advanced_settings`} className="collapse">
                <InputWrapper label="Min brightness">
                    <input type="text" className="form-control rule-limits" value={min} data-min={metadata.rule_limits[0]} data-max={metadata.rule_limits[1]} onChange={(e) => onChange('min_rule', e.target.value)} required />
                </InputWrapper>

                <InputWrapper label="Max brightness">
                    <input type="text" className="form-control rule-limits" value={max} data-min={metadata.rule_limits[0]} data-max={metadata.rule_limits[1]} onChange={(e) => onChange('max_rule', e.target.value)} required />
                </InputWrapper>
            </div>
        </>
    );
}

export default DefaultRuleIntRange;
