import { useContext, useEffect } from 'react';
import { ApiCardContext } from 'root/ApiCardContext';
import { showErrorModal, hideErrorModal } from 'modals/ErrorModal';


export const UpdateStatus = () => {
    const {status, setStatus, overview} = useContext(ApiCardContext);

    // Track if error modal is open, close modal when connection reestablished
    let targetOffline = false;

    function show_connection_error() {
        showErrorModal({
            title: "Connection Error",
            error: "connection_error",
            handleConfirm: overview
        });
    }

    // Get current status object, overwrite state, update cards
    // Called every 5 seconds by effect below
    async function get_new_status() {
        try {
            const response = await fetch(`/get_status/${status.metadata.id}`);
            if (response.status !== 200) {
                const error = await response.text();
                throw new Error(`${error} (status ${response.status})`);
            }
            const data = await response.json();
            setStatus(data);
            console.log("update", data);
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
    }

    // Update state every 5 seconds
    useEffect(() => {
        const timer = setInterval(get_new_status, 5000);
        return () => clearInterval(timer);
    }, []);
};
