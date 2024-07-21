import React, { useState } from 'react';
import Modal from 'react-bootstrap/Modal';
import { sleep } from 'util/helper_functions';
import { send_post_request } from 'util/django_util';
import { showErrorModal } from 'modals/ErrorModal';
import { HeaderStaticBackdrop } from 'modals/HeaderComponents';
import { LoadingSpinner, CheckmarkAnimation } from 'util/animations';

export let uploadConfigFile, showUploadModal, showUploadSuccess, closeUploadModal;

const UploadModal = () => {
    // Create state for modal visibility, loading/success animation
    const [visible, setVisible] = useState(false);
    const [uploadComplete, setUploadComplete] = useState(false);

    // Show modal with loading animation
    showUploadModal = () => {
        setUploadComplete(false);
        setVisible(true);
    };

    showUploadSuccess = () => {
        setUploadComplete(true);
    };

    closeUploadModal = () => {
        setVisible(false);
    };

    // Takes config filename and target IP address, uploads file to node
    // If optional reupload bool is true no entry is created in the database
    // Shows modal with loading animation until complete, then checkmark animation
    uploadConfigFile = async (filename, targetIP, reupload=false, onComplete=null) => {
        showUploadModal();

        // Upload config file to target IP address
        // Add /True to endpoint if reuploading (skips adding to database)
        const response = await send_post_request(
            reupload ? '/upload/True' : '/upload',
            {config: filename, ip: targetIP}
        );

        // If upload successful, show success animation and reload page
        if (response.ok) {
            // Change title, show success animation
            showUploadSuccess();

            // Wait for animation to complete
            await sleep(1200);

            // Call onComplete handler if given, hide upload modal
            if (onComplete) {
                console.log("Calling onComplete");
                onComplete();
            }
            closeUploadModal();

        // Unable to upload because of filesystem error on node
        } else if (response.status == 409) {
            const error = await response.json();
            // Hide upload modal, show response in error modal
            closeUploadModal();
            showErrorModal({
                title: "Upload Failed",
                error: "failed",
                body: error.message
            });

        // Unable to upload because node is unreachable
        } else if (response.status == 404) {
            // Hide upload modal, show error modal
            closeUploadModal();
            showErrorModal({
                title: "Connection Error",
                error: "unreachable",
                body: targetIP
            });

        // Other error: show in alert, close modal
        } else {
            const error = await response.json();
            alert(error.message);
            closeUploadModal();
        }
    };

    return (
        <Modal
            show={visible}
            onHide={closeUploadModal}
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

export default UploadModal;
