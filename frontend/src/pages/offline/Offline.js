import React, { useEffect } from 'react';
import Button from 'react-bootstrap/Button';
import { LoadingSpinner } from 'util/animations';

const App = () => {
    const attemptReconnect = async () => {
        // Reload current page once index is available
        const response = await fetch(`/`);
        if (response.ok) {
            location.reload();
        }
    };

    // Try to reconnect every 15 seconds
    useEffect(() => {
        const timer = setInterval(attemptReconnect, 15000);
        return () => clearInterval(timer);
    }, []);

    return (
        <div className='d-flex flex-column vh-100'>
            <h1 className='text-center my-3'>Offline Mode</h1>

            <div className='d-flex flex-column h-100 my-auto'>
                <span className='text-center mt-auto'>
                    Please check your internet/VPN connection
                </span>

                <LoadingSpinner size='large' classes={['my-5']} />
                <span className='text-center'>
                    This page will reload automatically when reconnected
                </span>

                <Button
                    variant='success'
                    className='mx-auto mt-5 mb-auto'
                    onClick={attemptReconnect}
                >
                    Retry
                </Button>
            </div>
        </div>
    );
};

export default App;
