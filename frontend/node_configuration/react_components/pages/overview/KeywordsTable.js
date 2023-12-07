import React, { useContext, useState } from 'react';
import PropTypes from 'prop-types';
import { OverviewContext } from 'root/OverviewContext';
import Row from 'react-bootstrap/Row';
import Form from 'react-bootstrap/Form';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';
import { send_post_request } from 'util/django_util';


const KeywordRow = ({initKeyword, initTimestamp}) => {
    // Create state objects for both inputs
    const [keyword, setKeyword] = useState(initKeyword);
    const [timestamp, setTimestamp] = useState(initTimestamp);

    // Create state to track button icon
    const [button, setButton] = useState("delete");

    const updateKeyword = (newKeyword) => {
        setKeyword(newKeyword);

        // Change delete button to edit if either input modified
        if (newKeyword !== initKeyword) {
            setButton("edit");
        // Change edit back to delete if returned to original value
        } else if (timestamp === initTimestamp) {
            setButton("delete");
        }
    };

    const updateTimestamp = (newTimestamp) => {
        setTimestamp(newTimestamp);

        // Change delete button to edit if either input modified
        if (newTimestamp !== initTimestamp) {
            setButton("edit");
        // Change edit back to delete if returned to original value
        } else if (keyword === initKeyword) {
            setButton("delete");
        }
    };

    const editKeyword = async () => {
        const payload = {
            "keyword_old": initKeyword,
            "keyword_new": keyword,
            "timestamp_new": timestamp
        };

        // Change delete button to loading animation, make API call
        setButton("loading");
        const result = await send_post_request("edit_schedule_keyword", payload);

        // Reload if successfully deleted
        if (result.ok) {
            location.reload();
        // Show error in alert, stop loading animation
        } else {
            alert(await result.text());
            setButton("edit");
        }
    };

    const deleteKeyword = async () => {
        // Change delete button to loading animation, make API call
        setButton("loading");
        const result = await send_post_request("delete_schedule_keyword", {"keyword": keyword});

        // Reload if successfully deleted
        if (result.ok) {
            location.reload();
            // Show error in alert, stop loading animation
        } else {
            alert(await result.text());
            setButton("delete");
        }
    };

    return (
        <tr id={`${keyword}_row`}>
            <td className="align-middle">
                <Form.Control
                    type="text"
                    className="keyword text-center"
                    placeholder="Keyword"
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
                switch(button) {
                    case "delete":
                        return (
                            <Button variant="danger" size="sm" onClick={deleteKeyword}>
                                <i className="bi-trash"></i>
                            </Button>
                        );
                    case "edit":
                        return (
                            <Button variant="primary" size="sm" onClick={editKeyword}>
                                <i className="bi-arrow-clockwise"></i>
                            </Button>
                        );
                    case "loading":
                        return (
                            <Button variant="primary" size="sm" onClick={deleteKeyword}>
                                <div className="spinner-border spinner-border-sm" role="status"></div>
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


const NewKeywordRow = () => {
    // Create state objects for both inputs
    const [keyword, setKeyword] = useState("");
    const [timestamp, setTimestamp] = useState("");

    // Create state to track button icon, enable state
    const [buttonLoading, setButtonLoading] = useState(false);
    const [buttonDisabled, setButtonDisabled] = useState(true);

    const updateKeyword = (newKeyword) => {
        setKeyword(newKeyword);

        // Change delete button to edit if either input modified
        if (newKeyword !== "" && timestamp !== "") {
            setButtonDisabled(false);
        // Change edit back to delete if returned to original value
        } else {
            setButtonDisabled(true);
        }
    };

    const updateTimestamp = (newTimestamp) => {
        setTimestamp(newTimestamp);

        // Change delete button to edit if either input modified
        if (newTimestamp !== "" && keyword !== "") {
            setButtonDisabled(false);
            // Change edit back to delete if returned to original value
        } else {
            setButtonDisabled(true);
        }
    };

    const addKeyword = async () => {
        setButtonLoading(true);
        const payload = {
            "keyword": keyword,
            "timestamp": timestamp
        }
        const result = await send_post_request("add_schedule_keyword", payload);

        // Reload if successfully added
        if (result.ok) {
            location.reload();
        // Show error in alert, stop loading animation
        } else {
            alert(await result.text());
            setButtonLoading(false);
        }
    };

    return (
        <tr id={`${keyword}_row`}>
            <td className="align-middle">
                <Form.Control
                    type="text"
                    className="keyword text-center"
                    placeholder="Keyword"
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
                    switch(buttonLoading) {
                        case false:
                            return (
                                <Button variant="primary" size="sm" disabled={buttonDisabled} onClick={addKeyword}>
                                    <i className="bi-plus"></i>
                                </Button>
                            );
                        case true:
                            return (
                                <Button variant="primary" size="sm">
                                    <div className="spinner-border spinner-border-sm" role="status"></div>
                                </Button>
                            );
                    }
                })()}
            </td>
        </tr>
    );
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
                            <NewKeywordRow />
                        </tbody>
                    </Table>
                </div>
            </Collapse>
        </Row>
    );
};


export default KeywordsTable;
