import React, { useContext } from 'react';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';

function DefaultRuleIntRange({ key, id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    // TODO find a better way
    const category = id.replace(/[0-9]/g, '');
    const instanceMetadata = metadata[`${category}s`][instance._type];

    return (
        <>
            <InputWrapper label="Default Rule">
                <div className="d-flex flex-row align-items-center my-2">
                    <button className="btn btn-sm me-1" /*onClick="rule_slider_increment(this);"*/ data-direction="down" data-stepsize="1"><i className="bi-dash-lg"></i></button>
                    <input type="range" className="mx-auto" min={instanceMetadata.rule_limits[0]} max={instanceMetadata.rule_limits[1]} data-displaymin="1" data-displaymax="100" data-displaytype="int" step="1" value={instance.default_rule} onChange={(e) => handleInputChange(id, "default_rule", e.target.value)} autoComplete="off" />
                    <button className="btn btn-sm ms-1" /*onClick="rule_slider_increment(this);"*/ data-direction="up" data-stepsize="1"><i className="bi-plus-lg"></i></button>
                </div>
            </InputWrapper>

            <div className="mt-3 text-center">
                <a className="text-decoration-none text-dim" data-bs-toggle="collapse" href={`#${id}-advanced_settings`} role="button" aria-expanded="false" aria-controls={`${id}-advanced_settings`}>Advanced</a>
            </div>

            <div id={`${id}-advanced_settings`} className="collapse">
                <InputWrapper label="Min brightness">
                    <input
                        type="text"
                        className="form-control rule-limits"
                        value={instance.min_rule}
                        data-min={instanceMetadata.rule_limits[0]}
                        data-max={instanceMetadata.rule_limits[1]}
                        onChange={(e) => handleInputChange(id, "min_rule", e.target.value)}
                        required
                    />
                </InputWrapper>

                <InputWrapper label="Max brightness">
                    <input
                        type="text"
                        className="form-control rule-limits"
                        value={instance.max_rule}
                        data-min={instanceMetadata.rule_limits[0]}
                        data-max={instanceMetadata.rule_limits[1]}
                        onChange={(e) => handleInputChange(id, "max_rule", e.target.value)}
                        required
                    />
                </InputWrapper>
            </div>
        </>
    );
}

export default DefaultRuleIntRange;
