import React, { useState, useContext } from 'react';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import { LoadingSpinner } from 'util/animations';
import { ApiCardContext } from 'root/ApiCardContext';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';

export let showLogModal;

const LogModal = () => {
    // Get function to make API calls
    const { send_command } = useContext(ApiCardContext);

    // Get node name from URL (status.metadata.id may contain a different name
    // than django database if new config was uploaded without updating django)
    const [nodeName] = useState(window.location.pathname.split('/')[2]);

    // Create visibility state
    const [visible, setVisible] = useState(false);
    const [log, setLog] = useState(null);

    // Create log level state
    const [logLevel, setLogLevel] = useState('ERROR')

    showLogModal = async () => {
        setVisible(true);
        await downloadLog();
    };

    const downloadLog = async () => {
        const response = await fetch(`/get_log/${nodeName}`);
        if (response.status !== 200) {
            const error = await response.json();
            setLog(error.message);
            console.error(`${error.message} (status ${response.status})`);
        }
        const data = await response.json();
        setLog(data.message);
    };

    const refresh = async () => {
        setLog(null);
        await downloadLog();
    };

    const changeLogLevel = async () => {
        const payload = {
            command: 'set_log_level',
            log_level: logLevel
        };
        const response = await send_command(payload);
        const data = await response.json();
        console.log(data);
        if (response.status === 200) {
            await send_command({command: 'reboot'});
            alert('Log level changed, rebooting node')
        } else {
            alert('Failed to change log level')
        }
    };

    return (
        <Modal
            show={visible}
            onHide={() => setVisible(false)}
            centered
            className={'log-modal overflow-x-scroll'}
        >
            <HeaderWithCloseButton
                title="Node Log"
                onClose={() => setVisible(false)}
            />

            <Modal.Body className="d-flex flex-column text-center">
                {log ? (
                    <>
                        <pre className='text-start section p-3 mb-2'>
                            {log}
                        </pre>

                        <Button className="mx-auto" onClick={refresh}>
                            Refresh
                        </Button>

                        <div className="mx-auto mt-4">
                            <span className="fs-5">
                                Set Log Level
                            </span>
                            <InputGroup className="mx-auto">
                                <Form.Select
                                    value={logLevel}
                                    onChange={(e) => setLogLevel(e.target.value)}
                                    className="text-center"
                                >
                                    <option value="CRITICAL">Critical</option>
                                    <option value="ERROR">Error</option>
                                    <option value="WARNING">Warning</option>
                                    <option value="INFO">Info</option>
                                    <option value="DEBUG">Debug</option>
                                </Form.Select>
                                <Button onClick={changeLogLevel}>
                                    Change
                                </Button>
                            </InputGroup>
                        </div>
                    </>
                ) : (
                    <>
                        <span>
                            Downloading log - this may take a few minutes
                        </span>
                        <LoadingSpinner size="medium" classes={['my-3']} />
                    </>
                )}
            </Modal.Body>
        </Modal>
    );
};

export default LogModal;
