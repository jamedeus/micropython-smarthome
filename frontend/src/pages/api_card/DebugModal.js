import React, { useContext, useState } from 'react';
import Modal from 'react-bootstrap/Modal';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';
import { ApiCardContext } from 'root/ApiCardContext';
import { LoadingSpinner } from 'util/animations';

export let showDebugModal;

const DebugModal = () => {
    // Get function to send API call to node
    const {send_command} = useContext(ApiCardContext);

    // Create visibility state
    const [visible, setVisible] = useState(false);
    const [attributes, setAttributes] = useState(null);

    showDebugModal = async (id) => {
        setAttributes(null);
        setVisible(true);
        const response = await send_command({
            command: 'get_attributes',
            instance: id
        });
        const data = await response.json();
        setAttributes(data);
    };

    return (
        <Modal show={visible} onHide={() => setVisible(false)} centered>
            <HeaderWithCloseButton
                title="Debug"
                onClose={() => setVisible(false)}
            />

            <Modal.Body className="d-flex flex-column mx-auto text-center">
                {attributes ? (
                    <pre className='d-inline-block text-start section p-3 mb-2'>
                        {JSON.stringify(attributes, null, 4)}
                    </pre>
                ) : (
                    <LoadingSpinner size="medium" classes={['my-3']} />
                )}
            </Modal.Body>
        </Modal>
    );
};

export default DebugModal;
