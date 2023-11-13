import React from 'react';
import NicknameInput from './inputs/NicknameInput';
import IPInput from './inputs/IPInput';
import URIInput from './inputs/URIInput';
import HttpGetPathInputs from './inputs/HttpGetPathInputs';
import ThermostatParamInputs from './inputs/ThermostatParamInputs';
import SensorPinSelect from './inputs/SensorPinSelect';
import DevicePinSelect from './inputs/DevicePinSelect';
import DefaultRuleStandard from './inputs/DefaultRuleStandard';
import DefaultRuleFloatRange from './inputs/DefaultRuleFloatRange';
import DefaultRuleIntRange from './inputs/DefaultRuleIntRange';
import DefaultRuleOnOff from './inputs/DefaultRuleOnOff';
import DefaultRuleApiTarget from './inputs/DefaultRuleApiTarget';

class InstanceCard extends React.Component {
    renderInputs = (config, category, globalMetadata) => {
        let inputs = [];

        if (config.nickname !== undefined) {
            inputs.push(<NicknameInput key="nickname" id="nickname" value={config.nickname} onChange={this.props.onInputChange} />);
        }

        if (config.pin !== undefined) {
            // Is device if no targets key
            if (config.targets === undefined) {
                inputs.push(<DevicePinSelect key="pin" id="pin" value={config.pin} onChange={this.props.onInputChange} />);
            // Otherwise is sensor
            } else {
                inputs.push(<SensorPinSelect key="pin" id="pin" value={config.pin} onChange={this.props.onInputChange} />);
            };
        }

        if (config.ip !== undefined) {
            inputs.push(<IPInput key="ip" id="ip" value={config.ip} onChange={this.props.onInputChange} />);
        }

        if (config.uri !== undefined) {
            inputs.push(<URIInput key="uri" id="uri" value={config.uri} onChange={this.props.onInputChange} />);
        }

        if (config.on_path !== undefined && config.off_path !== undefined) {
            inputs.push(<HttpGetPathInputs key="on_off_path" id="on_off_path" on_path={config.on_path} off_path={config.off_path} onChange={this.props.onInputChange} />);
        }

        // Add correct default rule input based on metadata rule_prompt
        inputs.push(this.renderRuleInput(config, category, globalMetadata));

        // Thermostat mode, units, tolerance inputs
        if (config.mode !== undefined && config.units !== undefined) {
            inputs.push(<ThermostatParamInputs key="thermostat" id="thermostat" mode={config['mode']} units={config['units']} tolerance={config['tolerance']} onChange={this.props.onInputChange} />);
        }

        return inputs;
    };

    renderRuleInput = (config, category, globalMetadata) => {
        // New card: skip
        if (config._type === undefined) {
            return null
        }

        // Get metadata for selected instance type
        const metadata = globalMetadata[`${category}s`][config._type];

        switch (metadata.rule_prompt) {
            case 'standard':
                return <DefaultRuleStandard key='default_rule' id='default_rule' value={config.default_rule} onChange={this.props.onInputChange} />;
            case 'on_off':
                return <DefaultRuleOnOff key='default_rule' id='default_rule' value={config.default_rule} onChange={this.props.onInputChange} />;
            case 'float_range':
                return <DefaultRuleFloatRange key='default_rule' id='default_rule' value={config.default_rule} metadata={metadata} onChange={this.props.onInputChange} />;
            case 'int_or_fade':
                return <DefaultRuleIntRange key='default_rule' id='default_rule' value={config.default_rule} min={config.min_rule} max={config.max_rule} metadata={metadata} onChange={this.props.onInputChange} />;
            case 'api_target':
                return <DefaultRuleApiTarget key='default_rule' id='default_rule' value={config.default_rule} onChange={this.props.onInputChange} />;
            default:
                return null;
        }
    }

    render() {
        // Index is the instance ID, config is section from state object
        const { id, category, config } = this.props;
        const globalMetadata = window.metadata; // Accessing the global metadata from index.html

        console.log(config)

        return (
            <div className="fade-in mb-4">
                <div className="card">
                <div className="card-body">
                    <div className="d-flex justify-content-between">
                        <button className="btn ps-2" style={{ visibility: 'hidden' }}><i className="bi-x-lg"></i></button>
                        <h4 className="card-title mx-auto my-auto">{`${id}`}</h4>
                        <button className="btn my-auto pe-2 delete" onClick={() => this.props.onDelete(id)}><i className="bi-x-lg"></i></button>
                    </div>
                    <label className="w-100">
                        <b>Type:</b>
                        <select className="form-select mt-2" data-param="_type" required onChange={this.props.onTypeChange}>
                            <option value="clear">Select {category} type</option>
                            {Object.entries(globalMetadata[`${category}s`]).map(([key, type]) => (
                            <option key={key} value={type.config_name}>{type.class_name}</option>
                            ))}
                        </select>
                    </label>
                    <div id={`${id}-params`} className="card-body">
                        {this.renderInputs(config, category, globalMetadata)}
                    </div>
                </div>
                </div>
            </div>
        );
    }
}

export default InstanceCard;
