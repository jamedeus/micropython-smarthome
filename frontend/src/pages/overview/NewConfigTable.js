import React, { useContext, useState } from 'react';
import PropTypes from 'prop-types';
import { OverviewContext } from 'root/OverviewContext';
import Row from 'react-bootstrap/Row';
import Form from 'react-bootstrap/Form';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';
import { send_post_request } from 'util/django_util';
import { showErrorModal, hideErrorModal } from 'modals/ErrorModal';
import { formatIp, ipRegex } from 'util/validation';
import { uploadConfigFile } from 'modals/UploadModal';

const NewConfigRow = ({ filename, friendlyName }) => {
    const { handleNewConfigUpload, deleteNewConfig } = useContext(OverviewContext);

    // Create state objects for IP field, submit button
    const [ipAddress, setIpAddress] = useState('');
    const [uploadEnabled, setUploadEnabled] = useState(false);

    // Create handler for upload button
    const uploadNewConfig = () => {
        const onUploadComplete = () => {
            handleNewConfigUpload(friendlyName, filename, ipAddress);
        };
        uploadConfigFile(filename, ipAddress, false, onUploadComplete);
    };

    // Takes config filename, opens modal to confirm deletion
    function show_delete_modal(filename) {
        showErrorModal({
            title: "Confirm Delete",
            error: "confirm_delete",
            handleConfirm: () => delete_config(filename)
        });
    }

    // Handler for confirm delete button in modal
    async function delete_config(filename) {
        let result = await send_post_request("delete_config", filename);

        // Remove filename from state if successfully deleted
        if (result.ok) {
            hideErrorModal();
            deleteNewConfig(filename);

        // Show error if failed
        } else {
            const error = await result.text();
            showErrorModal({
                title: "Error",
                error: "failed",
                body: error
            });
        }
    }

    // Takes current value of IP field, enables upload button
    // if passes regex, otherwise disables upload button
    const isIpValid = (ip) => {
        if (ipRegex.test(ip)) {
            setUploadEnabled(true);
        } else {
            setUploadEnabled(false);
        }
    };

    // Handler for IP address field, formats IP as user types
    const setIp = (value) => {
        // Format value entered by user
        const newIP = formatIp(ipAddress, value);
        // Enable upload button if IP is valid
        isIpValid(newIP);
        // Set IP in state object
        setIpAddress(newIP);
    };

    // Upload config if enter key pressed in IP input (ignore if IP invalid)
    const handleEnterKey = (e) => {
        if (e.key === "Enter" && uploadEnabled) {
            uploadNewConfig();
        }
    };

    // Return single table row with listeners to upload, delete config
    return (
        <tr id={filename}>
            <td className="align-middle">
                <span className="form-control text-center">{filename}</span>
            </td>
            <td className="align-middle">
                <Form.Control
                    type="text"
                    id={`${filename}-ip`}
                    value={ipAddress}
                    onChange={(e) => setIp(e.target.value)}
                    className="text-center ip-input"
                    placeholder="xxx.xxx.x.xxx"
                    onKeyDown={handleEnterKey}
                />
            </td>
            <td className="min align-middle">
                <Button
                    variant="primary"
                    size="sm"
                    disabled={!uploadEnabled}
                    onClick={uploadNewConfig}
                >
                    Upload
                </Button>
            </td>
            <td className="min align-middle">
                <Button
                    variant="danger"
                    size="sm"
                    onClick={() => show_delete_modal(filename)}
                >
                    <i className="bi-trash"></i>
                </Button>
            </td>
        </tr>
    );
};

NewConfigRow.propTypes = {
    filename: PropTypes.string.isRequired,
    friendlyName: PropTypes.string.isRequired
};

const NewConfigTable = () => {
    // Get django context
    const { context } = useContext(OverviewContext);

    // Set default collapse state
    const [open, setOpen] = useState(true);

    // Render full layout with metadata, wifi, IR Blaster, and instance cards
    return (
        <Row id="not_uploaded" className="text-center section pt-2 px-0 mb-5">
            <h3 className="text-center my-1" onClick={() => setOpen(!open)}>
                Configs Ready to Upload
            </h3>
            <Collapse in={open}>
                <div>
                    <Table borderless hover size="sm" className="mt-3 mx-auto">
                        <thead>
                            <tr>
                                <th className="w-50">Name</th>
                                <th className="w-50">IP</th>
                                <th></th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {context.not_uploaded.map((config) => {
                                return (
                                    <NewConfigRow
                                        key={config.filename}
                                        filename={config.filename}
                                        friendlyName={config.friendly_name}
                                    />
                                );
                            })}
                        </tbody>
                    </Table>
                </div>
            </Collapse>
        </Row>
    );
};

export default NewConfigTable;
