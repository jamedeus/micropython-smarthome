import React, { useContext } from 'react';
import Dropdown from 'react-bootstrap/Dropdown';
import { UploadModalContext } from 'modals/UploadModal';
import { ErrorModalContext } from 'modals/ErrorModal';
import { sleep } from 'util/helper_functions';
import { DesktopModal } from 'modals/DesktopIntegrationModal';
import { RestoreModal } from 'modals/RestoreModal';
import { WifiModal } from 'modals/WifiModal';
import { GpsModal } from 'modals/GpsModal';

const Header = () => {
    // Get callbacks for upload and error modals
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
            <Dropdown align="end" className="my-auto">
                <Dropdown.Toggle variant="light" id="settings-button">
                    <i className="bi-gear-fill"></i>
                </Dropdown.Toggle>
                <Dropdown.Menu>
                    <WifiModal />
                    <GpsModal />
                    <Dropdown.Item onClick={reuploadAll}>Re-upload all</Dropdown.Item>
                    <RestoreModal />
                    <DesktopModal />
                </Dropdown.Menu>
            </Dropdown>
        </div>
    );
};


export default Header;
