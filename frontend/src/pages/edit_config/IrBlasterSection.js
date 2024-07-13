import React, { useState, useContext } from 'react';
import PropTypes from 'prop-types';
import { ConfigContext } from 'root/ConfigContext';
import Card from 'react-bootstrap/Card';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';
import PinSelectDropdown from './PinSelectDropdown';
import { devicePins } from 'util/metadata';

const IrBlasterSection = () => {
    // Get curent state + callbacks from context
    const { config, updateConfig, handleIrTargetSelect } = useContext(ConfigContext);

    // Create state object to set visibility
    // Default to visible if config contains ir_blaster key
    const [show, setShow] = useState(Object.keys(config).includes("ir_blaster"));

    // Handler for Add IR Blaster button
    // Toggles collapse and adds/removes ir_blaster config section
    const toggleState = (visible) => {
        if (visible) {
            // Open collapse
            setShow(true);
            // Add ir_blaster section to state object
            let update = { ...config };
            update.ir_blaster = { pin: '', target: []};
            updateConfig(update);
        } else {
            // Close collapse
            setShow(false);
            // Remove ir_blaster section from state object
            let update = { ...config };
            delete update.ir_blaster;
            updateConfig(update);
        }
    };

    // Set target array for template below
    const targets = config.ir_blaster ? config.ir_blaster.target : [];

    const TargetCheckbox = ({ target, label }) => {
        return (
            <Form.Check
                type="checkbox"
                id={`${target}-codes`}
                label={label}
                checked={targets.includes(target)}
                onChange={(e) => handleIrTargetSelect(target, e.target.checked)}
            />
        );
    };

    TargetCheckbox.propTypes = {
        target: PropTypes.oneOf(["ac", "tv"]).isRequired,
        label: PropTypes.string.isRequired
    };

    return (
        <div className="max-width-md-50 w-100 mx-auto text-center">
            <p className="text-center mt-3">
                <Button
                    variant="secondary"
                    onClick={() => toggleState(!show)}
                >
                    Add IR Blaster
                </Button>
            </p>
            <Collapse in={show}>
                <div>
                    <Card>
                        <Card.Body className="mx-auto">
                            <h2>IR Blaster</h2>

                            {show ? (
                                <PinSelectDropdown
                                    id="ir_blaster"
                                    options={devicePins}
                                />
                            ) : null}

                            <div className="mb-2">
                                <label htmlFor="ir-remotes" className="fw-bold">
                                    Virtual remotes:
                                </label>
                                <div id="ir-remotes">
                                    <TargetCheckbox
                                        target={"tv"}
                                        label={"TV (Samsung)"}
                                    />
                                    <TargetCheckbox
                                        target={"ac"}
                                        label={"AC (Whynter)"}
                                    />
                                </div>
                            </div>
                        </Card.Body>
                    </Card>
                </div>
            </Collapse>
        </div>
    );
};

export default IrBlasterSection;
