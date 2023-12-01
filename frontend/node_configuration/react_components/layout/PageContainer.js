import React, { useState, useContext } from 'react';
import { ConfigContext } from 'root/ConfigContext';
import Button from 'react-bootstrap/Button';
import { send_post_request, edit_existing, target_node_ip } from 'root/django_util';
import Page1 from './Page1';
import Page2 from './Page2';
import Page3 from './Page3';
import { ApiTargetModalContextProvider, ApiTargetRuleModal } from 'modals/ApiTargetRuleModal';
import { ErrorModalContext, ErrorModal } from 'modals/ErrorModal';
import { UploadModalContext, UploadModal } from 'modals/UploadModal';

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

// Redirect back to overview page
function returnToOverview() {
    window.location.replace("/config_overview");
}

// Takes current config (state) object, compares with original from django
// context, returns True if changes have been made, false if no changes
function configModified(config) {
    // Get original config, compare with
    const original_config = JSON.parse(document.getElementById("config").textContent);
    return !areObjectsEqual(config, original_config);
}

// Takes 2 objects, recursively compares every sub-key, returns True if all identical
// Used to detect unsaved changes, show warning before returning to overview
function areObjectsEqual(obj1, obj2) {
    // Direct comparison for sub-keys on recursive calls
    if (obj1 === obj2) {
        return true;
    }

    // Not equal if failed comparison above and either is not object
    if (typeof(obj1) !== 'object' || typeof(obj2) !== 'object') {
        return false;
    }

    const keys1 = Object.keys(obj1);
    const keys2 = Object.keys(obj2);

    // Not equal if different number of keys
    if (keys1.length !== keys2.length) {
        return false;
    }

    // Confirm contain same keys
    // Call recursively with values of each key in both objects
    for (let key of keys1) {
        if (!keys2.includes(key) || !areObjectsEqual(obj1[key], obj2[key])) {
            return false;
        }
    }

    return true;
}

// Takes config (state) object, returns true if any keys are empty strings
// Used to detect empty fields before changing page
function hasEmptyFields(config) {
    for (let key in config) {
        if (typeof(config[key]) === 'object') {
            if (hasEmptyFields(config[key])) {
                console.log(`Empty field in ${key}`);
                return true;
            }
        } else if (config[key] === '') {
            console.log(`Empty field: ${key}`);
            return true;
        }
    }
    return false;
}

const PageContainer = () => {
    // Set default page, get callback to change visible page
    const [page, setPage] = useState(1);

    // Get full config (state object)
    const { config, setHighlightInvalid } = useContext(ConfigContext);

    // Get callbacks for upload modal
    const { setShowUpload, setUploadComplete } = useContext(UploadModalContext);

    // Get state and callback for error modal
    const { errorModalContent, setErrorModalContent } = useContext(ErrorModalContext);

    function prevPage() {
        // Go back to overview if current page is page 1
        if (page === 1) {
            // Show unsaved changes warning if user modified any inputs
            if (configModified(config)) {
                setErrorModalContent({
                    ...errorModalContent,
                    ["visible"]: true,
                    ["title"]: "Warning",
                    ["error"]: "unsaved_changes",
                    ["handleConfirm"]: returnToOverview
                });
            // Go directly to overview if no unsaved changes
            } else {
                returnToOverview();
            }
        // Otherwise go to previous page
        } else {
            setPage(page - 1);
        }
    }

    function nextPage() {
        // Don't go to page2 if empty inputs exist on page1
        if (page === 1 && hasEmptyFields(config)) {
            setHighlightInvalid(true);
            return;
        }
        // Clear highlight, go to next page
        setHighlightInvalid(false);
        setPage(page + 1);
    }

    // Post full config (state object) to backend when submit clicked
    async function submitButton() {
        console.log(config);

        // Overwrites if editing existing config, otherwise create config
        let response;
        if (edit_existing) {
            response = await send_post_request("generate_config_file/True", config);
        } else {
            response = await send_post_request("generate_config_file", config);
        }

        // If successfully created new config, redirect to overview
        if (!edit_existing && response.ok) {
            // Redirect back to overview where user can upload the newly-created config
            window.location.replace("/config_overview");

        // If successfully edited existing config, re-upload to target node
        } else if (edit_existing && response.ok) {
            upload();

        // If config with same name already exists, show modal allowing user to overwrite
        } else if (!edit_existing && response.status == 409) {
            setErrorModalContent({
                ...errorModalContent,
                ["visible"]: true,
                ["title"]: "Duplicate Warning",
                ["error"]: "duplicate",
                ["body"]: config.metadata.id,
                ["handleConfirm"]: confirmOverwriteDuplicate
            });

        // If other error, display in alert
        } else {
            alert(await response.text());
        }
    }

    // Handler for error modal overwrite button when showing duplicate error
    async function confirmOverwriteDuplicate() {
        // Convert friendly name into config filename
        const target_filename = `${config.metadata.id.toLowerCase().replace(' ', '-')}.json`;
        // Close error modal, delete existing file, resubmit
        setErrorModalContent({ ...errorModalContent, ["visible"]: false });
        await send_post_request("delete_config", `${target_filename}.json`);
        await submitButton();
    }

    async function upload() {
        // Show loading screen
        setShowUpload(true);

        // Convert friendly name into config filename
        const target_filename = `${config.metadata.id.toLowerCase().replace(' ', '-')}.json`;

        // Re-upload existing config
        var response = await send_post_request("upload/True", {config: target_filename, ip: target_node_ip});

        // If upload successful, show success animation and reload page
        if (response.ok) {
            // Change title, show success animation
            setUploadComplete(true);

            // Wait for animation to complete before reloading
            await sleep(1200);
            window.location.replace("/config_overview");

        // Unable to upload because of filesystem error on node
        } else if (response.status == 409) {
            const error = await response.text();
            // Hide upload modal, show response in error modal
            setShowUpload(false);
            setErrorModalContent({
                ...errorModalContent,
                ["visible"]: true,
                ["title"]: "Upload Failed",
                ["error"]: "failed",
                ["body"]: error
            });

        // Unable to upload because node is unreachable
        } else if (response.status == 404) {
            // Hide upload modal, show error modal
            setShowUpload(false);
            setErrorModalContent({
                ...errorModalContent,
                ["visible"]: true,
                ["title"]: "Connection Error",
                ["error"]: "unreachable",
                ["body"]: target_node_ip
            });

        // Other error, show in alert
        } else {
            alert(await response.text());

            // Hide modal allowing user to access page again
            setShowUpload(false);
        }
    }

    return (
        <ApiTargetModalContextProvider>
            <div className="d-flex flex-column vh-100">
                <h1 className="text-center pt-3 pb-4">{document.title}</h1>

                {/* Visible page */}
                {(() => {
                    switch(page) {
                        case 1:
                            console.log("rendering page1");
                            return <Page1 />;
                        case 2:
                            console.log("rendering page2");
                            return <Page2 />;
                        case 3:
                            console.log("rendering page3");
                            return <Page3 />;
                    }
                })()}

                {/* Change page buttons
                TODO modify SCSS so disabled changes color to grey */}
                <div className="d-flex justify-content-between mx-3 mt-auto">
                    <Button variant="primary" className="mb-4" onClick={prevPage}>Back</Button>
                    {(() => {
                        if (page === 3) {
                            return <Button variant="primary" className="mb-4" onClick={submitButton}>Submit</Button>;
                        }
                    })()}
                    <Button variant="primary" className="mb-4" onClick={nextPage} disabled={page === 3}>Next</Button>
                </div>
            </div>
            <ApiTargetRuleModal />
            <UploadModal />
            <ErrorModal />
        </ApiTargetModalContextProvider>
    );
};

export default PageContainer;
