import React from 'react';
import Card from 'react-bootstrap/Card';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';
import DevicePinSelect from './inputs/DevicePinSelect';


function IrBlasterSection({ key, configured, pin, target, onChange, onTargetSelect }) {
    return (
        <div id="ir_blaster_row" className="max-width-md-50 w-100 mx-auto text-center">
            <p className="text-center mt-3">
                <Button
                    variant="secondary"
                    onClick={() => onChange("ir_blaster", "configured", !configured)}
                >
                    Add IR Blaster
                </Button>
            </p>
            <Collapse in={configured}>
                <div>
                    <Card>
                        <Card.Body className="mx-auto">
                            <h2>IR Blaster</h2>

                            <DevicePinSelect
                                key="ir_blaster"
                                param="pin"
                                value={pin}
                                onChange={(paramName, value) => onChange("ir_blaster", paramName, value)}
                            />

                            <div className="mb-2">
                                <label htmlFor="ir-remotes"><b>Virtual remotes:</b></label>
                                <div id="ir-remotes">
                                    <Form.Check
                                        type="checkbox"
                                        id="tv-codes"
                                        label="TV (Samsung)"
                                        checked={target.includes("tv")}
                                        onChange={(e) => onTargetSelect("tv", e.target.checked)}
                                    />
                                    <Form.Check
                                        type="checkbox"
                                        id="ac-codes"
                                        label="AC (Whynter)"
                                        checked={target.includes("ac")}
                                        onChange={(e) => onTargetSelect("ac", e.target.checked)}
                                    />
                                </div>
                            </div>
                        </Card.Body>
                    </Card>
                </div>
            </Collapse>
        </div>
    )
}

export default IrBlasterSection;
