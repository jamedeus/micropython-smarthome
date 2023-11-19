import React, { useContext } from 'react';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';

function DefaultRuleFloatRange({ key, id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange, handleSliderButton } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    // TODO find a better way
    const category = id.replace(/[0-9]/g, '');
    const instanceMetadata = metadata[`${category}s`][instance._type];

    return (
        <InputWrapper label="Default Rule">
            <div className="d-flex flex-row align-items-center my-2">
                <button className="btn btn-sm me-1" onClick={(e) => handleSliderButton(id, 0.5, "down")}><i className="bi-dash-lg"></i></button>
                <input type="range" className="mx-auto" min={instance.min_rule} max={instance.max_rule} data-displaymin={instanceMetadata.rule_limits[0]} data-displaymax={instanceMetadata.rule_limits[1]} data-displaytype="float" step="0.5" value={instance.default_rule} onChange={(e) => handleInputChange(id, "default_rule", e.target.value)} autoComplete="off" />
                <button className="btn btn-sm ms-1" onClick={(e) => handleSliderButton(id, 0.5, "up")}><i className="bi-plus-lg"></i></button>
            </div>
        </InputWrapper>
    );
}

export default DefaultRuleFloatRange;
