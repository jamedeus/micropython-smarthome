import React, { useEffect } from 'react';
import Button from 'react-bootstrap/Button';
import { LoadingSpinner } from 'util/animations';
import { parse_dom_context, getCookie } from 'util/django_util';

const App = () => {
    const target_ip = parse_dom_context('target_ip');

    async function retryConnection() {
        const payload = {'command': 'status', 'target': target_ip};

        const response= await fetch('/send_command', {
            method: 'POST',
            body: JSON.stringify(payload),
            headers: { 'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json',
                "X-CSRFToken": getCookie('csrftoken') }
        });
        const data = await response.json();

        if (data != "Error: Unable to connect.") {
            location.reload();
        }
    }

    // Retry every 5 seconds
    useEffect(() => {
        const timer = setInterval(retryConnection, 5000);
        return () => clearInterval(timer);
    }, []);

    return (
        <div className="d-flex flex-column vh-100">
            <div className="d-flex justify-content-between">
                <Button
                    className="my-auto"
                    variant="dark"
                    onClick={() => window.location.href = '/api'}
                >
                    <i className="bi-chevron-left"></i>
                </Button>
                <h1 className="my-3">
                    Connection Failed
                </h1>
                <Button
                    className="my-auto"
                    variant="dark"
                    disabled
                >
                    <i className="bi-list"></i>
                </Button>
            </div>

            <div className="d-flex flex-column h-100">
                <div className="mt-auto">
                    <p className="text-center mb-0">
                        This page will reload automatically when the node is available
                    </p>
                    <div className="d-flex justify-content-center">
                        <LoadingSpinner size="medium" classes={['my-2']} />
                    </div>
                </div>

                <div className="d-flex flex-column my-auto">
                    <h2 className="text-center mt-auto mb-3">
                        Troubleshooting
                    </h2>
                    <ul className="mx-auto">
                        <li>
                            Unplug the node, plug back in, make sure the red light is on
                        </li>
                        <li>
                            If the blue light stays on 30+ seconds there is a network issue
                        </li>
                        <ul>
                            <li>Is your 2.4 GHz network available?</li>
                            <li>Can you connect to the internet?</li>
                            <li>Did the SSID or password change?</li>
                        </ul>
                    </ul>
                </div>

                <div className="d-flex justify-content-center mt-auto mb-3">
                    <Button
                        variant="success"
                        onClick={() => window.location.href = '/api'}
                    >
                        Back to Overview
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default App;
