import React from 'react';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import { showUploadModal, showUploadSuccess, closeUploadModal } from 'modals/UploadModal';
import { showErrorModal } from 'modals/ErrorModal';
import { sleep } from 'util/helper_functions';
import { showDesktopModal } from './DesktopIntegrationModal';
import { showRestoreModal } from './RestoreModal';
import { showWifiModal } from './WifiModal';
import { showGpsModal } from './GpsModal';

const Header = () => {
    const reuploadAll = async () => {
        // Show upload modal with loading spinner
        showUploadModal();

        // Send request, receive report on which uploads succeeded/failed
        const response = await fetch("/reupload_all");
        const report = await response.json();
        console.log(report);

        // Change title, show success animation, close modal when complete
        showUploadSuccess();
        await sleep(1200);
        closeUploadModal();

        // If any failed, show error modal with names and failure reasons
        if (Object.keys(report.failed).length !== 0) {
            showErrorModal({
                title: "Failed Uploads",
                error: "failed_upload_all",
                body: report.failed
            });
        }
    };

    // Render full layout with metadata, wifi, IR Blaster, and instance cards
    return (
        <div className="d-flex justify-content-between">
            <Button style={{visibility: "hidden"}}>
                <i className="bi-chevron-left"></i>
            </Button>
            <h1 className="my-3">Configure Nodes</h1>
            <Dropdown align="end" className="my-auto">
                <Dropdown.Toggle variant="light" id="settings-button">
                    <i className="bi-gear-fill"></i>
                </Dropdown.Toggle>
                <Dropdown.Menu>
                    <Dropdown.Item onClick={() => showWifiModal()}>
                        Set WIFI credentials
                    </Dropdown.Item>
                    <Dropdown.Item onClick={() => showGpsModal()}>
                        Set GPS coordinates
                    </Dropdown.Item>
                    <Dropdown.Item onClick={reuploadAll}>
                        Re-upload all
                    </Dropdown.Item>
                    <Dropdown.Item onClick={() => showRestoreModal()}>
                        Restore config
                    </Dropdown.Item>
                    <Dropdown.Item onClick={() => showDesktopModal()}>
                        Desktop integration
                    </Dropdown.Item>
                </Dropdown.Menu>
            </Dropdown>
        </div>
    );
};


export default Header;
