import React, { useContext, useState } from 'react';
import { OverviewContext } from 'root/OverviewContext';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';
import Dropdown from 'react-bootstrap/Dropdown';


const ExistingNodesTable = () => {
    // Get django context
    const { context } = useContext(OverviewContext);

    // Set default collapse state
    const [open, setOpen] = useState(true);

    function edit_config(friendly_name) {
        window.location.href = `/edit_config/${friendly_name}`;
    }

    function get_table_row(node) {
        return (
            <tr id={node.friendly_name}>
                <td className="align-middle">
                    <span className="form-control keyword text-center">{node.friendly_name}</span>
                </td>
                <td className="align-middle">
                    <span className="form-control keyword text-center">{node.ip}</span>
                </td>
                <td className="min align-middle">
                    <Dropdown className="my-auto">
                        <Dropdown.Toggle variant="primary" size="sm">
                            <i className="bi-list"></i>
                        </Dropdown.Toggle>
                        <Dropdown.Menu>
                            <Dropdown.Item onClick={() => edit_config(node.friendly_name)}>Edit</Dropdown.Item>
                            <Dropdown.Item>Re-upload</Dropdown.Item>
                            <Dropdown.Item>Chnge IP</Dropdown.Item>
                            <Dropdown.Item>Delete</Dropdown.Item>
                        </Dropdown.Menu>
                    </Dropdown>
                </td>
            </tr>
        )
    }

    // Render full layout with metadata, wifi, IR Blaster, and instance cards
    return (
        <Row id="existing" className="section px-0 pt-2">
            <h3 className="text-center my-1" onClick={() => setOpen(!open)}>Existing Nodes</h3>
            <Collapse in={open}>
                <div>
                    <Table id="nodes_table" className="table-borderless table-sm table-hover mt-3 mx-auto">
                        <thead>
                            <tr>
                                <th className="w-50"><span>Name</span></th>
                                <th className="w-50"><span>IP</span></th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {context.uploaded.map(node => get_table_row(node))}
                        </tbody>
                    </Table>
                </div>
            </Collapse>
        </Row>
    );
};


export default ExistingNodesTable;
