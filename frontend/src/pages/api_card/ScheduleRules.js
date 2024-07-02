import React, { useState, useContext } from 'react';
import PropTypes from 'prop-types';
import { ApiCardContext } from 'root/ApiCardContext';
import Table from 'react-bootstrap/Table';
import { TimeField } from 'inputs/TimeField';
import { RuleField } from 'inputs/RuleField';
import DeleteOrEditButton from 'inputs/DeleteOrEditButton';
import Button from 'react-bootstrap/Button';

const ScheduleRuleRow = ({ id, time, rule, getButtonState, className='' }) => {
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

    return (
        <tr className={className}>
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
                    status={getButtonState(time, newTime, rule, newRule)}
                    handleDelete={() => console.log('delete')}
                    handleEdit={() => console.log('edit')}
                />
            </td>
        </tr>
    );
};

ScheduleRuleRow.propTypes = {
    id: PropTypes.string,
    time: PropTypes.string,
    rule: PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.number,
        PropTypes.object,
    ]),
    getButtonState: PropTypes.func,
    getButtonDisabled: PropTypes.func,
    className: PropTypes.string
};


const ExistingScheduleRule = ({ id, time, rule }) => {
    const getButtonState = (oldTime, newTime, oldRule, newRule) => {
        if (oldTime != newTime || oldRule != newRule) {
            return 'edit';
        }
        return 'delete';
    };

    return (
        <ScheduleRuleRow
            id={id}
            time={time}
            rule={rule}
            getButtonState={getButtonState}
        />
    );
};

ExistingScheduleRule.propTypes = {
    id: PropTypes.string,
    time: PropTypes.string,
    rule: PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.number,
        PropTypes.object,
    ]),
    className: PropTypes.string
};

const NewScheduleRule = ({ id, visible }) => {
    const getButtonState = (_, newTime, __, newRule) => {
        if (newTime && newRule) {
            return 'edit';
        }
        return 'delete';
    };

    return (
        <ScheduleRuleRow
            id={id}
            time={''}
            rule={''}
            getButtonState={getButtonState}
            className={visible ? '' : 'd-none'}
        />
    );
};

NewScheduleRule.propTypes = {
    id: PropTypes.string,
    visible: PropTypes.bool
};

const ScheduleRulesTable = ({ id, schedule }) => {
    const [showNewRule, setShowNewRule] = useState(false);

    return (
        <div className="collapse text-center" id={`${id}-schedule-rules`}>
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
                            <ExistingScheduleRule
                                key={time}
                                id={id}
                                time={time}
                                rule={schedule[time]}
                            />
                        );
                    })}
                    <NewScheduleRule
                        key={'new'}
                        id={id}
                        visible={showNewRule}
                    />
                </tbody>
            </Table>

            <div className="text-center mx-3 mb-3">
                <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setShowNewRule(true)}
                >
                    <i className="bi-plus-lg"></i>
                </Button>
            </div>
        </div>
    );
};

ScheduleRulesTable.propTypes = {
    id: PropTypes.string,
    schedule: PropTypes.object
};

export default ScheduleRulesTable;
