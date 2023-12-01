import React, { useContext, useState } from 'react';
import { OverviewContext } from 'root/OverviewContext';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';
import Dropdown from 'react-bootstrap/Dropdown';


const NewConfigTable = () => {
    // Get django context
    const { context } = useContext(OverviewContext);

    // Set default collapse state
    const [open, setOpen] = useState(true);

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
                    <Button variant="danger" size="sm"><i className="bi-trash"></i></Button>
                </td>
            </tr>
        )
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
