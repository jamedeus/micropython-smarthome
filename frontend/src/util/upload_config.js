import { send_post_request } from 'util/django_util';
import { showErrorModal } from 'modals/ErrorModal';
import { showErrorToast } from 'util/ErrorToast';

// Takes config filename and target IP address, uploads file to node
// If optional reupload bool is true no entry is created in the database
// Returns true if upload succeeds, false if error
const uploadConfigFile = async (filename, targetIP, reupload=false) => {
    // Upload config file to target IP address
    // Add /True to endpoint if reuploading (skips adding to database)
    const response = await send_post_request(
        reupload ? '/upload/True' : '/upload',
        {config: filename, ip: targetIP}
    );

    // If upload successful return true
    if (response.ok) {
        return true;

    // Unable to upload because of filesystem error on node
    } else if (response.status == 409) {
        const error = await response.json();
        showErrorModal({
            title: "Upload Failed",
            error: "failed",
            body: error.message
        });
        return false;

    // Unable to upload because node is unreachable
    } else if (response.status == 404) {
        showErrorModal({
            title: "Connection Error",
            error: "unreachable",
            body: targetIP
        });
        return false;

    // Other error: show in error toast
    } else {
        const error = await response.json();
        showErrorToast(error.message);
        return false;
    }
};

export default uploadConfigFile;
