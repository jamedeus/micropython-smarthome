import React, { useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Card from 'react-bootstrap/Card';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import { ConfigContext } from 'root/ConfigContext';
import NicknameInput from 'inputs/NicknameInput';
import IPInput from 'inputs/IPInput';
import URIInput from 'inputs/URIInput';
import HttpGetPathInputs from 'inputs/HttpGetPathInputs';
import ThermostatParamInputs from 'inputs/ThermostatParamInputs';
import TargetNodeDropdown from 'inputs/TargetNodeDropdown';
import SensorPinSelect from 'inputs/SensorPinSelect';
import DevicePinSelect from 'inputs/DevicePinSelect';
import DefaultRuleStandard from 'inputs/DefaultRuleStandard';
import DefaultRuleFloatRange from 'inputs/DefaultRuleFloatRange';
import DefaultRuleThermostat from 'inputs/DefaultRuleThermostat';
import DefaultRuleIntRange from 'inputs/DefaultRuleIntRange';
import DefaultRuleOnOff from 'inputs/DefaultRuleOnOff';
import DefaultRuleApiTarget from 'inputs/DefaultRuleApiTarget';
import { get_instance_metadata, get_type_dropdown_options } from 'util/metadata';
import { v4 as uuid } from 'uuid';

const InstanceCard = ({ id }) => {
    // Get curent state + callback functions from context
    const {
        config,
        startDeletingInstance,
        changeInstanceType,
        highlightInvalid
    } = useContext(ConfigContext);

    // Get instance section in config + category (device or sensor)
    const instance = config[id];
    const category = id.replace(/[0-9]/g, '');

    // Get metadata object for selected type
    const instanceMetadata = get_instance_metadata(category, instance._type);

    // Create stable UUID for input field keys
    const [key] = useState(uuid());

    console.log(`Rendering ${id}`);

    // Returns true if any sensor (except this card) has type si7021
    // Used to remove si7021 option once used (can't have multiple)
    const containsSi7021 = () => {
        // Get object containing all sensors excluding this card
        const otherSensors = Object.entries(config).reduce((acc, [key, value]) => {
            if (key.startsWith('sensor') && key != id) {
                acc[key] = value;
            }
            return acc;
        }, {});
        // Get array of sensor types (excluding this card)
        const types = Object.values(otherSensors).map(sensor => sensor._type);
        return types.includes('si7021');
    };

    // Get dropdown options from metadata
    // Remove si7021 option if already used on another card
    let dropdownOptions;
    if (category === 'sensor' && containsSi7021(config)) {
        dropdownOptions = get_type_dropdown_options(category, ['si7021']);
    } else {
        dropdownOptions = get_type_dropdown_options(category);
    }

    // Returns list of nodes with input element for each parameter in config section
    // Must use random UUID keys, all other values can change (even device/sensor ID)
    const renderInputs = () => {
        let inputs = [];

        if (instance.nickname !== undefined) {
            inputs.push(
                <NicknameInput key={key + '-nickname'} id={id} />
            );
        }

        if (instance.pin !== undefined) {
            // Is device if no targets key
            if (instance.targets === undefined) {
                inputs.push(
                    <DevicePinSelect key={key + '-pin'} id={id} />
                );
            // Otherwise is sensor
            } else {
                inputs.push(
                    <SensorPinSelect key={key + '-pin'} id={id} />
                );
            }
        }

        if (instance.ip !== undefined) {
            if (instanceMetadata.rule_prompt !== "api_target") {
                inputs.push(
                    <IPInput key={key + '-ip'} id={id} />
                );
            } else {
                inputs.push(
                    <TargetNodeDropdown key={key + '-ip'} id={id} />
                );
            }
        }

        if (instance.uri !== undefined) {
            inputs.push(
                <URIInput key={key + '-uri'} id={id} />
            );
        }

        if (instance.on_path !== undefined && instance.off_path !== undefined) {
            inputs.push(
                <HttpGetPathInputs key={key + '-paths'} id={id}/>
            );
        }

        // Add correct default rule input based on metadata rule_prompt
        inputs.push(renderRuleInput());

        // Thermostat mode, units, tolerance inputs
        if (instance.mode !== undefined && instance.units !== undefined) {
            inputs.push(
                <ThermostatParamInputs key={key + '-params'} id={id} />
            );
        }

        return inputs;
    };

    const renderRuleInput = () => {
        // New card: skip
        if (instance._type === undefined) {
            return null;
        }

        // If instance has units key return thermostat input
        if (instance.units !== undefined) {
            return <DefaultRuleThermostat key={key + '-default_rule'} id={id} />;
        }

        switch (instanceMetadata.rule_prompt) {
            case 'standard':
                return <DefaultRuleStandard key={key + '-default_rule'} id={id} />;
            case 'on_off':
                return <DefaultRuleOnOff key={key + '-default_rule'} id={id} />;
            case 'float_range':
                return <DefaultRuleFloatRange key={key + '-default_rule'} id={id} />;
            case 'int_or_fade':
                return <DefaultRuleIntRange key={key + '-default_rule'} id={id} />;
            case 'api_target':
                return <DefaultRuleApiTarget key={key + '-default_rule'} id={id} />;
            default:
                return null;
        }
    };

    return (
        <div id={`${id}-card`} className="mb-4 instance-card">
            <Card>
                <Card.Body>
                    <div className="d-flex justify-content-between">
                        <Button className="ps-2" style={{ visibility: 'hidden' }}>
                            <i className="bi-x-lg"></i>
                        </Button>
                        <h4 className="card-title mx-auto my-auto">{`${id}`}</h4>
                        <Button
                            variant="link"
                            className="my-auto pe-2 delete"
                            onClick={() => startDeletingInstance(id)}
                        >
                            <i className="bi-x-lg"></i>
                        </Button>
                    </div>
                    <label className="w-100 fw-bold">
                        Type:
                        <Form.Select
                            value={instance._type}
                            onChange={(event) => changeInstanceType(id, category, event)}
                            isInvalid={(highlightInvalid && !instance._type)}
                        >
                            <option value="clear">Select {category} type</option>
                            {dropdownOptions}
                        </Form.Select>
                    </label>
                    <Card.Body id={`${id}-params`}>
                        {renderInputs()}
                    </Card.Body>
                </Card.Body>
            </Card>
        </div>
    );
};

InstanceCard.propTypes = {
    id: PropTypes.string
};

export default InstanceCard;
