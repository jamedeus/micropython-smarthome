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

const EditIrMacroModal = () => {
    // Get existing macros state, hook to update macro actions
    const { irMacros, edit_ir_macro } = useContext(ApiCardContext);

    // Create state for modal visibility, name of macro being edited
    const [visible, setVisible] = useState(false);
    const [macroName, setMacroName] = useState('');
    const [macroActions, setMacroActions] = useState([]);

    openEditIrMacroModal = (name) => {
        setMacroName(name);
        setMacroActions(irMacros[name]);
        console.log('editing:', irMacros[name]);
        setVisible(true);
    };

    const submit = () => {
        edit_ir_macro(macroName, macroActions);
        setVisible(false);
    };

    const setDelayField = (index, value) => {
        const actions = [ ...macroActions ];
        const [target, key, _, repeat] = actions[index].split(' ');
        actions[index] = `${target} ${key} ${value} ${repeat}`;
        setMacroActions(actions);
    };

    const setRepeatField = (index, value) => {
        const actions = [ ...macroActions ];
        const [target, key, delay, _] = actions[index].split(' ');
        actions[index] = `${target} ${key} ${delay} ${value}`;
        setMacroActions(actions);
    };

    const deleteMacroAction = (index) => {
        setMacroActions(macroActions.filter((_, idx) => idx !== index));
    };

    const TableRow = ({ action, index }) => {
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
                        onChange={(e) => setDelayField(index, e.target.value)}
                    />
                </td>
                <td className="edit-ir-macro-cell">
                    <Form.Control
                        className="text-center"
                        type="text"
                        value={repeat}
                        onChange={(e) => setRepeatField(index, e.target.value)}
                    />
                </td>
                <td className="min">
                    <Button
                        variant="danger"
                        size="sm"
                        className="my-auto"
                        onClick={() => deleteMacroAction(index)}
                    >
                        <i className="bi-trash"></i>
                    </Button>
                </td>
            </tr>
        );
    };

    TableRow.propTypes = {
        action: PropTypes.string.isRequired,
        index: PropTypes.number.isRequired
    };

    return (
        <Modal show={visible} onHide={() => setVisible(false)} centered size="lg">
            <HeaderWithCloseButton
                title={`Editing ${macroName}`}
                onClose={() => setVisible(false)}
                size="5"
            />

            <Modal.Body className="d-flex flex-column align-items-center mt-3 px-3">
                <Table borderless className="text-center">
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
                                    <TableRow
                                        key={index}
                                        action={action}
                                        index={index}
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
