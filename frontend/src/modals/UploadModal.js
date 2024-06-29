import React, { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Modal from 'react-bootstrap/Modal';
import { sleep } from 'util/helper_functions';
import { send_post_request } from 'util/django_util';
import { ErrorModalContext } from 'modals/ErrorModal';
import { HeaderStaticBackdrop } from 'modals/HeaderComponents';
import { LoadingSpinner, CheckmarkAnimation } from 'util/animations';

export const UploadModalContext = createContext();

export const UploadModalContextProvider = ({ children }) => {
    // Create state objects for upload modal visibility, status
    const [showUpload, setShowUpload] = useState(false);
    const [uploadComplete, setUploadComplete] = useState(false);

    const handleClose = () => {
        setShowUpload(false);
    };

    // Resets animation before showing modal
    const handleShow = () => {
        setUploadComplete(false);
        setShowUpload(true);
    };

    return (
        <UploadModalContext.Provider value={{
            showUpload,
            uploadComplete,
            setUploadComplete,
            handleClose,
            handleShow
        }}>
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
        <Modal
            show={showUpload}
            onHide={handleClose}
            backdrop="static"
            keyboard={false}
            centered
        >
            {uploadComplete ?
                <HeaderStaticBackdrop title="Upload Complete" /> :
                <HeaderStaticBackdrop title="Uploading..." />
            }
            <Modal.Body className="d-flex justify-content-center mb-4">
                {uploadComplete ?
                    <CheckmarkAnimation size="large" color="green" /> :
                    <LoadingSpinner size="medium" />
                }
            </Modal.Body>
        </Modal>
    );
};

// Custom hook that returns upload function
export const useUploader = () => {
    // Get callbacks for upload modal
    const { handleShow, handleClose, setUploadComplete } = useContext(UploadModalContext);

    // Get state and callback for error modal
    const { errorModalContent, setErrorModalContent } = useContext(ErrorModalContext);

    // Takes config filename and target IP address, uploads file to node
    // If optional reupload bool is true no entry is created in the database
    // Shows modal with loading animation while waiting, changes to success animation when complete
    async function upload(filename, targetIP, reupload=false, onComplete=null) {
        // Show modal with loading animation
        handleShow();

        // Set correct endpoint based on upload arg
        // Default: Upload and create new database entry if successful
        // Reupload: Upload without modifying database
        let endpoint = "upload";
        if (reupload) {
            endpoint = "upload/True";
        }

        // Upload config file to target IP address
        const response = await send_post_request(
            endpoint,
            {config: filename, ip: targetIP}
        );

        // If upload successful, show success animation and reload page
        if (response.ok) {
            // Change title, show success animation
            setUploadComplete(true);

            // Wait for animation to complete
            await sleep(1200);

            // Call onComplete handler if given, hide upload modal
            if (onComplete) {
                console.log("Calling onComplete");
                onComplete();
            }
            handleClose();

        // Unable to upload because of filesystem error on node
        } else if (response.status == 409) {
            const error = await response.text();
            // Hide upload modal, show response in error modal
            handleClose();
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
            handleClose();
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
            handleClose();
        }
    }

    return { upload };
};
