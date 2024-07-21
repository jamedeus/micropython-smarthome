import React, { useState } from 'react';
import PropTypes from 'prop-types';
import Row from 'react-bootstrap/Row';
import Form from 'react-bootstrap/Form';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';
import DeleteOrEditButton from 'inputs/DeleteOrEditButton';
import { send_post_request, parse_dom_context } from 'util/django_util';
import { v4 as uuid } from 'uuid';

const KeywordRow = ({initKeyword, initTimestamp, editKeyword, deleteKeyword}) => {
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

    const handleEdit = async () => {
        const payload = {
            keyword_old: initKeyword,
            keyword_new: keyword,
            timestamp_new: timestamp
        };

        // Change delete button to loading animation, make API call
        setButton("loading");
        const response = await send_post_request(
            "/edit_schedule_keyword",
            payload
        );

        // If successful update context (re-renders this row) and reset button
        if (response.ok) {
            editKeyword(initKeyword, keyword, timestamp);
            setButton("delete");
        // Show error in alert if failed, stop loading animation
        } else {
            const error = await response.json();
            alert(error.message);
            setButton("edit");
        }
    };

    const handleDelete = async () => {
        // Change delete button to loading animation, make API call
        setButton("loading");
        const response = await send_post_request(
            "/delete_schedule_keyword",
            {keyword: keyword}
        );

        // If successful delete from context and re-render (removes this row)
        if (response.ok) {
            deleteKeyword(keyword);
        // Show error in alert if failed, stop loading animation
        } else {
            const error = await response.json();
            alert(error.message);
            setButton("delete");
        }
    };

    // Edit keyword if enter key pressed in either input
    // Ignored if fields not modified or currently loading
    const handleEnterKey = (e) => {
        if (e.key === "Enter" && button === "edit") {
            handleEdit();
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
                <DeleteOrEditButton
                    status={button}
                    handleDelete={handleDelete}
                    handleEdit={handleEdit}
                />
            </td>
        </tr>
    );
};

KeywordRow.propTypes = {
    initKeyword: PropTypes.string.isRequired,
    initTimestamp: PropTypes.string.isRequired,
    editKeyword: PropTypes.func.isRequired,
    deleteKeyword: PropTypes.func.isRequired
};

const NewKeywordRow = ({ addKeyword }) => {
    // Create state objects for both inputs
    const [keyword, setKeyword] = useState("");
    const [timestamp, setTimestamp] = useState("");

    // Create state to track button icon, enable state
    const [buttonLoading, setButtonLoading] = useState(false);
    const [buttonDisabled, setButtonDisabled] = useState(true);

    const updateKeyword = (newKeyword) => {
        setKeyword(newKeyword);

        // Enable add button if both inputs have value
        if (newKeyword !== "" && timestamp !== "") {
            setButtonDisabled(false);
        // Disable add button until both inputs have value
        } else {
            setButtonDisabled(true);
        }
    };

    const updateTimestamp = (newTimestamp) => {
        setTimestamp(newTimestamp);

        // Enable add button if both inputs have value
        if (newTimestamp !== "" && keyword !== "") {
            setButtonDisabled(false);
        // Disable add button until both inputs have value
        } else {
            setButtonDisabled(true);
        }
    };

    const handleAdd = async () => {
        setButtonLoading(true);
        const payload = {
            keyword: keyword,
            timestamp: timestamp
        };
        const response = await send_post_request("/add_schedule_keyword", payload);

        // If successful add to context (renders new row) + reset new keyword row
        if (response.ok) {
            addKeyword(keyword, timestamp);
            setKeyword("");
            setTimestamp("");
            setButtonDisabled(true);
            setButtonLoading(false);
        // Show error in alert if failed, stop loading animation
        } else {
            const error = await response.json();
            alert(error.message);
            setButtonLoading(false);
        }
    };

    // Add keyword if enter key pressed in either input
    // Ignored if fields not complete or currently loading
    const handleEnterKey = (e) => {
        if (e.key === "Enter" && !buttonLoading && !buttonDisabled) {
            handleAdd();
        }
    };

    const AddButton = () => {
        return (
            <Button
                variant="primary"
                size="sm"
                disabled={buttonDisabled}
                onClick={handleAdd}
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

NewKeywordRow.propTypes = {
    addKeyword: PropTypes.func.isRequired
};

const KeywordsTable = () => {
    // Load existing keyword context set by django template
    const [keywords, setKeywords] = useState(() => {
        return parse_dom_context("schedule_keywords");
    });

    const addKeyword = (keyword, timestamp) => {
        setKeywords([
            ...keywords,
            {id: uuid(), keyword: keyword, timestamp: timestamp}
        ]);
    };

    const editKeyword = (keyword_old, keyword_new, timestamp_new) => {
        setKeywords(keywords.map(item =>
            item.keyword === keyword_old ? { ...item, keyword: keyword_new, timestamp: timestamp_new} : item
        ));
    };

    const deleteKeyword = (keyword) => {
        setKeywords(keywords.filter(item => item.keyword !== keyword));
    };

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
                            {keywords.map(item =>
                                <KeywordRow
                                    key={item.id}
                                    initKeyword={item.keyword}
                                    initTimestamp={item.timestamp}
                                    editKeyword={editKeyword}
                                    deleteKeyword={deleteKeyword}
                                />
                            )}
                            <NewKeywordRow addKeyword={addKeyword} />
                        </tbody>
                    </Table>
                </div>
            </Collapse>
        </Row>
    );
};

export default KeywordsTable;
