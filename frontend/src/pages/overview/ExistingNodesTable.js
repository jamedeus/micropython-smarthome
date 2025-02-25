import React, { useContext, useState } from 'react';
import PropTypes from 'prop-types';
import { OverviewContext } from 'root/OverviewContext';
import Row from 'react-bootstrap/Row';
import Table from 'react-bootstrap/Table';
import Collapse from 'react-bootstrap/Collapse';
import Dropdown from 'react-bootstrap/Dropdown';
import { send_post_request } from 'util/django_util';
import { showErrorModal, hideErrorModal } from 'modals/ErrorModal';
import { showChangeIpModal } from './ChangeIpModal';
import { uploadConfigWithToast } from './ReuploadToast';

const ExistingNodeRow = ({ friendly_name, filename, ip, onDelete }) => {
    // Handler for Re-upload menu option
    const reupload = () => {
        uploadConfigWithToast(filename, ip);
    };

    // Handler for Edit menu option
    const edit = () => {
        window.location.href = `/edit_config/${friendly_name}`;
    };

    // Handler for Change IP menu option
    const changeIp = () => {
        showChangeIpModal(friendly_name, ip);
    };

    // Handler for Delete menu option
    const handleDelete = () => {
        onDelete(friendly_name);
    };

    return (
        <tr id={friendly_name}>
            <td className="align-middle">
                <span className="form-control keyword text-center">
                    {friendly_name}
                </span>
            </td>
            <td className="align-middle">
                <span className="form-control keyword text-center">
                    {ip}
                </span>
            </td>
            <td className="min align-middle">
                <Dropdown align="end" className="my-auto">
                    <Dropdown.Toggle variant="primary" size="sm">
                        <i className="bi-list"></i>
                    </Dropdown.Toggle>
                    <Dropdown.Menu>
                        <Dropdown.Item onClick={edit}>
                            Edit
                        </Dropdown.Item>
                        <Dropdown.Item onClick={reupload}>
                            Re-upload
                        </Dropdown.Item>
                        <Dropdown.Item onClick={changeIp}>
                            Change IP
                        </Dropdown.Item>
                        <Dropdown.Item onClick={handleDelete}>
                            Delete
                        </Dropdown.Item>
                    </Dropdown.Menu>
                </Dropdown>
            </td>
        </tr>
    );
};

ExistingNodeRow.propTypes = {
    friendly_name: PropTypes.string.isRequired,
    filename: PropTypes.string.isRequired,
    ip: PropTypes.string.isRequired,
    onDelete: PropTypes.func.isRequired
};

const ExistingNodesTable = () => {
    // Set default collapse state
    const [open, setOpen] = useState(true);

    // Get django context (contains existing nodes) and callback to delete node
    const { context, deleteExistingNode } = useContext(OverviewContext);

    // Takes node friendly name, opens modal to confirm deletion
    const show_delete_modal = (friendly_name) => {
        showErrorModal({
            title: "Confirm Delete",
            error: "confirm_delete",
            handleConfirm: () => delete_node(friendly_name)
        });
    };

    // Handler for confirm delete button in modal
    const delete_node = async (friendly_name) => {
        const response = await send_post_request(
            "/delete_node",
            {friendly_name: friendly_name}
        );

        // If successful close modal and update context (rerender without this row)
        if (response.ok) {
            deleteExistingNode(friendly_name);
            hideErrorModal();

        // Show error if failed
        } else {
            const error = await response.json();
            showErrorModal({
                title: "Error",
                error: "failed",
                body: error.message
            });
        }
    };

    // Render table with row for each existing node
    return (
        <Row id="existing" className="text-center section px-0 pt-2">
            <h3 className="text-center my-1" onClick={() => setOpen(!open)}>
                Existing Nodes
            </h3>
            <Collapse in={open}>
                <div>
                    <Table className="table-borderless table-sm table-hover mt-3 mx-auto">
                        <thead>
                            <tr>
                                <th className="w-50">Name</th>
                                <th className="w-50">IP</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {context.uploaded.map(node =>
                                <ExistingNodeRow
                                    key={node.friendly_name}
                                    friendly_name={node.friendly_name}
                                    filename={node.filename}
                                    ip={node.ip}
                                    onDelete={show_delete_modal}
                                />
                            )}
                        </tbody>
                    </Table>
                </div>
            </Collapse>
        </Row>
    );
};

export default ExistingNodesTable;
