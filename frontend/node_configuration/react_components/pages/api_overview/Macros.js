import React, { useState, useContext } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import FloatingLabel from 'react-bootstrap/FloatingLabel';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';
import { ApiOverviewContext } from 'root/ApiOverviewContext';
import { EditMacroModalContext } from 'modals/EditMacroModal';
import { toTitle, sleep } from 'util/helper_functions';
import { ButtonSpinner, CheckmarkAnimation } from 'util/animations';


const MacroRow = ({ name, actions }) => {
    // Get callback to delete macro context
    const { deleteMacro } = useContext(ApiOverviewContext);

    // Get callback to open edit macro modal
    const { openEditMacroModal } = useContext(EditMacroModalContext);

    // Create state objects for button animations
    const [runAnimation, setRunAnimation] = useState("false");
    const [deleteAnimation, setDeleteAnimation] = useState("false");

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
        setDeleteAnimation("loading");

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
        }
    };

    return (
        <div id={name} className="d-flex mb-3">
            <h3 className="mx-auto my-auto">{toTitle(name)}</h3>
            <Button variant="primary" className="btn-macro mx-3" onClick={run}>
                {(() => {
                    switch(runAnimation) {
                        case("loading"):
                            return <ButtonSpinner />;
                        case("complete"):
                            return <CheckmarkAnimation size="small" />;
                        default:
                            return "Run";
                    }
                })()}
            </Button>
            <Button variant="primary" className="btn-macro mx-3" onClick={edit}>Edit</Button>
            <Button variant="danger" className="btn-macro mx-3" onClick={del}>
                {(() => {
                    switch(deleteAnimation) {
                        case("loading"):
                            return <ButtonSpinner />;
                        default:
                            return <i className="bi-trash"></i>;
                    }
                })()}
            </Button>
        </div>
    );
};

MacroRow.propTypes = {
    name: PropTypes.string,
    actions: PropTypes.array
};


const Macros = () => {
    // Get django context + record macro state and callback
    const { context, recording, setRecording } = useContext(ApiOverviewContext);

    // Create state object to set collapse visibility
    const [show, setShow] = useState(false);

    // Create state object for new macro name input
    const [newMacroName, setNewMacroName] = useState("");

    const startRecording = () => {
        setRecording(newMacroName);
    };

    const finishRecording = () => {
        setRecording("");
    }


    return (
        <>
            <div className={ recording ? "d-none" : "text-center section p-3 mx-auto mb-5"}>
                {Object.keys(context.macros).map((name) => {
                    return <MacroRow key={name} name={name} actions={context.macros[name]} />;
                })}

                <div className="text-center mt-3">
                    <Button
                        variant="secondary"
                        className="mt-3 mx-auto"
                        onClick={() => setShow(!show)}
                    >
                        <i className="bi-plus-lg"></i>
                    </Button>
                </div>
                <Collapse in={show}>
                    <div className="p-3">
                        <div className="form-floating mb-3">
                            <FloatingLabel label="New macro name">
                                <Form.Control
                                    type="text"
                                    value={newMacroName}
                                    placeholder="New macro name"
                                    onChange={(e) => setNewMacroName(e.target.value)}
                                />
                            </FloatingLabel>
                            <div id="invalid-name" className="invalid-feedback">
                                Name already in use
                            </div>
                        </div>
                        <Button
                            variant="success"
                            disabled={newMacroName.length === 0}
                            onClick={startRecording}
                        >
                            Start Recording
                        </Button>
                    </div>
                </Collapse>
            </div>

            <Button
                variant="danger"
                className={ recording ? "mb-5 mx-auto" : "d-none" }
                onClick={finishRecording}
            >
                Finish Recording
            </Button>
        </>
    );
};


export default Macros;
