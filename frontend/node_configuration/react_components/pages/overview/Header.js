import React, { useContext } from 'react';
import Dropdown from 'react-bootstrap/Dropdown';
import { UploadModalContext } from 'modals/UploadModal';
import { ErrorModalContext } from 'modals/ErrorModal';

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

const Header = () => {
    // Get callbacks for upload modal and error modal
    const { setShowUpload, setUploadComplete } = useContext(UploadModalContext);
    const { errorModalContent, setErrorModalContent } = useContext(ErrorModalContext);

    async function reuploadAll() {
        // Show upload modal with loading spinner
        setUploadComplete(false);
        setShowUpload(true);

        // Send request, receive report on which uploads succeeded/failed
        let response = await fetch("/reupload_all");
        response = await response.json();
        console.log(response);

        // Change title, show success animation, close modal when complete
        setUploadComplete(true);
        await sleep(1200);
        setShowUpload(false);

        // If any failed, show error modal with names and failure reasons
        if (Object.keys(response.failed).length !== 0) {
            setErrorModalContent({
                ...errorModalContent,
                ["visible"]: true,
                ["title"]: "Failed Uploads",
                ["error"]: "failed_upload_all",
                ["body"]: response.failed
            });
        }
    }

    // Render full layout with metadata, wifi, IR Blaster, and instance cards
    return (
        <div className="d-flex justify-content-between">
            <button type="button" className="btn my-auto" id="back_button" style={{visibility: "hidden"}}><i className="bi-chevron-left"></i></button>
            <h1 className="my-3">Configure Nodes</h1>
            <Dropdown className="my-auto">
                <Dropdown.Toggle variant="dark" id="settings-button">
                    <i className="bi-gear-fill"></i>
                </Dropdown.Toggle>
                <Dropdown.Menu>
                    <Dropdown.Item>Set WIFI credentials</Dropdown.Item>
                    <Dropdown.Item>Set GPS coordinates</Dropdown.Item>
                    <Dropdown.Item onClick={reuploadAll}>Re-upload all</Dropdown.Item>
                    <Dropdown.Item>Restore config</Dropdown.Item>
                    <Dropdown.Item>Desktop integration</Dropdown.Item>
                </Dropdown.Menu>
            </Dropdown>
        </div>
    );
};


export default Header;
