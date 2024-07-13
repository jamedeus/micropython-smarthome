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

// Takes instance ID, key from config template, and metadata object
// Renders correct input for config template key
const ConfigParamInput = ({ id, configKey, metadata }) => {
    switch(configKey) {
        case('nickname'):
            return <NicknameInput id={id} />;
        case('pin'):
            if (id.startsWith('device')) {
                return <DevicePinSelect id={id} />;
            } else {
                return <SensorPinSelect id={id} />;
            }
        case('ip'):
            if (metadata.rule_prompt !== "api_target") {
                return <IPInput id={id} />;
            } else {
                return <TargetNodeDropdown id={id} />;
            }
        case('uri'):
            return <URIInput id={id} />;
        case('on_path'):
            return <HttpGetPathInputs id={id}/>;
        default:
            return null;
    }
};

ConfigParamInput.propTypes = {
    id: PropTypes.string.isRequired,
    configKey: PropTypes.string.isRequired,
    metadata: PropTypes.object.isRequired
};

// Takes instance ID, instance config section, and metadata object
// Renders correct default_rule input based on metadata and config section
const DefaultRuleInput = ({ id, instance, metadata }) => {
    // If instance has units key return thermostat input
    if (instance.units !== undefined) {
        return <DefaultRuleThermostat id={id} />;
    }

    switch (metadata.rule_prompt) {
        case 'standard':
            return <DefaultRuleStandard id={id} />;
        case 'on_off':
            return <DefaultRuleOnOff id={id} />;
        case 'float_range':
            return <DefaultRuleFloatRange id={id} />;
        case 'int_or_fade':
            return <DefaultRuleIntRange id={id} />;
        case 'api_target':
            return <DefaultRuleApiTarget id={id} />;
        default:
            return null;
    }
};

DefaultRuleInput.propTypes = {
    id: PropTypes.string.isRequired,
    instance: PropTypes.object.isRequired,
    metadata: PropTypes.object.isRequired
};

const InstanceCard = ({ id }) => {
    // Get curent state + callback functions from context
    const {
        config,
        deleteing,
        deleteInstance,
        changeInstanceType,
        highlightInvalid
    } = useContext(ConfigContext);

    // Get instance section in config + category (device or sensor)
    const instance = config[id];
    const category = id.replace(/[0-9]/g, '');

    // Get metadata object for selected type
    const instanceMetadata = get_instance_metadata(category, instance._type);

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

    // Returns fade out class if this card is being deleted
    const fadeOutClass = deleteing.id === id ? 'fade-out-card' : '';

    // Returns slide-up class if a card above this one is being deleted
    const slideUpClass = (() => {
        if (deleteing.category === category) {
            // Card being deleted is above this card if it has lower index
            if (parseInt(id.replace(/[a-z]/g, '')) > deleteing.index) {
                return 'slide-up';
            }
        }
        return '';
    })();

    return (
        <div id={`${id}-card`} className={`mb-4 instance-card ${fadeOutClass}`}>
            <Card className={slideUpClass}>
                <Card.Body>
                    <div className="d-flex justify-content-between">
                        <Button className="ps-2" style={{ visibility: 'hidden' }}>
                            <i className="bi-x-lg"></i>
                        </Button>
                        <h4 className="card-title mx-auto my-auto">{`${id}`}</h4>
                        <Button
                            variant="link"
                            className="my-auto pe-2 delete"
                            onClick={() => deleteInstance(id)}
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
                        {/* Render correct input for each key in config template */}
                        {Object.keys(instance).map(key =>
                            <ConfigParamInput
                                key={key}
                                id={id}
                                configKey={key}
                                metadata={instanceMetadata}
                            />
                        )}

                        <DefaultRuleInput
                            id={id}
                            instance={instance}
                            metadata={instanceMetadata}
                        />

                        {/* Thermostat: add units, tolerance inputs */}
                        {instance.units !== undefined ? (
                            <ThermostatParamInputs id={id} />
                        ) : null}
                    </Card.Body>
                </Card.Body>
            </Card>
        </div>
    );
};

InstanceCard.propTypes = {
    id: PropTypes.string.isRequired
};

export default InstanceCard;
