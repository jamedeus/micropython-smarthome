import React, { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Modal from 'react-bootstrap/Modal';
import { sleep } from 'util/helper_functions';
import { send_post_request } from 'util/django_util';
import { ErrorModalContext } from 'modals/ErrorModal';

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
};

export const UploadModal = () => {
    // Get state object that determines modal contents
    const { showUpload, uploadComplete, handleClose } = useContext(UploadModalContext);

    return (
        <Modal show={showUpload} onHide={handleClose} backdrop="static" keyboard={false} centered>
            <Modal.Header className="justify-content-between">
                {(() => {
                    switch (uploadComplete) {
                        case false:
                            return <h3 className="modal-title mx-auto">Uploading...</h3>;
                        case true:
                            return <h3 className="modal-title mx-auto">Upload Complete</h3>;
                    }
                })()}
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

// Custom hook that returns upload function
export const useUploader = () => {
    // Get callbacks for upload modal
    const { setShowUpload, setUploadComplete } = useContext(UploadModalContext);

    // Get state and callback for error modal
    const { errorModalContent, setErrorModalContent } = useContext(ErrorModalContext);

    // Takes config filename and target IP address, uploads file to node
    // If optional reupload bool is true no entry is created in the database
    // Shows modal with loading animation while waiting, changes to success animation when complete
    async function upload(filename, targetIP, reupload=false) {
        // Show modal with loading animation
        setShowUpload(true);

        // Set correct endpoint based on upload arg
        // Default: Upload and create new database entry if successful
        // Reupload: Upload without modifying database
        let endpoint = "upload";
        if (reupload) {
            endpoint = "upload/True";
        }

        // Upload config file to target IP address
        var response = await send_post_request(endpoint, {config: filename, ip: targetIP});

        // If upload successful, show success animation and reload page
        if (response.ok) {
            // Change title, show success animation
            setUploadComplete(true);

            // Wait for animation to complete before reloading
            await sleep(1200);
            window.location.replace("/config_overview");

            // Unable to upload because of filesystem error on node
        } else if (response.status == 409) {
            const error = await response.text();
            // Hide upload modal, show response in error modal
            setShowUpload(false);
            setErrorModalContent({
                ...errorModalContent,
                ["visible"]: true,
                ["title"]: "Upload Failed",
                ["error"]: "failed",
                ["body"]: error
            });

            // Unable to upload because node is unreachable
        } else if (response.status == 404) {
            // Hide upload modal, show error modal
            setShowUpload(false);
            setErrorModalContent({
                ...errorModalContent,
                ["visible"]: true,
                ["title"]: "Connection Error",
                ["error"]: "unreachable",
                ["body"]: targetIP
            });

            // Other error, show in alert
        } else {
            alert(await response.text());

            // Hide modal allowing user to access page again
            setShowUpload(false);
        }
    }

    return { upload };
};
