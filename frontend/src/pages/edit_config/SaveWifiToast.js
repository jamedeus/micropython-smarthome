import React, { useContext } from 'react';
import { EditConfigContext } from '../../EditConfigContext';
import Toast from 'react-bootstrap/Toast';
import Button from 'react-bootstrap/Button';
import { send_post_request } from 'util/django_util';

const SaveWifiToast = () => {
    const {
        config,
        showWifiToast,
        setShowWifiToast
    } = useContext(EditConfigContext);

    // Submit handler, post credentials to backend and close toast
    const setWifiCredentials = () => {
        send_post_request(
            "/set_default_credentials",
            {ssid: config.wifi.ssid, password: config.wifi.password}
        );
        setShowWifiToast(false);
    };

    const closeToast = () => {
        setShowWifiToast(false);
    };

    return (
        <Toast
            show={showWifiToast}
            onClose={closeToast}
            autohide
            delay={60000}
            className="fixed-bottom text-center mx-auto mb-3"
        >
            <Toast.Body>
                Save default wifi credentials?<br/>
                (pre-loaded on all future configs)<br/>
                <Button
                    variant="primary"
                    size="sm"
                    className="mx-2 mt-2"
                    onClick={setWifiCredentials}
                >
                    Yes
                </Button>
                <Button
                    variant="secondary"
                    size="sm"
                    className="mx-2 mt-2"
                    onClick={closeToast}
                >
                    No
                </Button>
            </Toast.Body>
        </Toast>
    );
};

export default SaveWifiToast;
