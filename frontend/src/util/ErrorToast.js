import React, { useState } from 'react';
import Toast from 'react-bootstrap/Toast';

export let showErrorToast;

const ReuploadToast = () => {
    const [ error, setError ] = useState('');
    const [ timeout, setTimeout ] = useState(10000);
    const [ visible, setVisible ] = useState(false);

    const closeToast = () => {
        setVisible(false);
    };

    // Takes error message and milliseconds until hidden
    showErrorToast = async (error, duration) => {
        setError(error);
        setTimeout(duration);
        setVisible(true);
    };

    return (
        <Toast
            show={visible}
            autohide
            delay={timeout}
            onClose={closeToast}
            onClick={closeToast}
            bg={'danger'}
            className="fixed-bottom text-center mx-auto mb-3"
        >
            <Toast.Body>
                {error}
            </Toast.Body>
        </Toast>
    );
};

export default ReuploadToast;
