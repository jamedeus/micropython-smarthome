import React from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';

const DeleteOrEditButton = ({ status, handleDelete, handleEdit }) => {
    switch(status) {
        case "delete":
            return (
                <Button variant="danger" size="sm" onClick={handleDelete}>
                    <i className="bi-trash"></i>
                </Button>
            );
        case "edit":
            return (
                <Button variant="primary" size="sm" onClick={handleEdit}>
                    <i className="bi-arrow-clockwise"></i>
                </Button>
            );
        case "loading":
            return (
                <Button variant="primary" size="sm">
                    <div className="spinner-border spinner-border-sm" role="status"></div>
                </Button>
            );
    }
};

DeleteOrEditButton.propTypes = {
    status: PropTypes.oneOf([
        'delete',
        'edit',
        'loading'
    ]),
    handleDelete: PropTypes.func,
    handleEdit: PropTypes.func
};

export default DeleteOrEditButton;
