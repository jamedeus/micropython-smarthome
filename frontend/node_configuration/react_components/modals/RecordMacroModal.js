import React, { useContext, useState } from 'react';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import { ApiOverviewContext } from 'root/ApiOverviewContext';
import { getCookie } from 'util/django_util';


export const RecordMacroModal = () => {
    // Get context object, start_recording key contains bool that toggles to true
    // when recording started (but not when returning to overview from node page)
    const { context } = useContext(ApiOverviewContext);

    // Show modal if start_recording is true and skip instructions cookie not set
    let visible = false;
    if (context.start_recording && !getCookie("skip_instructions")) {
        visible = true;
    }

    // Create state object to control visibility
    const [ show, setShow ] = useState(visible);

    // Create state object for checkbox
    const [ checked, setChecked ] = useState(false);

    // Hide modal, set skip_instructions cookie if box was checked
    const handleClose = () => {
        setShow(false);
        if (checked) {
            fetch('/skip_instructions');
        };
    }

    return (
        <Modal show={show} onHide={handleClose} centered className="modal-fit-contents">
            <Modal.Header className="justify-content-between pb-0">
                <h3 className="modal-title mx-auto mb-0">Macro Instructions</h3>
            </Modal.Header>

            <Modal.Body className="pb-0">
                <div className="section p-3">
                    <p className="text-center">Use the interface as you normally would<br/>to record actions.</p>
                    <ul className="text-start">
                        <li>Change rules, turn devices on/off,<br/>and enable/disable things</li>
                        <li>Don&apos;t worry about conflicts, only<br/>the last change will be saved</li>
                        <li>Example: If a light is turned off, then<br/>turned on, only on is saved</li>
                    </ul>
                    <p className="text-center">When you&apos;re done, return to the<br/>overview and click &ldquo;Finish Recording&rdquo;.</p>
                    <p className="text-center">You can always click the edit button<br/>later to delete actions or record more.</p>
                </div>
                <div className="d-flex flex-column pt-3 pb-2">
                    <Form.Check
                        id="dontShowAgain"
                        type="checkbox"
                        label="Don't show again"
                        checked={checked}
                        onChange={() => setChecked(!checked)}
                    />
                </div>
            </Modal.Body>
            <Modal.Footer className="mx-auto pt-0">
                <Button variant="success" onClick={handleClose} >
                    OK
                </Button>
            </Modal.Footer>
        </Modal>
    );
};
