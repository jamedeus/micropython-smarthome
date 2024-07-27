import React, { useState } from 'react';
import Modal from 'react-bootstrap/Modal';
import { sleep } from 'util/helper_functions';
import { HeaderStaticBackdrop } from 'modals/HeaderComponents';
import { LoadingSpinner, CheckmarkAnimation } from 'util/animations';
import uploadConfigFile from 'util/upload_config';

export let uploadConfigWithModal, showUploadModal, showUploadSuccess, closeUploadModal;

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
    uploadConfigWithModal = async (filename, targetIP, reupload=false) => {
        showUploadModal();
        const success = await uploadConfigFile(filename, targetIP, reupload);
        if (success) {
            // Change title, show checkmark animation
            showUploadSuccess();

            // Wait for animation to complete, close modal
            await sleep(1200);
            closeUploadModal();
            return true;
        } else {
            closeUploadModal();
            return false;
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
