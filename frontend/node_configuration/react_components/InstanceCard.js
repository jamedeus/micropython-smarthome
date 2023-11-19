import React, { useContext, useMemo } from 'react';
import { ConfigContext } from './ConfigContext';
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


function InstanceCard({key, id}) {
    // Get curent state + callback functions from context
    const { config, startDeletingInstance, changeInstanceType, handleInputChange } = useContext(ConfigContext);

    // Get instance section in config + category (device or sensor)
    const instance = config[id];
    const category = id.replace(/[0-9]/g, '');

    const renderInputs = () => {
        let inputs = [];

        if (instance.nickname !== undefined) {
            inputs.push(<NicknameInput key={key} id={id} param="nickname" value={instance.nickname} onChange={handleInputChange} />);
        }

        if (instance.pin !== undefined) {
            // Is device if no targets key
            if (instance.targets === undefined) {
                inputs.push(<DevicePinSelect key={key} id={id} param="pin" value={instance.pin} onChange={handleInputChange} />);
            // Otherwise is sensor
            } else {
                inputs.push(<SensorPinSelect key={key} id={id} param="pin" value={instance.pin} onChange={handleInputChange} />);
            };
        }

        if (instance.ip !== undefined) {
            inputs.push(<IPInput key={key} id={id} param="ip" value={instance.ip} onChange={handleInputChange} />);
        }

        if (instance.uri !== undefined) {
            inputs.push(<URIInput key={key} id={id} param="uri" value={instance.uri} onChange={handleInputChange} />);
        }

        if (instance.on_path !== undefined && instance.off_path !== undefined) {
            inputs.push(<HttpGetPathInputs key={key} id={id} param="on_off_path" on_path={instance.on_path} off_path={instance.off_path} onChange={handleInputChange} />);
        }

        // Add correct default rule input based on metadata rule_prompt
        inputs.push(renderRuleInput());

        // Thermostat mode, units, tolerance inputs
        if (instance.mode !== undefined && instance.units !== undefined) {
            inputs.push(<ThermostatParamInputs key={key} id={id} param="thermostat" mode={config['mode']} units={config['units']} tolerance={config['tolerance']} onChange={handleInputChange} />);
        }

        return inputs;
    };

    const renderRuleInput = () => {
        // New card: skip
        if (instance._type === undefined) {
            return null
        }

        // Get metadata for selected instance type from global metadata object (from django template)
        const instanceMetadata = metadata[`${category}s`][instance._type];

        switch (instanceMetadata.rule_prompt) {
            case 'standard':
                return <DefaultRuleStandard key={key} id={id} param='default_rule' value={instance.default_rule} onChange={handleInputChange} />;
            case 'on_off':
                return <DefaultRuleOnOff key={key} id={id} param='default_rule' value={instance.default_rule} onChange={handleInputChange} />;
            case 'float_range':
                return <DefaultRuleFloatRange key={key} id={id} param='default_rule' value={instance.default_rule} metadata={instanceMetadata} onChange={handleInputChange} />;
            case 'int_or_fade':
                console.log('INT RULE')
                console.log(key)
                console.log(id)
                return <DefaultRuleIntRange key={key} id={id} param='default_rule' value={instance.default_rule} min={instance.min_rule} max={instance.max_rule} metadata={instanceMetadata} onChange={handleInputChange} />;
            case 'api_target':
                return <DefaultRuleApiTarget key={key} id={id} param='default_rule' value={instance.default_rule} onChange={handleInputChange} />;
            default:
                return null;
        }
    }

    console.log(instance)

    return (
        <div id={`${id}-card`} className="mb-4 instance-card">
            <div className="card">
            <div className="card-body">
                <div className="d-flex justify-content-between">
                    <button className="btn ps-2" style={{ visibility: 'hidden' }}><i className="bi-x-lg"></i></button>
                    <h4 className="card-title mx-auto my-auto">{`${id}`}</h4>
                    <button className="btn my-auto pe-2 delete" onClick={() => startDeletingInstance(id)}><i className="bi-x-lg"></i></button>
                </div>
                <label className="w-100">
                    <b>Type:</b>
                    <select className="form-select mt-2" value={instance._type} required onChange={(event) => changeInstanceType(id, category, event)}>
                        <option value="clear">Select {category} type</option>
                        {Object.entries(metadata[`${category}s`]).map(([key, type]) => (
                        <option key={key} value={type.config_name}>{type.class_name}</option>
                        ))}
                    </select>
                </label>
                <div id={`${id}-params`} className="card-body">
                    {renderInputs()}
                </div>
            </div>
            </div>
        </div>
    );
}

export default InstanceCard;
