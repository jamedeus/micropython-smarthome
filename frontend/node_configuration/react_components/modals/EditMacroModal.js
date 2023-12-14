import React, { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Modal from 'react-bootstrap/Modal';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';
import { sleep, toTitle } from 'util/helper_functions';
import { ApiOverviewContext } from 'root/ApiOverviewContext';


export const EditMacroModalContext = createContext();


export const EditMacroModalContextProvider = ({ children }) => {
    const [editMacroContent, setEditMacroContent] = useState({
        visible: false,
        name: '',
        actions: []
    });

    const openEditMacroModal = (name, actions) => {
        setEditMacroContent({
            ...editMacroContent,
            ["visible"]: true,
            ["name"]: name,
            ["actions"]: actions
        });
    };

    const handleClose = () => {
        setEditMacroContent({
            ...editMacroContent,
            ["visible"]: false
        });
    };

    return (
        <EditMacroModalContext.Provider value={{
            editMacroContent,
            setEditMacroContent,
            openEditMacroModal,
            handleClose
        }}>
            {children}
        </EditMacroModalContext.Provider>
    );
};

EditMacroModalContextProvider.propTypes = {
    children: PropTypes.node,
};


export const EditMacroModal = () => {
    // Get state object that determines modal contents
    const { editMacroContent, handleClose } = useContext(EditMacroModalContext);

    // Get callbacks to remove macro action, resume recording actions
    const { deleteMacroAction, startRecording } = useContext(ApiOverviewContext);

    // Handler for record more button: set record name, close modal, change URL
    const resumeRecording = () => {
        startRecording(editMacroContent.name);
        handleClose();
        history.pushState({}, '', `/api/recording/${editMacroContent.name}`);
    };

    const TableRow = ({action, actionID}) => {
        // Create callback for delete button
        const del = async () => {
            // Delete macro action
            const result = await fetch(`/delete_macro_action/${editMacroContent.name}/${actionID}`);
            const status = await result.status;

            // Fade row out if successful
            // TODO handle failure
            if (status === 200) {
                // Fade out row
                const row = document.getElementById(`macro-action-${actionID}`);
                row.classList.add('fade-out');
                await sleep(200);

                // Remove from context (re-renders without this row)
                deleteMacroAction(editMacroContent.name, actionID);

                // Close modal if last action deleted (context deletes whole macro)
                if (editMacroContent.actions.every(item => item === null)) {
                    handleClose();
                }
            }
        };

        return (
            <tr id={`macro-action-${actionID}`}>
                <td style={{width: "auto"}}>{action.node_name}</td>
                <td style={{width: "auto"}}>{action.target_name}</td>
                <td style={{width: "auto"}}>{action.action_name}</td>
                <td style={{width: "auto"}}>
                    <Button
                        variant="danger"
                        size="sm"
                        className="my-auto"
                        onClick={del}
                    >
                        <i className="bi-trash"></i>
                    </Button>
                </td>
            </tr>
        );
    };

    TableRow.propTypes = {
        action: PropTypes.object,
        actionID: PropTypes.number
    };

    return (
        <Modal show={editMacroContent.visible} onHide={handleClose} centered>
            <HeaderWithCloseButton
                title={`Edit ${toTitle(editMacroContent.name)} Macro`}
                onClose={handleClose}
                size="3"
            />

            <Modal.Body className="d-flex flex-column align-items-center">
                <h5 className="text-center mt-3">Actions</h5>
                <Table borderless className="text-center section mb-0">
                    <thead>
                        <tr>
                            <th className="text-center">Node</th>
                            <th className="text-center">Target</th>
                            <th className="text-center">Action</th>
                            <th className="text-center">Delete</th>
                        </tr>
                    </thead>
                    <tbody>
                        {editMacroContent.actions.map((action, index) => {
                            return <TableRow key={index} action={action} actionID={index} />;
                        })}
                    </tbody>
                </Table>
            </Modal.Body>
            <Modal.Footer className="mx-auto pt-2">
                <Button variant="success" className="mx-auto mb-3" onClick={resumeRecording}>
                    Record More
                </Button>
            </Modal.Footer>
        </Modal>
    );
};
