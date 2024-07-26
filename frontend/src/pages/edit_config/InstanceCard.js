import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Card from 'react-bootstrap/Card';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import { EditConfigContext } from 'root/EditConfigContext';
import { MetadataContext } from 'root/MetadataContext';
import NicknameInput from './NicknameInput';
import IPInput from './IPInput';
import URIInput from './URIInput';
import HttpGetPathInputs from './HttpGetPathInputs';
import ThermostatParamInputs from './ThermostatParamInputs';
import TargetNodeDropdown from './TargetNodeDropdown';
import PinSelectDropdown from './PinSelectDropdown';
import DefaultRuleStandard from './DefaultRuleStandard';
import DefaultRuleFloatRange from './DefaultRuleFloatRange';
import DefaultRuleThermostat from './DefaultRuleThermostat';
import DefaultRuleIntRange from './DefaultRuleIntRange';
import DefaultRuleOnOff from './DefaultRuleOnOff';
import DefaultRuleApiTarget from './DefaultRuleApiTarget';
import { sensorPins, devicePins } from 'util/metadata';

// Takes category ("device" or "sensor"), returns array of dropdown options
// containing every driver type in category.
// Optional exclude array can contain config_names that should be skipped.
const TypeDropdownOptions = ({ category, exclude }) => {
    // Get metadata for all devices and sensors
    const { metadata } = useContext(MetadataContext);

    return (
        Object.entries(metadata[`${category}s`])
            .filter(([key, _]) =>
                !exclude.includes(key)
            ).map(([key, type]) => (
                <option key={key} value={type.config_name}>
                    {type.class_name}
                </option>
            ))
    );
};

TypeDropdownOptions.propTypes = {
    category: PropTypes.oneOf(['device', 'sensor']).isRequired,
    exclude: PropTypes.array
};

// Takes instance ID, key from config template, and metadata object
// Renders correct input for config template key
const ConfigParamInput = ({ id, configKey, metadata }) => {
    switch(configKey) {
        case('nickname'):
            return <NicknameInput id={id} />;
        case('pin'):
            if (id.startsWith('device')) {
                return <PinSelectDropdown id={id} options={devicePins} />;
            } else {
                return <PinSelectDropdown id={id} options={sensorPins} />;
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
        return (
            <DefaultRuleThermostat
                id={id}
                instance={instance}
                metadata={metadata}
            />
        );
    }

    switch (metadata.rule_prompt) {
        case 'standard':
            return (
                <DefaultRuleStandard
                    id={id}
                    instance={instance}
                />
            );
        case 'on_off':
            return (
                <DefaultRuleOnOff
                    id={id}
                    instance={instance}
                />
            );
        case 'float_range':
            return (
                <DefaultRuleFloatRange
                    id={id}
                    instance={instance}
                    metadata={metadata}
                />
            );
        case 'int_or_fade':
            return (
                <DefaultRuleIntRange
                    id={id}
                    instance={instance}
                    metadata={metadata}
                />
            );
        case 'api_target':
            return (
                <DefaultRuleApiTarget
                    id={id}
                    instance={instance}
                />
            );
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
    } = useContext(EditConfigContext);

    // Get instance section in config + category (device or sensor)
    const instance = config[id];
    const category = id.replace(/[0-9]/g, '');

    // Get metadata object for selected type
    const { get_instance_metadata } = useContext(MetadataContext);
    const instanceMetadata = get_instance_metadata(category, instance._type);

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

    // Returns fade out class if this card is being deleted, fade in otherwise
    const fadeClass = deleteing.id === id ? 'fade-out-card' : 'fade-in-card';

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
        <div id={`${id}-card`} className={`mb-4 ${fadeClass}`}>
            <Card className={slideUpClass}>
                <Card.Body>
                    <div className="d-flex justify-content-between">
                        <Button className="ps-2" style={{ visibility: 'hidden' }}>
                            <i className="bi-x-lg"></i>
                        </Button>
                        <h4 className="card-title mx-auto my-auto">
                            {`${id}`}
                        </h4>
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
                            <TypeDropdownOptions
                                category={category}
                                exclude={containsSi7021(config) ? ['si7021'] : []}
                            />
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
