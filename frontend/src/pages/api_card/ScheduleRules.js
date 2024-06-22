import React from 'react';
import PropTypes from 'prop-types';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';


const ScheduleRule = ({ time, rule }) => {
    return (
        <tr>
            <td>
                <span className="form-control schedule-rule time">{time}</span>
            </td>
            <td>
                <span className="form-control schedule-rule">{rule}</span>
            </td>
            <td className="min">
                <Button variant="primary" size="sm">
                    <i className="bi-pencil"></i>
                </Button>
            </td>
        </tr>
    );
};

ScheduleRule.propTypes = {
    time: PropTypes.string,
    rule: PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.number,
        PropTypes.object,
    ]),
};


const ScheduleRulesTable = ({ id, schedule }) => {
    return (
        <Table borderless>
            <thead>
                <tr>
                    <th className="w-50">Time</th>
                    <th className="w-50">Rule</th>
                </tr>
            </thead>
            <tbody>
                {Object.keys(schedule).map((time, index) => {
                    return <ScheduleRule key={`${id}-rule-${index}`} time={time} rule={schedule[time]} />;
                })}
            </tbody>
        </Table>
    );
};

ScheduleRulesTable.propTypes = {
    id: PropTypes.string,
    schedule: PropTypes.object
};


export { ScheduleRule, ScheduleRulesTable };
