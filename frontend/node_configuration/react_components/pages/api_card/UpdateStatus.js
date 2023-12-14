import { useContext, useEffect } from 'react';
import { ApiCardContext } from 'root/ApiCardContext';
import { ErrorModalContext } from 'modals/ErrorModal';


export const UpdateStatus = () => {
    const {status, setStatus, overview} = useContext(ApiCardContext);

    // Get state and callback for error modal
    const { errorModalContent, setErrorModalContent } = useContext(ErrorModalContext);

    // Track if error modal is open, close modal when connection reestablished
    let targetOffline = false;

    function show_connection_error() {
        setErrorModalContent({
            ...errorModalContent,
            ["visible"]: true,
            ["title"]: "Connection Error",
            ["error"]: "connection_error",
            ["handleConfirm"]: overview
        });
    }

    function hide_connection_error() {
        setErrorModalContent({
            ...errorModalContent,
            ["visible"]: false,
            ["title"]: "Connection Error",
            ["error"]: "connection_error"
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
                hide_connection_error();
                targetOffline = false;
            }
        } catch (error) {
            show_connection_error();
            targetOffline = true;
            console.error('Failed to update status:', error);
        }
    }

    // Update state every 5 seconds
    useEffect(() => {
        const timer = setInterval(get_new_status, 5000);
        return () => clearInterval(timer);
    }, []);
};
