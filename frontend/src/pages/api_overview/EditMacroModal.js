import React, { useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Modal from 'react-bootstrap/Modal';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';
import { toTitle } from 'util/helper_functions';
import { ApiOverviewContext } from 'root/ApiOverviewContext';
import { TransitionGroup, CSSTransition } from "react-transition-group";
import 'css/macros.css';

export let openEditMacroModal;

const EditMacroModal = () => {
    // Create state for modal visibility, name of macro being edited
    const [visible, setVisible] = useState(false);
    const [macroName, setMacroName] = useState('');

    // Get context (contains macro actions), hooks to delete and record actions
    const { context, deleteMacroAction, startRecording } = useContext(ApiOverviewContext);

    openEditMacroModal = (name) => {
        setMacroName(name);
        setVisible(true);
    };

    // Handler for record more button: set record name, close modal, change URL
    const resumeRecording = () => {
        startRecording(macroName);
        setVisible(false);
        history.pushState({}, '', `/api/recording/${macroName}`);
    };

    const TableRow = ({action, actionID}) => {
        // Create callback for delete button
        const del = async () => {
            // Delete macro action
            const result = await fetch(`/delete_macro_action/${macroName}/${actionID}`);

            // Fade row out if successful
            // TODO handle failure
            if (result.status === 200) {
                // Remove from context (row fades out before unmounting)
                deleteMacroAction(macroName, actionID);

                // Close modal if last action deleted (context deletes whole macro)
                if (context.macros[macroName].length === 1) {
                    setVisible(false);
                }
            }
        };

        return (
            <tr>
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
        action: PropTypes.object.isRequired,
        actionID: PropTypes.number.isRequired
    };

    return (
        <Modal show={visible} onHide={() => setVisible(false)} centered>
            <HeaderWithCloseButton
                title={`Edit ${toTitle(macroName)} Macro`}
                onClose={() => setVisible(false)}
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
                    <TransitionGroup component="tbody">
                        {context["macros"][macroName] ? (
                            context["macros"][macroName].map((action, index) => {
                                return (
                                    <CSSTransition
                                        key={JSON.stringify(action)}
                                        timeout={200}
                                        classNames='fade'
                                    >
                                        <TableRow action={action} actionID={index} />
                                    </CSSTransition>
                                );
                            })
                        ) : null}
                    </TransitionGroup>
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

export default EditMacroModal;
