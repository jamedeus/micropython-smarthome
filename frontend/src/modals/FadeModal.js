import React, { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import { ApiCardContext } from 'root/ApiCardContext';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';


export const FadeContext = createContext();

export const FadeContextProvider = ({ children }) => {
    const [fadeModalContent, setFadeContent] = useState({
        visible: false,
        target: '',
        brightness: '',
        duration: ''
    });

    // Get function to send API call to node
    const {send_command} = useContext(ApiCardContext);

    const handleClose = () => {
        setFadeContent({ ...fadeModalContent, ["visible"]: false });
    };

    const showFadeModal = (id) => {
        setFadeContent({
            ...fadeModalContent,
            ["visible"]: true,
            ["target"]: id
        });
    };

    const setBrightness = (value) => {
        setFadeContent({
            ...fadeModalContent,
            ["brightness"]: formatField(value, fadeModalContent.brightness)
        });
    };

    const setDuration = (value) => {
        setFadeContent({
            ...fadeModalContent,
            ["duration"]: formatField(value, fadeModalContent.duration)
        });
    };

    // Format fields as user types, remove non-numeric characters
    const formatField = (newDuration, oldDuration) => {
        // Backspace and delete bypass formatting
        if (newDuration.length < oldDuration.length) {
            return newDuration;
        }

        // Remove non-numeric characters
        return newDuration.replace(/[^\d.]/g, '');
    };

    // Close modal, send command to start fade
    const submit = async () => {
        handleClose();
        const result = await send_command({
            command: 'set_rule',
            instance: fadeModalContent.target,
            rule: `fade/${fadeModalContent.brightness}/${fadeModalContent.duration}`
        });
        const response = await result.json();
        console.log(response);
    };

    // Return true if both fields have value, false if either empty
    const readyToSubmit = () => {
        return fadeModalContent.duration !== '' && fadeModalContent.brightness !== '';
    }

    // Change IP if enter key pressed in either field
    const handleEnterKey = (e) => {
        if (e.key === "Enter" && readyToSubmit()) {
            submit();
        }
    };

    return (
        <FadeContext.Provider value={{
            fadeModalContent,
            setFadeContent,
            handleClose,
            showFadeModal,
            setBrightness,
            setDuration,
            submit,
            readyToSubmit,
            handleEnterKey
        }}>
            {children}
        </FadeContext.Provider>
    );
};

FadeContextProvider.propTypes = {
    children: PropTypes.node,
};


export const FadeModal = () => {
    // Get function used to make API call
    const {
        fadeModalContent,
        handleClose,
        setBrightness,
        setDuration,
        submit,
        readyToSubmit,
        handleEnterKey
    } = useContext(FadeContext);

    return (
        <Modal show={fadeModalContent.visible} onHide={handleClose} centered>
            <HeaderWithCloseButton
                title="Start Fade"
                onClose={handleClose}
                size="5"
            />

            <Modal.Body className="d-flex">
                <Col className="text-center mx-1">
                    <Form.Label>Target Brightness</Form.Label>
                    <Form.Control
                        type="text"
                        value={fadeModalContent.brightness}
                        onChange={(e) => setBrightness(e.target.value)}
                        onKeyDown={handleEnterKey}
                    />
                </Col>
                <Col className="text-center mx-1">
                    <Form.Label>Duration (seconds)</Form.Label>
                    <Form.Control
                        type="text"
                        value={fadeModalContent.duration}
                        onChange={(e) => setDuration(e.target.value)}
                        onKeyDown={handleEnterKey}
                    />
                </Col>
            </Modal.Body>
            <Modal.Footer className="mx-auto pt-0">
                <Button
                    variant="success"
                    disabled={!readyToSubmit()}
                    onClick={submit}
                >
                    Start
                </Button>
            </Modal.Footer>
        </Modal>
    );
};
