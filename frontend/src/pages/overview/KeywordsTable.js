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
    // Get callbacks used to modify keywords
    const { editScheduleKeyword, deleteScheduleKeyword } = useContext(OverviewContext);

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
        const result = await send_post_request(
            "edit_schedule_keyword",
            payload
        );

        // If successful update context (re-renders this row) and reset button
        if (result.ok) {
            editScheduleKeyword(initKeyword, keyword, timestamp);
            setButton("delete");
        // Show error in alert if failed, stop loading animation
        } else {
            alert(await result.text());
            setButton("edit");
        }
    };

    const deleteKeyword = async () => {
        // Change delete button to loading animation, make API call
        setButton("loading");
        const result = await send_post_request(
            "delete_schedule_keyword",
            {"keyword": keyword}
        );

        // If successful delete from context and re-render (removes this row)
        if (result.ok) {
            deleteScheduleKeyword(keyword);
        // Show error in alert if failed, stop loading animation
        } else {
            alert(await result.text());
            setButton("delete");
        }
    };

    // Edit keyword if enter key pressed in either input
    // Ignored if fields not modified or currently loading
    const handleEnterKey = (e) => {
        if (e.key === "Enter" && button === "edit") {
            editKeyword();
        }
    };

    // Returns save/delete button or loading animation based on button state
    const SaveButton = () => {
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
                    onKeyDown={handleEnterKey}
                />
            </td>
            <td className="align-middle">
                <Form.Control
                    type="time"
                    className="keyword text-center"
                    value={timestamp}
                    onChange={(e) => updateTimestamp(e.target.value)}
                    onKeyDown={handleEnterKey}
                />
            </td>
            <td className="min align-middle">
                <SaveButton />
            </td>
        </tr>
    );
};

KeywordRow.propTypes = {
    initKeyword: PropTypes.string,
    initTimestamp: PropTypes.string
};


const NewKeywordRow = () => {
    // Get context and callback (used to add new row)
    const { addScheduleKeyword } = useContext(OverviewContext);

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
        };
        const result = await send_post_request("add_schedule_keyword", payload);

        // If successful add to context (renders new row) + reset new keyword row
        if (result.ok) {
            addScheduleKeyword(keyword, timestamp);
            setKeyword("");
            setTimestamp("");
            setButtonDisabled(true);
            setButtonLoading(false);
        // Show error in alert if failed, stop loading animation
        } else {
            alert(await result.text());
            setButtonLoading(false);
        }
    };

    // Add keyword if enter key pressed in either input
    // Ignored if fields not complete or currently loading
    const handleEnterKey = (e) => {
        if (e.key === "Enter" && !buttonLoading && !buttonDisabled) {
            addKeyword();
        }
    };

    const AddButton = () => {
        return (
            <Button
                variant="primary"
                size="sm"
                disabled={buttonDisabled}
                onClick={addKeyword}
            >
                <i className="bi-plus"></i>
            </Button>
        );
    };

    const LoadingButton = () => {
        return (
            <Button variant="primary" size="sm">
                <div className="spinner-border spinner-border-sm" role="status"></div>
            </Button>
        );
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
                    onKeyDown={handleEnterKey}
                />
            </td>
            <td className="align-middle">
                <Form.Control
                    type="time"
                    className="keyword text-center"
                    value={timestamp}
                    onChange={(e) => updateTimestamp(e.target.value)}
                    onKeyDown={handleEnterKey}
                />
            </td>
            <td className="min align-middle">
                {buttonLoading ? <LoadingButton /> : <AddButton />}
            </td>
        </tr>
    );
};


const KeywordsTable = () => {
    // Get django context
    const { context } = useContext(OverviewContext);

    // Set default collapse state
    const [open, setOpen] = useState(true);

    // Render table with row for each existing keyword + empty row to add new keywords
    return (
        <Row id="keywords" className="text-center section px-0 pt-2">
            <h3 className="text-center my-1" onClick={() => setOpen(!open)}>
                Schedule Keywords
            </h3>
            <Collapse in={open}>
                <div>
                    <Table className="table-borderless table-sm table-hover mt-3 mx-auto">
                        <thead>
                            <tr>
                                <th className="w-50">Keyword</th>
                                <th className="w-50">Timestamp</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {context.schedule_keywords.map(item =>
                                <KeywordRow
                                    key={item.id}
                                    initKeyword={item.keyword}
                                    initTimestamp={item.timestamp}
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
