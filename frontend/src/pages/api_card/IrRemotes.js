import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import { ApiCardContext } from 'root/ApiCardContext';
import 'css/remote.css';

const IrButton = ({title, icon, variant='primary', onClick}) => {
    return (
        <Button
            variant={variant}
            size="lg"
            className="m-3 ir-btn"
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
    onClick: PropTypes.func.isRequired
};

const AcRemote = () => {
    const { send_command } = useContext(ApiCardContext);

    const HandleKey = (key) => {
        send_command({'command': 'ir', 'ir_target': 'ac', 'key': key});
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
                    onClick={() => HandleKey('stop')}
                />
                <IrButton
                    title="Turn off fan"
                    icon="bi-x-octagon-fill"
                    onClick={() => HandleKey('off')}
                />
                <IrButton
                    title="Start cooling"
                    icon="bi-snow"
                    onClick={() => HandleKey('start')}
                />
            </div>
        </div>
    );
};

const TvRemote = () => {
    const { send_command } = useContext(ApiCardContext);

    const HandleKey = (key) => {
        send_command({'command': 'ir', 'ir_target': 'tv', 'key': key});
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
                    onClick={() => HandleKey('power')}
                />
                <SpacerButton />
                <IrButton
                    title="Source"
                    icon="bi-upload"
                    onClick={() => HandleKey('source')}
                />
            </div>
            <div className="d-flex flex-row mx-auto">
                <SpacerButton />
                <IrButton
                    title="Up"
                    icon="bi-arrow-up"
                    onClick={() => HandleKey('up')}
                />
                <SpacerButton />
            </div>
            <div className="d-flex flex-row mx-auto">
                <IrButton
                    title="Left"
                    icon="bi-arrow-left"
                    onClick={() => HandleKey('left')}
                />
                <IrButton
                    title="Enter"
                    icon="bi-app"
                    onClick={() => HandleKey('enter')}
                />
                <IrButton
                    title="Right"
                    icon="bi-arrow-right"
                    onClick={() => HandleKey('right')}
                />
            </div>
            <div className="d-flex flex-row pb-3 mx-auto">
                <SpacerButton />
                <IrButton
                    title="Down"
                    icon="bi-arrow-down"
                    onClick={() => HandleKey('down')}
                />
                <SpacerButton />
            </div>
            <div className="d-flex flex-row mx-auto">
                <IrButton
                    title="Volume Down"
                    icon="bi-volume-down-fill"
                    onClick={() => HandleKey('vol_down')}
                />
                <IrButton
                    title="Mute"
                    icon="bi-volume-mute-fill"
                    onClick={() => HandleKey('mute')}
                />
                <IrButton
                    title="Volume Up"
                    icon="bi-volume-up-fill"
                    onClick={() => HandleKey('vol_up')}
                />
            </div>
            <div className="d-flex flex-row mx-auto">
                <IrButton
                    title="Settings"
                    icon="bi-gear-fill"
                    variant="secondary"
                    onClick={() => HandleKey('settings')}
                />
                <SpacerButton />
                <IrButton
                    title="Exit"
                    icon="bi-arrow-return-left"
                    variant="secondary"
                    onClick={() => HandleKey('exit')}
                />
            </div>
        </div>
    );
};

const IrRemotes = () => {
    const { status } = useContext(ApiCardContext);

    if (status.metadata.ir_blaster) {
        return (
            <>
                {status.metadata.ir_targets.includes('tv') ? <TvRemote /> : null }
                {status.metadata.ir_targets.includes('ac') ? <AcRemote /> : null }
            </>
        );
    } else {
        return null;
    }
};

export default IrRemotes;
