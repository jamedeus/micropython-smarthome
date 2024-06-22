import React, { useState, useContext } from 'react';
import { ConfigContext } from 'root/ConfigContext';
import Card from 'react-bootstrap/Card';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';
import DevicePinSelect from 'inputs/DevicePinSelect';

function IrBlasterSection() {
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
    let target = [];
    if (config.ir_blaster !== undefined) {
        target = config.ir_blaster.target;
    }

    return (
        <div id="ir_blaster_row" className="max-width-md-50 w-100 mx-auto text-center">
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

                            <DevicePinSelect
                                id="ir_blaster"
                            />

                            <div className="mb-2">
                                <label htmlFor="ir-remotes"><b>Virtual remotes:</b></label>
                                <div id="ir-remotes">
                                    <Form.Check
                                        type="checkbox"
                                        id="tv-codes"
                                        label="TV (Samsung)"
                                        checked={target.includes("tv")}
                                        onChange={(e) => handleIrTargetSelect("tv", e.target.checked)}
                                    />
                                    <Form.Check
                                        type="checkbox"
                                        id="ac-codes"
                                        label="AC (Whynter)"
                                        checked={target.includes("ac")}
                                        onChange={(e) => handleIrTargetSelect("ac", e.target.checked)}
                                    />
                                </div>
                            </div>
                        </Card.Body>
                    </Card>
                </div>
            </Collapse>
        </div>
    );
}

export default IrBlasterSection;
