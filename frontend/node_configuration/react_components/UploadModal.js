import React, { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Modal from 'react-bootstrap/Modal';

export const UploadModalContext = createContext();

export const UploadModalContextProvider = ({ children }) => {
    // Create state objects for upload modal visibility, status
    const [showUpload, setShowUpload] = useState(false);
    const [uploadComplete, setUploadComplete] = useState(false);

    const handleClose = () => {
        setShowUpload(false);
    };

    return (
        <UploadModalContext.Provider value={{ showUpload, setShowUpload, uploadComplete, setUploadComplete, handleClose }}>
            {children}
        </UploadModalContext.Provider>
    );
};

UploadModalContextProvider.propTypes = {
    children: PropTypes.node,
}

export const UploadModal = () => {
    // Get state object that determines modal contents
    const { showUpload, uploadComplete, handleClose } = useContext(UploadModalContext);

    return (
        <Modal show={showUpload} onHide={handleClose} centered>
            <Modal.Header className="justify-content-between">
                <button type="button" className="btn-close" style={{visibility: "hidden"}}></button>
                <h5 className="modal-title">Uploading...</h5>
                <button type="button" className="btn-close" onClick={handleClose}></button>
            </Modal.Header>

            <Modal.Body className="d-flex justify-content-center mb-4">
                {(() => {
                    switch (uploadComplete) {
                        case false:
                            return (
                                <div className="spinner-border" style={{width: "3rem", height: "3rem"}} role="status">
                                    <span className="visually-hidden">Loading...</span>
                                </div>
                            );
                        case true:
                            return (
                                <svg className="checkmark mx-auto" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                                    <circle className="checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
                                    <path className="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                                </svg>
                            );
                    }
                })()}
            </Modal.Body>
        </Modal>
    );
};
