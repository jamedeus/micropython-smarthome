import React from 'react';
import PropTypes from 'prop-types';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';

const HeaderText = ({ title, size }) => {
    switch(size) {
        case("3"):
            return <h3 className="modal-title mx-auto">{title}</h3>;
        case("5"):
            return <h5 className="modal-title mx-auto">{title}</h5>;
    }
};

HeaderText.propTypes = {
    title: PropTypes.string.isRequired,
    size: PropTypes.oneOf([
        "3",
        "5"
    ]).isRequired
};

export const HeaderWithCloseButton = ({ title, onClose, size="5" }) => {
    return (
        <Modal.Header className="justify-content-between pb-0">
            <Button
                variant="link"
                className={`btn-close ${size === "3" ? "ms-1 me-0" : ""}`}
                style={{visibility: "hidden"}}
            ></Button>

            <HeaderText title={title} size={size} />

            <Button
                variant="link"
                className={`btn-close ${size === "3" ? "ms-0 me-1" : ""}`}
                onClick={onClose}
            ></Button>
        </Modal.Header>
    );
};

HeaderWithCloseButton.propTypes = {
    title: PropTypes.string.isRequired,
    onClose: PropTypes.func.isRequired,
    size: PropTypes.string
};

export const HeaderStaticBackdrop = ({ title, size="3" }) => {
    return (
        <Modal.Header className="justify-content-between">
            <HeaderText title={title} size={size} />
        </Modal.Header>
    );
};

HeaderStaticBackdrop.propTypes = {
    title: PropTypes.string.isRequired,
    size: PropTypes.string
};
