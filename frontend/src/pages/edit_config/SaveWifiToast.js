import React, { useContext } from 'react';
import { ConfigContext } from '../../ConfigContext';
import Toast from 'react-bootstrap/Toast';
import Button from 'react-bootstrap/Button';
import { send_post_request } from 'util/django_util';

const SaveWifiToast = () => {
    const {
        config,
        showWifiToast,
        setShowWifiToast
    } = useContext(ConfigContext);

    // Submit handler, post credentials to backend and close toast
    const setWifiCredentials = () => {
        send_post_request(
            "/set_default_credentials",
            {ssid: config.wifi.ssid, password: config.wifi.password}
        );
        setShowWifiToast(false);
    };

    return (
        <Toast
            show={showWifiToast}
            onClose={() => setShowWifiToast(false)}
            autohide
            delay={10000}
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
                    onClick={() => setShowWifiToast(false)}
                >
                    No
                </Button>
            </Toast.Body>
        </Toast>
    );
};

export default SaveWifiToast;
