import React from 'react';
import InputWrapper from './InputWrapper';

function DefaultRuleFloatRange({ key, param, value, metadata, onChange }) {
    return (
        <InputWrapper label="Default Rule">
            <div className="d-flex flex-row align-items-center my-2">
                <button className="btn btn-sm me-1" /*onClick="rule_slider_increment(this);"*/ data-direction="down" data-stepsize="0.5"><i className="bi-dash-lg"></i></button>
                <input type="range" className="mx-auto" min={metadata.rule_limits[0]} max={metadata.rule_limits[1]} data-displaymin={metadata.rule_limits[0]} data-displaymax={metadata.rule_limits[1]} data-displaytype="float" step="0.5" value={value} onChange={(e) => onChange(param, e.target.value)} autoComplete="off" />
                <button className="btn btn-sm ms-1" /*onClick="rule_slider_increment(this);"*/ data-direction="up" data-stepsize="0.5"><i className="bi-plus-lg"></i></button>
            </div>
        </InputWrapper>
    );
}

export default DefaultRuleFloatRange;
