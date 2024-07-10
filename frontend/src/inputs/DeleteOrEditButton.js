import React from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';

const DeleteOrEditButton = ({ status, handleDelete, handleEdit, disabled=false }) => {
    switch(status) {
        case "delete":
            return (
                <Button
                    variant="danger"
                    size="sm"
                    onClick={handleDelete}
                    disabled={disabled}
                >
                    <i className="bi-trash"></i>
                </Button>
            );
        case "edit":
            return (
                <Button
                    variant="primary"
                    size="sm"
                    onClick={handleEdit}
                    disabled={disabled}
                >
                    <i className="bi-arrow-clockwise"></i>
                </Button>
            );
        case "loading":
            return (
                <Button
                    variant="primary"
                    size="sm"
                    disabled={disabled}
                >
                    <div
                        className="spinner-border spinner-border-sm"
                        role="status"
                    ></div>
                </Button>
            );
    }
};

DeleteOrEditButton.propTypes = {
    status: PropTypes.oneOf([
        'delete',
        'edit',
        'loading'
    ]).isRequired,
    handleDelete: PropTypes.func.isRequired,
    handleEdit: PropTypes.func.isRequired,
    disabled: PropTypes.bool
};

export default DeleteOrEditButton;
