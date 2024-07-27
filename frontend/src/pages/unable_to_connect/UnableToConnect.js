import React, { useEffect } from 'react';
import Button from 'react-bootstrap/Button';
import { LoadingSpinner } from 'util/animations';
import { parse_dom_context } from 'util/django_util';

const App = () => {
    const target_node = parse_dom_context('target_node');

    const retryConnection = async () => {
        const response = await fetch(`/get_status/${target_node}`);
        if (response.ok) {
            window.location.reload();
        } else {
            const error = await response.json();
            console.log('Failed to connect:', error);
        }
    };

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
                    variant="adaptive"
                    onClick={() => window.location.href = '/api'}
                >
                    <i className="bi-chevron-left"></i>
                </Button>
                <h1 className="my-3">
                    Connection Failed
                </h1>
                <Button
                    className="my-auto"
                    variant="adaptive"
                    disabled
                >
                    <i className="bi-list"></i>
                </Button>
            </div>

            <div className="d-flex flex-column h-100 justify-content-evenly my-auto">
                <p className="text-center my-3">
                    This page will reload automatically when the node is available
                </p>

                <LoadingSpinner size="large" classes={['my-3']} />

                <div className="d-flex flex-column">
                    <h2 className="text-center mb-3">
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

                <div className="d-flex mx-auto mb-3">
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
