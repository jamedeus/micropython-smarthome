import React, { useState, useContext } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import FloatingLabel from 'react-bootstrap/FloatingLabel';
import Button from 'react-bootstrap/Button';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import Dropdown from 'react-bootstrap/Dropdown';
import DropdownButton from 'react-bootstrap/DropdownButton';
import Collapse from 'react-bootstrap/Collapse';
import { ApiCardContext } from 'root/ApiCardContext';
import EditIrMacroModal, { openEditIrMacroModal } from './EditIrMacroModal';
import 'css/remote.css';

const IrButton = ({title, icon, variant='primary', recording=false, onClick}) => {
    return (
        <Button
            variant={variant}
            size="lg"
            className={`m-3 ir-btn ${recording ? 'blue-glow' : null}`}
            onClick={onClick}
            title={title}
        >
            <i className={icon}></i>
        </Button>
    );
};

const SpacerButton = () => {
    return (
        <Button
            size="lg"
            className="m-3 ir-btn"
            style={{
                visibility: 'hidden'
            }}
        >
            <i className="bi-question"></i>
        </Button>
    );
};

IrButton.propTypes = {
    title: PropTypes.string.isRequired,
    icon: PropTypes.string.isRequired,
    variant: PropTypes.oneOf([
        'primary',
        'secondary'
    ]),
    recording: PropTypes.bool,
    onClick: PropTypes.func.isRequired
};

const AcRemote = ({ recording=false, addMacroAction }) => {
    const { send_command } = useContext(ApiCardContext);

    const HandleKey = (key) => {
        if (recording) {
            addMacroAction(`ac ${key} 100 1`);
        } else {
            send_command({command: 'ir', ir_target: 'ac', key: key});
        }
    };

    return (
        <div className="d-flex flex-column remote mx-auto mb-4">
            <div className="row text-center">
                <h4 className="my-2">AC Remote</h4>
            </div>
            <div className="d-flex flex-row my-2 mx-auto">
                <IrButton
                    title="Stop cooling"
                    icon="bi-wind"
                    recording={recording}
                    onClick={() => HandleKey('stop')}
                />
                <IrButton
                    title="Turn off fan"
                    icon="bi-x-octagon-fill"
                    recording={recording}
                    onClick={() => HandleKey('off')}
                />
                <IrButton
                    title="Start cooling"
                    icon="bi-snow"
                    recording={recording}
                    onClick={() => HandleKey('start')}
                />
            </div>
        </div>
    );
};

AcRemote.propTypes = {
    recording: PropTypes.bool,
    addMacroAction: PropTypes.func.isRequired
};

const TvRemote = ({ recording=false, addMacroAction }) => {
    const { send_command } = useContext(ApiCardContext);

    const HandleKey = (key) => {
        if (recording) {
            addMacroAction(`tv ${key} 100 1`);
        } else {
            send_command({command: 'ir', ir_target: 'tv', key: key});
        }
    };

    return (
        <div className="d-flex flex-column remote mx-auto mb-4">
            <div className="row text-center">
                <h4 className="my-2">TV Remote</h4>
            </div>
            <div className="d-flex flex-row pb-3 mx-auto">
                <IrButton
                    title="Power"
                    icon="bi-power"
                    recording={recording}
                    onClick={() => HandleKey('power')}
                />
                <SpacerButton />
                <IrButton
                    title="Source"
                    icon="bi-upload"
                    recording={recording}
                    onClick={() => HandleKey('source')}
                />
            </div>
            <div className="d-flex flex-row mx-auto">
                <SpacerButton />
                <IrButton
                    title="Up"
                    icon="bi-arrow-up"
                    recording={recording}
                    onClick={() => HandleKey('up')}
                />
                <SpacerButton />
            </div>
            <div className="d-flex flex-row mx-auto">
                <IrButton
                    title="Left"
                    icon="bi-arrow-left"
                    recording={recording}
                    onClick={() => HandleKey('left')}
                />
                <IrButton
                    title="Enter"
                    icon="bi-app"
                    recording={recording}
                    onClick={() => HandleKey('enter')}
                />
                <IrButton
                    title="Right"
                    icon="bi-arrow-right"
                    recording={recording}
                    onClick={() => HandleKey('right')}
                />
            </div>
            <div className="d-flex flex-row pb-3 mx-auto">
                <SpacerButton />
                <IrButton
                    title="Down"
                    icon="bi-arrow-down"
                    recording={recording}
                    onClick={() => HandleKey('down')}
                />
                <SpacerButton />
            </div>
            <div className="d-flex flex-row mx-auto">
                <IrButton
                    title="Volume Down"
                    icon="bi-volume-down-fill"
                    recording={recording}
                    onClick={() => HandleKey('vol_down')}
                />
                <IrButton
                    title="Mute"
                    icon="bi-volume-mute-fill"
                    recording={recording}
                    onClick={() => HandleKey('mute')}
                />
                <IrButton
                    title="Volume Up"
                    icon="bi-volume-up-fill"
                    recording={recording}
                    onClick={() => HandleKey('vol_up')}
                />
            </div>
            <div className="d-flex flex-row mx-auto">
                <IrButton
                    title="Settings"
                    icon="bi-gear-fill"
                    variant="secondary"
                    recording={recording}
                    onClick={() => HandleKey('settings')}
                />
                <SpacerButton />
                <IrButton
                    title="Exit"
                    icon="bi-arrow-return-left"
                    variant="secondary"
                    recording={recording}
                    onClick={() => HandleKey('exit')}
                />
            </div>
        </div>
    );
};

TvRemote.propTypes = {
    recording: PropTypes.bool,
    addMacroAction: PropTypes.func.isRequired
};

const IrMacros = ({ recording, setRecording, newMacroActions, setNewMacroActions }) => {
    const {
        irMacros,
        send_command,
        add_ir_macro,
        edit_ir_macro,
        delete_ir_macro
    } = useContext(ApiCardContext);

    const [showNewMacro, setShowNewMacro] = useState(false);
    const [newMacroName, setNewMacroName] = useState('');

    const runMacro = (name) => {
        send_command({command: 'ir_run_macro', macro_name: name});
    };

    const startRecording = () => {
        if (Object.keys(irMacros).includes(newMacroName)) {
            // Add existing actions to state before starting
            resumeRecording(newMacroName);
        } else {
            // Ensure actions state is empty (prevent actions from last
            // recorded macro being duplicated in next macro)
            setNewMacroActions([]);
            setRecording(true);
        }
    };

    const resumeRecording = (name) => {
        // Populate state with existing name and actions
        setNewMacroName(name);
        setNewMacroActions(irMacros[name]);
        // Open collapse to show save button, start recording
        setShowNewMacro(true);
        setRecording(true);
    };

    const finishRecording = () => {
        setRecording(false);
        // Call edit endpoint if adding more actions to existing macro
        if (Object.keys(irMacros).includes(newMacroName)) {
            edit_ir_macro(newMacroName, newMacroActions);
        // Call add endpoint if recording new macro
        } else {
            add_ir_macro(newMacroName, newMacroActions);
        }
        setNewMacroName('');
    };

    return (
        <div className="d-flex flex-column remote mx-auto mb-4">
            <div className="row text-center">
                <h4 className="my-2">
                    IR Macros
                </h4>
            </div>

            {Object.entries(irMacros).map(([name, _]) => {
                return (
                    <div key={name} className="d-flex flex-row my-2">
                        <ButtonGroup className="w-100 mx-3">
                            <Button
                                variant="primary"
                                size="lg"
                                className="w-100"
                                onClick={() => runMacro(name)}

                            >
                                {name}
                            </Button>

                            <DropdownButton
                                as={ButtonGroup}
                                size="lg"
                                variant="success"
                                title={<i className="bi-pencil"></i>}
                                align="end"
                                className="macro-options"
                            >
                                <Dropdown.Item
                                    onClick={() => openEditIrMacroModal(name)}
                                >
                                    <i className="bi-pencil"></i> Edit
                                </Dropdown.Item>
                                <Dropdown.Item
                                    onClick={() => resumeRecording(name)}
                                >
                                    <i className="bi-record-circle-fill"></i> Record
                                </Dropdown.Item>
                                <Dropdown.Item
                                    onClick={() => delete_ir_macro(name)}
                                >
                                    <i className="bi-trash"></i> Delete
                                </Dropdown.Item>
                            </DropdownButton>
                        </ButtonGroup>
                    </div>
                );
            })}

            <Button
                variant="secondary"
                className="my-3 mx-auto"
                onClick={() => setShowNewMacro(!showNewMacro)}
            >
                <i className="bi-plus-lg"></i>
            </Button>

            <Collapse in={showNewMacro}>
                <div>
                    <div className="d-flex flex-column">
                        <FloatingLabel
                            label="New macro name"
                            className="px-3 pb-3"
                        >
                            <Form.Control
                                id="new-macro-name"
                                type="text"
                                className="mb-3"
                                placeholder="New macro name"
                                value={newMacroName}
                                onChange={(e) => setNewMacroName(e.target.value)}
                                disabled={recording}
                            />
                        </FloatingLabel>
                        <Button
                            variant="success"
                            className="mx-auto"
                            onClick={recording ? finishRecording : startRecording}
                        >
                            {recording ? 'Save Macro' : 'Start Recording'}
                        </Button>
                    </div>
                </div>
            </Collapse>
        </div>
    );
};

IrMacros.propTypes = {
    recording: PropTypes.bool.isRequired,
    setRecording: PropTypes.func.isRequired,
    newMacroActions: PropTypes.array.isRequired,
    setNewMacroActions: PropTypes.func.isRequired
};

const IrRemotes = () => {
    const { status } = useContext(ApiCardContext);

    const [recordingMacro, setRecordingMacro] = useState(false);
    const [newMacroActions, setNewMacroActions] = useState([]);

    const addMacroAction = (action) => {
        setNewMacroActions([ ...newMacroActions, action]);
    };

    if (status.metadata.ir_blaster) {
        return (
            <>
                {status.metadata.ir_targets.includes('tv') ? (
                    <TvRemote recording={recordingMacro} addMacroAction={addMacroAction} />
                ) : null }
                {status.metadata.ir_targets.includes('ac') ? (
                    <AcRemote recording={recordingMacro} addMacroAction={addMacroAction} />
                ) : null }
                <IrMacros
                    recording={recordingMacro}
                    setRecording={setRecordingMacro}
                    newMacroActions={newMacroActions}
                    setNewMacroActions={setNewMacroActions}
                />
                <EditIrMacroModal />
            </>
        );
    } else {
        return null;
    }
};

export default IrRemotes;
