import React, { useState, useContext } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import FloatingLabel from 'react-bootstrap/FloatingLabel';
import Button from 'react-bootstrap/Button';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import Dropdown from 'react-bootstrap/Dropdown';
import DropdownButton from 'react-bootstrap/DropdownButton';
import Collapse from 'react-bootstrap/Collapse';
import { ApiOverviewContext } from 'root/ApiOverviewContext';
import { openEditMacroModal } from './EditMacroModal';
import { toTitle, sleep } from 'util/helper_functions';
import { LoadingSpinner, CheckmarkAnimation } from 'util/animations';
import { TransitionGroup, CSSTransition } from "react-transition-group";
import 'css/macros.css';

const MacroRow = ({ name }) => {
    // Get callback to delete macro context
    const { deleteMacro } = useContext(ApiOverviewContext);

    // Create state objects for button animations
    const [runAnimation, setRunAnimation] = useState("false");

    const runMacro = async () => {
        // Start loading animation
        setRunAnimation("loading");

        // Run macro
        const result = await fetch(`/run_macro/${name}`);

        // TODO handle failure
        if (result.status === 200) {
            // Start checkmark animation, wait until complete
            setRunAnimation("complete");
            await sleep(2000);

            // Return to original text
            // TODO fade out (handle in CSS)
            setRunAnimation("false");
        }
    };

    const delMacro = async () => {
        // Start loading animation
        setRunAnimation("loading");
        deleteMacro(name);
    };

    return (
        <div id={name} className="d-flex mb-3">
            <ButtonGroup className="macro-row">
                <Button onClick={runMacro} className="macro-button">
                    <h3 className="macro-name">
                        {(() => {
                            switch(runAnimation) {
                                case("loading"):
                                    return <LoadingSpinner size="small" />;
                                case("complete"):
                                    return <CheckmarkAnimation size="small" color="white" />;
                                default:
                                    return toTitle(name);
                            }
                        })()}
                    </h3>
                </Button>

                <DropdownButton
                    as={ButtonGroup}
                    title={<i className="bi-gear-fill"></i>}
                    align="end"
                    className="macro-options"
                >
                    <Dropdown.Item onClick={() => openEditMacroModal(name)}>
                        <i className="bi-pencil"></i> Edit
                    </Dropdown.Item>
                    <Dropdown.Item onClick={delMacro}>
                        <i className="bi-trash"></i> Delete
                    </Dropdown.Item>
                </DropdownButton>
            </ButtonGroup>
        </div>
    );
};

MacroRow.propTypes = {
    name: PropTypes.string.isRequired
};

const ExistingMacros = () => {
    const { context } = useContext(ApiOverviewContext);

    // Create state object to set collapse visibility
    const [show, setShow] = useState(false);

    const openNewMacro = async () => {
        // Toggle collapse visibility
        setShow(!show);
        // If collapse was previously closed focus input after opening
        if (!show) {
            await sleep(1);
            document.getElementById('new-macro-name').focus();
        }
    };

    return (
        <div className="text-center section p-3 mx-auto macro-container">
            <TransitionGroup>
                {Object.keys(context.macros).map((name) => {
                    return (
                        <CSSTransition
                            key={name}
                            timeout={200}
                            classNames='fade'
                        >
                            <MacroRow name={name} />
                        </CSSTransition>
                    );
                })}
            </TransitionGroup>

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
        </div>
    );
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

        // If name is available start recording
        if (response.status === 200) {
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

export const FinishRecordingButton = () => {
    const { recording, setRecording } = useContext(ApiOverviewContext);

    // Reset state, remove name from URL (prevent resuming if page refreshed)
    const finishRecording = () => {
        setRecording("");
        history.pushState({}, '', '/api');
    };

    return (
        <Button
            variant="danger"
            className={ recording ? "mb-5 mx-auto" : "d-none" }
            onClick={finishRecording}
        >
            Finish Recording
        </Button>
    );
};

const Macros = () => {
    // Get django context, state object for name of macro being recorded
    const { context } = useContext(ApiOverviewContext);

    // If macros exist render row for each, hide new macro field in collapse
    if (Object.keys(context.macros).length > 0) {
        return <ExistingMacros />;

    // If no macros exist show new macro field (no collapse)
    } else {
        return (
            <div className="text-center section p-3 mx-auto macro-container">
                <NewMacroField />
            </div>
        );
    }
};

export default Macros;
