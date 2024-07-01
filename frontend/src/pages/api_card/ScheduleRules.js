import React, { useState, useContext } from 'react';
import PropTypes from 'prop-types';
import { ApiCardContext } from 'root/ApiCardContext';
import Table from 'react-bootstrap/Table';
import { TimeField } from 'inputs/TimeField';
import { RuleField } from 'inputs/RuleField';
import DeleteOrEditButton from 'inputs/DeleteOrEditButton';


const ScheduleRule = ({ id, time, rule }) => {
    // Get status object for instance
    const { status } = useContext(ApiCardContext);
    const instance = status[`${id.replace(/[0-9]/g, '')}s`][id];

    // States to store modified timestamp and rule
    const [newTime, setNewTime] = useState(time);
    const [newRule, setNewRule] = useState(rule);

    // Called by TimeField when user changes value and closes
    const handleNewTimestamp = (newTimestamp, _) => {
        setNewTime(newTimestamp);
    };

    // Called by RuleField when user changes value and closes
    const handleNewRule = (rule, fade_rule, duration, range_rule) => {
        if (range_rule && fade_rule) {
            // Fade rule: Combine params into single string
            setNewRule(`fade/${rule}/${duration}`);
        } else {
            setNewRule(rule);
        }
    };

    // Controls button state
    const modified = time != newTime || rule != newRule;

    return (
        <tr>
            <td>
                <TimeField
                    timestamp={newTime}
                    handleChange={handleNewTimestamp}
                    schedule_keywords={status.metadata.schedule_keywords}
                    highlightInvalid={false}
                />
            </td>
            <td>
                <RuleField
                    instance={instance}
                    category={id.replace(/[0-9]/g, '')}
                    type={instance.type}
                    rule={newRule}
                    handleChange={handleNewRule}
                />
            </td>
            <td className="min">
                <DeleteOrEditButton
                    status={modified ? 'edit' : 'delete'}
                    handleDelete={() => console.log('delete')}
                    handleEdit={() => console.log('edit')}
                />
            </td>
        </tr>
    );
};

ScheduleRule.propTypes = {
    id: PropTypes.string,
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
                    return (
                        <ScheduleRule
                            key={`${id}-rule-${index}`}
                            id={id}
                            time={time}
                            rule={schedule[time]}
                        />
                    );
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
