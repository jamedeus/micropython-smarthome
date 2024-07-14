import React, { useContext } from 'react';
import { ApiCardContext } from 'root/ApiCardContext';
import Toast from 'react-bootstrap/Toast';
import Button from 'react-bootstrap/Button';

const SaveRulesToast = () => {
    const {
        showRulesToast,
        setShowRulesToast,
        sync_schedule_rules
    } = useContext(ApiCardContext);

    const saveRules = () => {
        sync_schedule_rules();
        setShowRulesToast(false);
    };

    return (
        <Toast
            show={showRulesToast}
            onClose={() => setShowRulesToast(false)}
            autohide
            delay={10000}
            className="fixed-bottom text-center mx-auto mb-3"
        >
            <Toast.Body>
                Should this rule change persist after reboot?
                <Button
                    variant="primary"
                    size="sm"
                    className="mx-2 mt-2"
                    onClick={saveRules}
                >
                    Yes
                </Button>
                <Button
                    variant="secondary"
                    size="sm"
                    className="mx-2 mt-2"
                    onClick={() => setShowRulesToast(false)}
                >
                    No
                </Button>
            </Toast.Body>
        </Toast>
    );
};

export default SaveRulesToast;
