import React, { useState } from 'react';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';
import { LoadingSpinner } from 'util/animations';

export let showLogModal;

const LogModal = () => {
    // Get node name from URL (status.metadata.id may contain a different name
    // than django database if new config was uploaded without updating django)
    const [nodeName] = useState(window.location.pathname.split('/')[2]);

    // Create visibility state
    const [visible, setVisible] = useState(false);
    const [log, setLog] = useState(null);

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
