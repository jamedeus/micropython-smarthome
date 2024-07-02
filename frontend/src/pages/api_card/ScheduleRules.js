import React, { useState, useContext } from 'react';
import PropTypes from 'prop-types';
import { ApiCardContext } from 'root/ApiCardContext';
import Table from 'react-bootstrap/Table';
import { TimeField } from 'inputs/TimeField';
import { RuleField } from 'inputs/RuleField';
import DeleteOrEditButton from 'inputs/DeleteOrEditButton';
import Button from 'react-bootstrap/Button';

const ScheduleRuleRow = ({ id, time, rule, getButtonState, handleEdit, handleDelete, className='' }) => {
    // Get status object for instance
    const { status } = useContext(ApiCardContext);
    const instance = status[`${id.replace(/[0-9]/g, '')}s`][id];

    // States to store modified timestamp and rule
    const [newTime, setNewTime] = useState(time);
    const [newRule, setNewRule] = useState(rule);

    // State to show button loading animation
    const [loading, setLoading] = useState(false);

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

    const onEdit = () => {
        setLoading(true);
        handleEdit(newTime, newRule);
    };

    const onDelete = () => {
        setLoading(true);
        handleDelete(id, time);
    };

    const loadingButtonStatus = loading ? 'loading' : getButtonState(time, newTime, rule, newRule);

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
                    status={loadingButtonStatus}
                    handleDelete={onDelete}
                    handleEdit={onEdit}
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
    handleEdit: PropTypes.func,
    handleDelete: PropTypes.func,
    className: PropTypes.string
};


const ExistingScheduleRule = ({ id, time, rule }) => {
    const { edit_schedule_rule, delete_schedule_rule } = useContext(ApiCardContext);

    const handlEdit = async (timestamp, rule) => {
        await edit_schedule_rule(id, time, timestamp, String(rule));
    }

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
            handleEdit={handlEdit}
            handleDelete={delete_schedule_rule}
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
    ])
};

const NewScheduleRule = ({ id, visible, setShowNewRule }) => {
    const { add_schedule_rule } = useContext(ApiCardContext);

    const handleAdd = async (timestamp, rule) => {
        const result = await add_schedule_rule(id, timestamp, String(rule));
        if (result) {
            setShowNewRule(false);
        };
    };

    const handleDelete = async () => {
        setShowNewRule(false);
    };

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
            handleEdit={handleAdd}
            handleDelete={handleDelete}
            className={visible ? '' : 'd-none'}
        />
    );
};

NewScheduleRule.propTypes = {
    id: PropTypes.string,
    visible: PropTypes.bool,
    setShowNewRule: PropTypes.func
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
                        setShowNewRule={setShowNewRule}
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
