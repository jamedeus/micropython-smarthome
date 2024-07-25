import React, { useState } from 'react';
import Toast from 'react-bootstrap/Toast';
import { sleep } from 'util/helper_functions';
import uploadConfigFile from 'util/upload_config';

export let uploadConfigWithToast;

const ReuploadToast = () => {
    const [ display, setDisplay ] = useState('');
    const [ visible, setVisible ] = useState(false);

    const closeToast = () => {
        setVisible(false);
    };

    // Takes config filename and target IP address, uploads file to node
    // Shows toast with name and IP, changes to success message when complete
    uploadConfigWithToast = async (filename, targetIP) => {
        setDisplay(`Reuploading ${filename} to ${targetIP}...`);
        setVisible(true);
        const success = await uploadConfigFile(filename, targetIP, true);
        if (success) {
            setVisible(true);
            setDisplay(`Finished reuploading ${filename}`);
            await sleep(5000);
        }
        closeToast();
    };

    return (
        <Toast
            show={visible}
            onClose={closeToast}
            className="fixed-bottom text-center mx-auto mb-3"
        >
            <Toast.Body>
                {display}
            </Toast.Body>
        </Toast>
    );
};

export default ReuploadToast;
