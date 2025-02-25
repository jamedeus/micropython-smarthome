import { useState, useContext, useEffect } from 'react';
import { ApiCardContext } from 'root/ApiCardContext';
import { showErrorModal, hideErrorModal } from 'modals/ErrorModal';

export const UpdateStatus = () => {
    const {setStatus, overview} = useContext(ApiCardContext);

    // Get node name from URL (status.metadata.id may contain a different name
    // than django database if new config was uploaded without updating django)
    const [nodeName] = useState(window.location.pathname.split('/')[2]);

    // Track if error modal is open, close modal when connection reestablished
    let targetOffline = false;

    const show_connection_error = () => {
        showErrorModal({
            title: "Connection Error",
            error: "connection_error",
            handleConfirm: overview
        });
    };

    // Get current status object, overwrite state, update cards
    // Called every 5 seconds by effect below
    const get_new_status = async () => {
        try {
            const response = await fetch(`/get_status/${nodeName}`);
            if (response.status !== 200) {
                const error = await response.json();
                throw new Error(`${error.message} (status ${response.status})`);
            }
            const data = await response.json();
            setStatus(data.message);
            console.log("update", data.message);
            if (targetOffline) {
                hideErrorModal();
                targetOffline = false;
            }
        } catch (error) {
            if (!targetOffline) {
                show_connection_error();
                targetOffline = true;
            }
            console.error('Failed to update status:', error);
        }
    };

    // Update state every 5 seconds
    useEffect(() => {
        const timer = setInterval(get_new_status, 5000);
        return () => clearInterval(timer);
    }, []);
};
