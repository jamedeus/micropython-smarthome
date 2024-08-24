import React, { useState, useContext } from 'react';
import PropTypes from 'prop-types';
import { EditConfigContext } from 'root/EditConfigContext';
import Card from 'react-bootstrap/Card';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';
import PinSelectDropdown from './PinSelectDropdown';
import { devicePins } from 'util/metadata';
import { parse_dom_context } from 'util/django_util';

const IrBlasterSection = () => {
    // Get curent state + callbacks from context
    const {
        config,
        addIrBlasterSection,
        handleIrTargetSelect
    } = useContext(EditConfigContext);

    // Read ir_blaster target names from django template context
    const [ir_blaster_targets] = useState(() => {
        return parse_dom_context("ir_blaster_targets");
    });

    // Create state object to set visibility
    // Default to visible if config contains ir_blaster key
    const [show, setShow] = useState(Object.keys(config).includes("ir_blaster"));

    // Handler for Add IR Blaster button
    // Toggles collapse and adds/removes ir_blaster config section
    const toggleState = () => {
        addIrBlasterSection(!show);
        setShow(!show);
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
        target: PropTypes.oneOf(ir_blaster_targets).isRequired,
        label: PropTypes.string.isRequired
    };

    // Takes ir_blaster target name, returns label shown next to checkbox
    // Replaces underscores with spaces, capitalizes each word, replaces
    // ac with AC, replaces tv with TV
    const getTargetLabel = (target) => {
        return target.split('_').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ')
        .replace('Tv', 'TV')
        .replace('Ac', 'AC');
    };

    return (
        <div className="max-width-md-50 w-100 mx-auto text-center">
            <p className="text-center mt-3">
                <Button
                    variant="secondary"
                    onClick={() => toggleState()}
                >
                    Add IR Blaster
                </Button>
            </p>
            <Collapse in={show}>
                <div>
                    <Card>
                        <Card.Body className="mx-auto">
                            <h2>IR Blaster</h2>

                            <PinSelectDropdown
                                id="ir_blaster"
                                options={devicePins}
                            />

                            <div className="mb-2">
                                <label htmlFor="ir-remotes" className="fw-bold">
                                    Virtual remotes:
                                </label>
                                <div id="ir-remotes">
                                    {ir_blaster_targets.map(target => {
                                        return (
                                            <TargetCheckbox
                                                target={target}
                                                label={getTargetLabel(target)}
                                                key={target}
                                            />
                                        );
                                    })}
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
