import React, { useContext } from 'react';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import { ApiCardContext } from 'root/ApiCardContext';
import InstanceCard from './InstanceCard';
import IrRemotes from './IrRemotes';

const Layout = () => {
    const {status} = useContext(ApiCardContext);

    return (
        <Row>
            {Object.keys(status.sensors).length ? (
                <Col id="sensor-cards" className="col-sm">
                    {Object.keys(status.sensors).map((sensor) => {
                        return <InstanceCard key={sensor} id={sensor} />;
                    })}
                </Col>
            ) : null}
            {Object.keys(status.devices).length || status.metadata.ir_blaster ? (
                <Col id="device-cards" className="col-sm">
                    {Object.keys(status.devices).map((device) => {
                        return <InstanceCard key={device} id={device} />;
                    })}
                    <IrRemotes />
                </Col>
            ) : null}
        </Row>
    );
};

export default Layout;
