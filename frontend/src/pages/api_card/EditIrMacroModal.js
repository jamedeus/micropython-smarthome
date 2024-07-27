import React, { useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';
import { ApiCardContext } from 'root/ApiCardContext';
import 'css/remote.css';

export let openEditIrMacroModal;

// Renders table row with inputs for a single action
const ActionRow = ({ action, index, setDelay, setRepeat, deleteAction }) => {
    const [target, key, delay, repeat] = action.split(' ');

    return (
        <tr>
            <td style={{width: "auto"}}>
                {target} {key}
            </td>
            <td className="edit-ir-macro-cell">
                <Form.Control
                    className="text-center"
                    type="text"
                    value={delay}
                    onChange={(e) => setDelay(index, e.target.value)}
                />
            </td>
            <td className="edit-ir-macro-cell">
                <Form.Control
                    className="text-center"
                    type="text"
                    value={repeat}
                    onChange={(e) => setRepeat(index, e.target.value)}
                />
            </td>
            <td className="min">
                <Button
                    variant="danger"
                    size="sm"
                    className="my-auto"
                    onClick={() => deleteAction(index)}
                >
                    <i className="bi-trash"></i>
                </Button>
            </td>
        </tr>
    );
};

ActionRow.propTypes = {
    action: PropTypes.string.isRequired,
    index: PropTypes.number.isRequired,
    setDelay: PropTypes.func.isRequired,
    setRepeat: PropTypes.func.isRequired,
    deleteAction: PropTypes.func.isRequired
};

const EditIrMacroModal = () => {
    // Get existing macros state, hook to update macro actions
    const { irMacros, edit_ir_macro, delete_ir_macro } = useContext(ApiCardContext);

    // Create state for modal visibility
    const [visible, setVisible] = useState(false);

    // Create states for name of macro and actions of macro being edited
    const [macroName, setMacroName] = useState('');
    const [macroActions, setMacroActions] = useState([]);

    openEditIrMacroModal = (name) => {
        setMacroName(name);
        setMacroActions(irMacros[name]);
        setVisible(true);
    };

    // Handler for delay field, takes row number and new value
    const setDelayField = (index, value) => {
        const actions = [ ...macroActions ];
        const [target, key, _, repeat] = actions[index].split(' ');
        actions[index] = `${target} ${key} ${value} ${repeat}`;
        setMacroActions(actions);
    };

    // Handler for repeat field, takes row number and new value
    const setRepeatField = (index, value) => {
        const actions = [ ...macroActions ];
        const [target, key, delay, _] = actions[index].split(' ');
        actions[index] = `${target} ${key} ${delay} ${value}`;
        setMacroActions(actions);
    };

    // Handler for delete button, takes row number
    const deleteMacroAction = (index) => {
        setMacroActions(macroActions.filter((_, idx) => idx !== index));

        // Delete macro and close modal if last action removed
        if (macroActions.length === 1) {
            delete_ir_macro(macroName);
            setVisible(false);
        }
    };

    const submit = () => {
        edit_ir_macro(macroName, macroActions);
        setVisible(false);
    };

    return (
        <Modal show={visible} onHide={() => setVisible(false)} centered size="lg">
            <HeaderWithCloseButton
                title={`Editing ${macroName}`}
                onClose={() => setVisible(false)}
                size="5"
            />

            <Modal.Body className="d-flex flex-column align-items-center mt-3 px-3">
                <Table id="ir-macro-modal" borderless className="text-center">
                    <thead>
                        <tr>
                            <th className="text-center">Key</th>
                            <th className="text-center">Delay (ms)</th>
                            <th className="text-center">Repeat</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {macroActions.length ? (
                            macroActions.map((action, index) => {
                                return (
                                    <ActionRow
                                        key={index}
                                        action={action}
                                        index={index}
                                        setDelay={setDelayField}
                                        setRepeat={setRepeatField}
                                        deleteAction={deleteMacroAction}
                                    />
                                );
                            })
                        ) : null}
                    </tbody>
                </Table>
            </Modal.Body>
            <Modal.Footer className="mx-auto">
                <Button variant="success" onClick={submit}>
                    Edit
                </Button>
                <Button variant="secondary" onClick={() => setVisible(false)}>
                    Cancel
                </Button>
            </Modal.Footer>
        </Modal>
    );
};

export default EditIrMacroModal;
