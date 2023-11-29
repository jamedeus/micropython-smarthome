import React, { useState } from 'react';
import Button from 'react-bootstrap/Button';
import { submit } from './django_util';
import Page1 from './Page1';
import Page2 from './Page2';
import Page3 from './Page3';
import { ApiTargetModalContextProvider } from './ApiTargetRuleModal';


const PageContainer = () => {
    // Set default page, get callback to change visible page
    const [page, setPage] = useState(1);

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

    function submitButton() {
        submit();
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
        </ApiTargetModalContextProvider>
    );
};


export default PageContainer;
