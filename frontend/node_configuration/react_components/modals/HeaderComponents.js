import React from 'react';
import PropTypes from 'prop-types';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';


export const HeaderWithCloseButton = ({ title, onClose }) => {
    return (
        <Modal.Header className="justify-content-between pb-0">
            <Button variant="link" className="btn-close" style={{visibility: "hidden"}}></Button>
            <h5 className="modal-title">{title}</h5>
            <Button variant="link" className="btn-close" style={{right: "5%"}} onClick={onClose}></Button>
        </Modal.Header>
    );
};

HeaderWithCloseButton.propTypes = {
    title: PropTypes.string,
    onClose: PropTypes.func
};


export const HeaderStaticBackdrop = ({ title }) => {
    return (
        <Modal.Header className="justify-content-between">
            <h3 className="modal-title mx-auto">{title}</h3>
        </Modal.Header>
    );
};

HeaderStaticBackdrop.propTypes = {
    title: PropTypes.string
};
