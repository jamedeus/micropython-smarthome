import React from 'react';
import PropTypes from 'prop-types';
import Card from 'react-bootstrap/Card';
import Table from 'react-bootstrap/Table';
import 'css/PowerButton.css';
import 'css/TriggerButton.css';

const ClimateDataCard = ({ temperature, humidity }) => {
    return (
        <Card className="mb-4">
            <Card.Body className="d-flex flex-column">
                <div className="d-flex justify-content-between">
                    <h4 className="card-title mx-auto my-auto">
                        Climate Data
                    </h4>
                </div>
                <div id="climate-data-body">
                    <Table borderless className="mt-3">
                        <thead>
                            <tr>
                                <th className="text-center w-50 pb-0">
                                    Temperature
                                </th>
                                <th className="text-center w-50 pb-0">
                                    Humidity
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td className="text-center fs-5">
                                    {temperature}
                                </td>
                                <td className="text-center fs-5">
                                    {humidity}
                                </td>
                            </tr>
                        </tbody>
                    </Table>
                </div>
            </Card.Body>
        </Card>
    );
};

ClimateDataCard.propTypes = {
    temperature: PropTypes.string.isRequired,
    humidity: PropTypes.string.isRequired
};

export default ClimateDataCard;
