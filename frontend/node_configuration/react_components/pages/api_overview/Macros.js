import React, { useState, useContext } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import FloatingLabel from 'react-bootstrap/FloatingLabel';
import Button from 'react-bootstrap/Button';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import Dropdown from 'react-bootstrap/Dropdown';
import DropdownButton from 'react-bootstrap/DropdownButton';
import Collapse from 'react-bootstrap/Collapse';
import { RecordMacroModal } from 'modals/RecordMacroModal';
import { ApiOverviewContext } from 'root/ApiOverviewContext';
import { EditMacroModalContext } from 'modals/EditMacroModal';
import { toTitle, sleep } from 'util/helper_functions';
import { ButtonSpinner, CheckmarkAnimation } from 'util/animations';
import 'css/macros.css';


const MacroRow = ({ name, actions }) => {
    // Get callback to delete macro context
    const { deleteMacro } = useContext(ApiOverviewContext);

    // Get callback to open edit macro modal
    const { openEditMacroModal } = useContext(EditMacroModalContext);

    // Create state objects for button animations
    const [runAnimation, setRunAnimation] = useState("false");

    const edit = () => {
        openEditMacroModal(name, actions);
    };

    const run = async () => {
        // Start loading animation
        setRunAnimation("loading");

        // Run macro
        const result = await fetch(`/run_macro/${name}`);
        const status = await result.status;

        // TODO handle failure
        if (status === 200) {
            // Start checkmark animation, wait until complete
            setRunAnimation("complete");
            await sleep(2000);

            // Return to original text
            // TODO fade out (handle in CSS)
            setRunAnimation("false");
        }
    };

    const del = async () => {
        // Start loading animation
        setRunAnimation("loading");

        // Delete macro
        const result = await fetch(`/delete_macro/${name}`);
        const status = await result.status;

        // TODO handle failure
        if (status === 200) {
            // Fade row out, wait for animation to complete
            document.getElementById(name).classList.add('fade-out');
            await sleep(200);

            // Remove from context (re-renders without this row)
            deleteMacro(name);
        } else {
            // Cancel loading animation
            setRunAnimation("false");
        }
    };

    return (
        <div id={name} className="d-flex mb-3">
            <ButtonGroup className="macro-row">
                <Button onClick={run} className="macro-button">
                    {(() => {
                        switch(runAnimation) {
                            case("loading"):
                                return <ButtonSpinner />;
                            case("complete"):
                                return <CheckmarkAnimation size="small" />;
                            default:
                                return <h3 className="macro-name">{toTitle(name)}</h3>;
                        }
                    })()}
                </Button>

                <DropdownButton as={ButtonGroup} title={<i className="bi-gear-fill"></i>} align="end" className="macro-dropdown-button">
                    <Dropdown.Item onClick={edit}><i className="bi-pencil"></i> Edit</Dropdown.Item>
                    <Dropdown.Item onClick={del}><i className="bi-trash"></i> Delete</Dropdown.Item>
                </DropdownButton>
            </ButtonGroup>
        </div>
    );
};

MacroRow.propTypes = {
    name: PropTypes.string,
    actions: PropTypes.array
};


const NewMacroField = () => {
    // Get callback to start recording macro
    const { startRecording } = useContext(ApiOverviewContext);

    // Create state object for new macro name input, validation status
    const [newMacroName, setNewMacroName] = useState("");
    const [invalid, setInvalid] = useState(false);

    // Start recording macro with name from input, add record mode URL params
    const handleStart = async () => {
        // Check if name is available
        const response = await fetch(`/macro_name_available/${newMacroName}`);
        const status = await response.status;

        // If name is available start recording
        if (status === 200) {
            startRecording(newMacroName);
            history.pushState({}, '', `/api/recording/${newMacroName}`);
        // If name is taken show invalid highlight
        } else {
            setInvalid(true);
        }
    };

    // Clear previous invalid highlight when user types in field
    const handleInput = (value) => {
        setNewMacroName(value);
        setInvalid(false);
    };

    // Start recording if enter key pressed in field with text
    const handleEnterKey = (e) => {
        if (e.key === "Enter" && newMacroName.length > 0) {
            handleStart();
        }
    };

    return (
        <>
            <div className="form-floating mb-3">
                <FloatingLabel label="New macro name">
                    <Form.Control
                        type="text"
                        id="new-macro-name"
                        value={newMacroName}
                        placeholder="New macro name"
                        onChange={(e) => handleInput(e.target.value)}
                        onKeyDown={handleEnterKey}
                        isInvalid={invalid}
                    />
                    <Form.Control.Feedback type="invalid">
                        Name already in use
                    </Form.Control.Feedback>
                </FloatingLabel>
            </div>
            <Button
                variant="success"
                disabled={newMacroName.length === 0}
                onClick={handleStart}
            >
                Start Recording
            </Button>
        </>
    );
};


const Macros = () => {
    // Get django context, state object for name of macro being recorded, callback to finish recording
    const { context, recording, setRecording } = useContext(ApiOverviewContext);

    // Create state object to set collapse visibility
    const [show, setShow] = useState(false);

    const finishRecording = () => {
        setRecording("");
        // Remove URL params (prevents page refresh from resuming recording)
        history.pushState({}, '', '/api');
    };

    const openNewMacro = async () => {
        // Toggle collapse visibility
        setShow(!show);
        // If collapse was previously closed focus input after opening
        if (!show) {
            await sleep(1);
            document.getElementById('new-macro-name').focus();
        }
    };

    console.log(recording);

    switch(recording.length) {
        case(0):
            return (
                <div className="text-center section p-3 mx-auto mb-5">
                    {(() => {
                        switch(true) {
                            // If macros exist render row for each, hide new macro field in collapse
                            case(Object.keys(context.macros).length > 0):
                                return (
                                    <>
                                        {Object.keys(context.macros).map((name) => {
                                            return (
                                                <MacroRow
                                                    key={name}
                                                    name={name}
                                                    actions={context.macros[name]}
                                                />
                                            );
                                        })}

                                        <div className="text-center mt-3">
                                            <Button
                                                variant="secondary"
                                                className="mt-3 mx-auto"
                                                onClick={openNewMacro}
                                            >
                                                <i className="bi-plus-lg"></i>
                                            </Button>
                                        </div>
                                        <Collapse in={show}>
                                            <div className="p-3">
                                                <NewMacroField />
                                            </div>
                                        </Collapse>
                                    </>
                                );
                            // If no macros exist show new macro field, no collapse
                            default:
                                return <NewMacroField />;
                        }
                    })()}
                </div>

            );
        default:
            return (
                <>
                    <Button
                        variant="danger"
                        className={ recording ? "mb-5 mx-auto" : "d-none" }
                        onClick={finishRecording}
                    >
                        Finish Recording
                    </Button>

                    <RecordMacroModal />
                </>
            );
    }
};


export default Macros;
