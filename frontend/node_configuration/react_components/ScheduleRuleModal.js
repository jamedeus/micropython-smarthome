import React, { createContext, useContext, useState } from 'react';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';


export const ModalContext = createContext();

export const ModalContextProvider = ({ children }) => {
    // Create state objects for modal visibility, contents
    const [show, setShow] = useState(false);
    const [modalContent, setModalContent] = useState('');

    const handleShow = (content) => {
        setModalContent(content);
        setShow(true);
    };

    const handleClose = () => {
        setShow(false);
    };

    return (
        <ModalContext.Provider value={{ show, modalContent, handleShow, handleClose }}>
            {children}
        </ModalContext.Provider>
    );
};


export const ScheduleRuleModal = (contents) => {
    // Get context and callbacks
    const { show, handleShow, handleClose, modalContent } = useContext(ModalContext);
    console.log("Rendering schedule rule modal")

    return (
        <ModalContextProvider>
            <Modal show={show} onHide={handleClose} centered>
                <Modal.Header className="justify-content-between">
                    <button type="button" class="btn-close" style={{visibility: "hidden"}}></button>
                    <h5 class="modal-title">Schedule Rule</h5>
                    <button type="button" class="btn-close" onClick={() => handleClose()}></button>
                </Modal.Header>

                <Modal.Body>
                    {modalContent}
                </Modal.Body>

                <Modal.Footer className="mx-auto">
                    <div id="rule-buttons">
                        <Button variant="success" className="m-1">Submit</Button>
                        <Button variant="danger" className="m-1">Delete</Button>
                    </div>
                </Modal.Footer>
            </Modal>
        </ModalContextProvider>
    );
};
