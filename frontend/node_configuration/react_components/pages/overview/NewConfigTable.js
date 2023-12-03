import React, { useContext, useState } from 'react';
import { OverviewContext } from 'root/OverviewContext';
import Row from 'react-bootstrap/Row';
import Form from 'react-bootstrap/Form';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';
import { send_post_request } from 'util/django_util';
import { ErrorModalContext } from 'modals/ErrorModal';
import { UploadModalContext } from 'modals/UploadModal';
import { sleep } from 'util/helper_functions';
import { formatIp } from 'util/validation';

const ipRegex = /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;


const NewConfigRow = ({ config }) => {
    // Get callbacks for error modal
    const { errorModalContent, setErrorModalContent } = useContext(ErrorModalContext);

    // Get callbacks for upload modal
    const { setShowUpload, setUploadComplete } = useContext(UploadModalContext);

    // Create state objects for IP field, submit button
    const [ipAddress, setIpAddress] = useState('');
    const [uploadEnabled, setUploadEnabled] = useState(false);

    // Takes config filename, opens modal to confirm deletion
    function show_delete_modal(filename) {
        setErrorModalContent({
            ...errorModalContent,
            ["visible"]: true,
            ["title"]: "Confirm Delete",
            ["error"]: "confirm_delete",
            ["handleConfirm"]: () => delete_config(filename)
        });
    }

    // Handler for confirm delete button in modal
    async function delete_config(filename) {
        let result = await send_post_request("delete_config", filename);

        // Refresh page if successfully deleted
        if (result.ok) {
            location.reload();

            // Show error if failed
        } else {
            const error = await result.text();

            setErrorModalContent({
                ...errorModalContent,
                ["visible"]: true,
                ["title"]: "Error",
                ["error"]: "failed",
                ["body"]: error
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

    // Handler for upload button
    async function upload() {
        // Show loading screen
        setShowUpload(true);

        // Upload new config to IP in IP address field
        var response = await send_post_request("upload/True", {config: config, ip: ipAddress});

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
                ["body"]: ipAddress
            });

        // Other error, show in alert
        } else {
            alert(await response.text());

            // Hide modal allowing user to access page again
            setShowUpload(false);
        }
    }

    // Return single table row with listeners to upload, delete config
    return (
        <tr id={config}>
            <td className="align-middle">
                <span className="form-control text-center">{config}</span>
            </td>
            <td className="align-middle">
                <Form.Control
                    type="text"
                    id={`${config}-ip`}
                    value={ipAddress}
                    onChange={(e) => setIp(e.target.value)}
                    className="text-center ip-input"
                    placeholder="xxx.xxx.x.xxx"
                />
            </td>
            <td className="min align-middle">
                <Button
                    variant="primary"
                    size="sm"
                    disabled={!uploadEnabled}
                    onClick={upload}
                >
                    Upload
                </Button>
            </td>
            <td className="min align-middle">
                <Button variant="danger" size="sm" onClick={() => show_delete_modal(config)}>
                    <i className="bi-trash"></i>
                </Button>
            </td>
        </tr>
    );
};


const NewConfigTable = () => {
    // Get django context
    const { context } = useContext(OverviewContext);

    // Set default collapse state
    const [open, setOpen] = useState(true);

    // Render full layout with metadata, wifi, IR Blaster, and instance cards
    return (
        <Row id="not_uploaded" className="section pt-2 px-0 mb-5">
            <h3 className="text-center my-1" onClick={() => setOpen(!open)}>Configs Ready to Upload</h3>
            <Collapse in={open}>
                <div>
                    <Table borderless hover size="sm" className="mt-3 mx-auto">
                        <thead>
                            <tr>
                                <th className="w-50"><span>Name</span></th>
                                <th className="w-50"><span>IP</span></th>
                                <th></th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {context.not_uploaded.map((config) => {
                                return <NewConfigRow config={config} />;
                            })}
                        </tbody>
                    </Table>
                </div>
            </Collapse>
        </Row>
    );
};


export default NewConfigTable;
