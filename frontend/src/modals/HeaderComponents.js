import React from 'react';
import PropTypes from 'prop-types';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';


const HeaderText = ({ title, size }) => {
    switch(size) {
        case("1"):
            return <h1 className="modal-title mx-auto">{title}</h1>;
        case("2"):
            return <h2 className="modal-title mx-auto">{title}</h2>;
        case("3"):
            return <h3 className="modal-title mx-auto">{title}</h3>;
        case("4"):
            return <h4 className="modal-title mx-auto">{title}</h4>;
        case("5"):
            return <h5 className="modal-title mx-auto">{title}</h5>;
    }
};

HeaderText.propTypes = {
    title: PropTypes.string,
    size: PropTypes.string
};


export const HeaderWithCloseButton = ({ title, onClose, size="5" }) => {
    return (
        <Modal.Header className="justify-content-between pb-0">
            <Button variant="link" className="btn-close" style={{visibility: "hidden"}}></Button>
            <HeaderText title={title} size={size} />
            <Button variant="link" className="btn-close" style={{right: "5%"}} onClick={onClose}></Button>
        </Modal.Header>
    );
};

HeaderWithCloseButton.propTypes = {
    title: PropTypes.string,
    onClose: PropTypes.func,
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
    title: PropTypes.string,
    size: PropTypes.string
};
