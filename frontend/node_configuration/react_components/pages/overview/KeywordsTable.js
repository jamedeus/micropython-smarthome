import React, { useContext, useState } from 'react';
import PropTypes from 'prop-types';
import { OverviewContext } from 'root/OverviewContext';
import Row from 'react-bootstrap/Row';
import Form from 'react-bootstrap/Form';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';


const KeywordRow = ({initKeyword, initTimestamp}) => {
    // Create state objects for both inputs
    const [keyword, setKeyword] = useState(initKeyword);
    const [timestamp, setTimestamp] = useState(initTimestamp);
    // Create state to track if either input was modified
    const [modified, setModified] = useState(false);

    const updateKeyword = (newKeyword) => {
        setKeyword(newKeyword);

        // Change delete button to edit if either input modified
        if (newKeyword !== initKeyword) {
            setModified(true);
        // Change edit back to delete if returned to original value
        } else if (timestamp === initTimestamp) {
            setModified(false);
        }
    };

    const updateTimestamp = (newTimestamp) => {
        setTimestamp(newTimestamp);

        // Change delete button to edit if either input modified
        if (newTimestamp !== initTimestamp) {
            setModified(true);
        // Change edit back to delete if returned to original value
        } else if (keyword === initKeyword) {
            setModified(false);
        }
    };

    return (
        <tr id={`${keyword}_row`}>
            <td className="align-middle">
                <Form.Control
                    type="text"
                    className="keyword text-center"
                    value={keyword}
                    onChange={(e) => updateKeyword(e.target.value)}
                />
            </td>
            <td className="align-middle">
                <Form.Control
                    type="time"
                    className="keyword text-center"
                    value={timestamp}
                    onChange={(e) => updateTimestamp(e.target.value)}
                />
            </td>
            <td className="min align-middle">
                {(() => {
                    switch(modified) {
                        case true:
                            return (
                                <Button variant="primary" size="sm">
                                    <i className="bi-arrow-clockwise"></i>
                                </Button>
                            );
                        case false:
                            return (
                                <Button variant="danger" size="sm">
                                    <i className="bi-trash"></i>
                                </Button>
                            );
                    }
                })()}
            </td>
        </tr>
    );
};

KeywordRow.propTypes = {
    initKeyword: PropTypes.string,
    initTimestamp: PropTypes.string
};


const KeywordsTable = () => {
    // Get django context
    const { context } = useContext(OverviewContext);

    // Set default collapse state
    const [open, setOpen] = useState(true);

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
                            {Object.keys(context.schedule_keywords).map(keyword =>
                                <KeywordRow
                                    initKeyword={keyword}
                                    initTimestamp={context.schedule_keywords[keyword]}
                                />
                            )}
                        </tbody>
                    </Table>
                </div>
            </Collapse>
        </Row>
    );
};


export default KeywordsTable;
