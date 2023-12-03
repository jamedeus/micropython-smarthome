import React, { useContext, useState } from 'react';
import { OverviewContext } from 'root/OverviewContext';
import Row from 'react-bootstrap/Row';
import Form from 'react-bootstrap/Form';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';
import { send_post_request } from 'util/django_util';
import { ErrorModalContext } from 'modals/ErrorModal';


const NewConfigTable = () => {
    // Get django context
    const { context } = useContext(OverviewContext);

    // Get callbacks for error modal
    const { errorModalContent, setErrorModalContent } = useContext(ErrorModalContext);

    // Set default collapse state
    const [open, setOpen] = useState(true);

    // Takes config filename, opens modal to confirm deletion
    function show_delete_modal(filename) {
        setErrorModalContent({
            ...errorModalContent,
            ["visible"]: true,
            ["title"]: "Confirm Delete",
            ["error"]: "confirm_delete",
            ["handleConfirm"]: () => delete_config(filename)
        });
    }

    // Handler for confirm delete button in modal
    async function delete_config(filename) {
        let result = await send_post_request("delete_config", filename);

        // Refresh page if successfully deleted
        if (result.ok) {
            location.reload();

            // Show error if failed
        } else {
            const error = await result.text();

            setErrorModalContent({
                ...errorModalContent,
                ["visible"]: true,
                ["title"]: "Error",
                ["error"]: "failed",
                ["body"]: error
            });
        }
    }

    function get_table_row(config) {
        return (
            <tr id={config}>
                <td className="align-middle">
                    <span className="form-control text-center">{config}</span>
                </td>
                <td className="align-middle">
                    <Form.Control
                        type="text"
                        id={`${config}-ip`}
                        className="text-center ip-input"
                        placeholder="xxx.xxx.x.xxx"
                        pattern="^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
                    />
                </td>
                <td className="min align-middle">
                    <Button variant="primary" size="sm">Upload</Button>
                </td>
                <td className="min align-middle">
                    <Button variant="danger" size="sm" onClick={() => show_delete_modal(config)}>
                        <i className="bi-trash"></i>
                    </Button>
                </td>
            </tr>
        );
    }

    // Render full layout with metadata, wifi, IR Blaster, and instance cards
    return (
        <Row id="not_uploaded" className="section pt-2 px-0 mb-5">
            <h3 className="text-center my-1" onClick={() => setOpen(!open)}>Configs Ready to Upload</h3>
            <Collapse in={open}>
                <div>
                    <Table borderless hover size="sm" className="mt-3 mx-auto">
                        <thead>
                            <tr>
                                <th className="w-50"><span>Name</span></th>
                                <th className="w-50"><span>IP</span></th>
                                <th></th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {context.not_uploaded.map(config => get_table_row(config))}
                        </tbody>
                    </Table>
                </div>
            </Collapse>
        </Row>
    );
};


export default NewConfigTable;
