import React, { useContext } from 'react';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import { ApiCardContext } from 'root/ApiCardContext';
import SensorCard from './SensorCard';
import DeviceCard from './DeviceCard';


const Layout = () => {
    // Get status object, function to make API calls
    const {status, send_command} = useContext(ApiCardContext);

    return (
        <Row>
            <Col id="sensor-cards" className="col-sm">
                {Object.keys(status.sensors).map((sensor) => {
                    return <SensorCard
                                key={sensor}
                                id={sensor}
                                params={status.sensors[sensor]}
                            />;
                })}
            </Col>
            <Col id="device-cards" className="col-sm">
                {Object.keys(status.devices).map((device) => {
                    return <DeviceCard
                                key={device}
                                id={device}
                                params={status.devices[device]}
                            />;
                })}
            </Col>
        </Row>
    );
}


export default Layout;
