import React, { useState, useContext } from 'react';
import { ConfigContext } from './ConfigContext';
import Button from 'react-bootstrap/Button';
import { send_post_request, edit_existing, target_node_ip } from './django_util';
import Page1 from './Page1';
import Page2 from './Page2';
import Page3 from './Page3';
import { ApiTargetModalContextProvider, ApiTargetRuleModal } from './ApiTargetRuleModal';
import { ErrorModalContext, ErrorModal } from './ErrorModal';
import { UploadModalContext, UploadModal } from './UploadModal';

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

const PageContainer = () => {
    // Set default page, get callback to change visible page
    const [page, setPage] = useState(1);

    // Get full config (state object)
    const { config } = useContext(ConfigContext);

    // Get callbacks for upload modal
    const { setShowUpload, setUploadComplete } = useContext(UploadModalContext);

    // Get state and callback for error modal
    const { errorModalContent, setErrorModalContent } = useContext(ErrorModalContext);

    function prevPage() {
        // Go back to overview if current page is page 1
        // TODO add warning if editing and config modified
        if (page === 1) {
            window.location.replace("/config_overview");
        // Otherwise go to previous page
        } else {
            setPage(page - 1);
        }
    }

    function nextPage() {
        // TODO don't proceed if blank fields exist on page 1
        setPage(page + 1);
    }

    // Post full config (state object) to backend when submit clicked
    async function submitButton() {
        console.log(config)

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
            // TODO implement modal, remove submit button arg (handle in react)
            alert("Duplicate config name");
//             handle_duplicate_prompt(config.metadata.id, submit_button);

        // If other error, display in alert
        } else {
            alert(await response.text());
        }
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
            })

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
            })

        // Other error, show in alert
        } else {
            alert(await response.text());

            // Hide modal allowing user to access page again
            setShowUpload(false);
        };
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
                            return <Button variant="primary" className="mb-4" onClick={submitButton}>Submit</Button>
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
