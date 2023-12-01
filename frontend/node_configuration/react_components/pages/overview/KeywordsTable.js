import React, { useContext, useState } from 'react';
import { OverviewContext } from 'root/OverviewContext';
import Row from 'react-bootstrap/Row';
import Form from 'react-bootstrap/Form';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';


const KeywordsTable = () => {
    // Get django context
    const { context } = useContext(OverviewContext);

    // Set default collapse state
    const [open, setOpen] = useState(true);

    function get_table_row(keyword) {
        return (
            <tr id={`${keyword}_row`}>
                <td className="align-middle">
                    <Form.Control
                        type="text"
                        className="keyword text-center"
                        value={keyword}
                    />
                </td>
                <td className="align-middle">
                    <Form.Control
                        type="time"
                        className="keyword text-center"
                        value={context.schedule_keywords[keyword]}
                    />
                </td>
                <td className="min align-middle">
                    <Button variant="danger" size="sm">
                        <i className="bi-trash"></i>
                    </Button>
                </td>
            </tr>
        );
    }

    // Render full layout with metadata, wifi, IR Blaster, and instance cards
    return (
        <Row id="keywords" className="section px-0 pt-2">
            <h3 className="text-center my-1" onClick={() => setOpen(!open)}>Schedule Keywords</h3>
            <Collapse in={open}>
                <div>
                    <Table id="nodes_table" className="table-borderless table-sm table-hover mt-3 mx-auto">
                        <thead>
                            <tr>
                                <th className="w-50"><span>Keyword</span></th>
                                <th className="w-50"><span>Timestamp</span></th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {Object.keys(context.schedule_keywords).map(keyword => get_table_row(keyword))}
                        </tbody>
                    </Table>
                </div>
            </Collapse>
        </Row>
    );
};


export default KeywordsTable;
