import React from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';

const DeleteOrEditButton = ({
    status,
    handleDelete,
    handleEdit,
    disabled=false ,
    deleteIcon="bi-trash",
    editIcon="bi-arrow-clockwise"
}) => {
    switch(status) {
        case "delete":
            return (
                <Button
                    variant="danger"
                    size="sm"
                    onClick={handleDelete}
                    disabled={disabled}
                >
                    <i className={deleteIcon}></i>
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
                    <i className={editIcon}></i>
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
    disabled: PropTypes.bool,
    deleteIcon: PropTypes.string,
    editIcon: PropTypes.string
};

export default DeleteOrEditButton;
