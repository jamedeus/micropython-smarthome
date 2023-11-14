import React from 'react';
import InstanceCard from './InstanceCard';
import { TransitionGroup, CSSTransition } from 'react-transition-group';
import './Animation.css';


// Takes object and key prefix, returns all keys that begin with prefix
function filterObject(obj, prefix) {
    return Object.entries(obj).reduce((acc, [key, value]) => {
        if (key.startsWith(prefix)) {
            acc[key] = value;
        }
        return acc;
    }, {});
};


class App extends React.Component {
    constructor(props) {
        super(props);
        // Default state object if not received from context
        this.state = {
            metadata: {},
            wifi: {}
        };
    }

    componentDidMount() {
        // Overwrite state with config received from context (if present)
        const config = JSON.parse(document.getElementById("config").textContent);
        console.log(config)
        if (config) {
            this.setState({ ...config });
        }
    }

    logState = () => {
        console.log(this.state);
    };

    // Handler for add device and add sensor buttons
    addInstance = (category) => {
        this.setState(prevState => {
            // Get index of new instance
            const index = Object.keys(filterObject(prevState, category)).length + 1;

            // Add key to state object with empty config
            // Will be populated with metadata template when user selects type
            prevState[`${category}${index}`] = {}

            return prevState;
        });
    };

    // Handler for delete button on device and sensor cards
    deleteInstance = (id) => {
        this.setState(prevState => {
            // Remove deleted instance from state object
            delete prevState[id]
            // Decrement all subsequent IDs in state object to prevent gaps in index
            return update_ids(id, prevState);
        });
    };

    // Handler for type select dropdown in device and sensor cards
    changeInstanceType = (id, category, event) => {
        this.setState(prevState => {
            // Get config template for selected type from metadata object
            const template = metadata[`${category}s`][event.target.value]['config_template'];
            // Overwrite section in state object with config template
            prevState[id] = template;
            return prevState;
        })
    };

    // Handler for all inputs inside device and sensor cards
    // Takes device/sensor ID, param, and value; updates state object
    // TODO this has issues for components with multiple inputs (on/off paths, thermostat)
    handleInputChange = (id, param, value) => {
        console.log(param)
        this.setState(prevState => {
            prevState[id][param] = value;
            return prevState;
        });
    };

    // Render 2 column layout with device and sensor cards
    renderLayout = () => {
        const deviceEntries = (
            <TransitionGroup className="device-container">
                {Object.entries(this.state)
                .filter(([key, _]) => key.startsWith('device'))
                .map(([key, config]) => (
                    <CSSTransition key={key} timeout={500} classNames="fade">
                        <InstanceCard
                            key={key}
                            id={key}
                            category="device"
                            config={config}
                            onDelete={() => this.deleteInstance(key)}
                            onInputChange={(paramName, value) => this.handleInputChange(key, paramName, value)}
                            onTypeChange={(event) => this.changeInstanceType(key, "device", event)}
                        />
                    </CSSTransition>
                ))}
            </TransitionGroup>
        );

        const sensorEntries = (
            <TransitionGroup className="sensor-container">
                {Object.entries(this.state)
                .filter(([key, _]) => key.startsWith('sensor'))
                .map(([key, config]) => (
                    <CSSTransition key={key} timeout={500} classNames="fade">
                        <InstanceCard
                            key={key}
                            id={key}
                            category="sensor"
                            config={config}
                            onDelete={() => this.deleteInstance(key)}
                            onInputChange={(paramName, value) => this.handleInputChange(key, paramName, value)}
                            onTypeChange={(event) => this.changeInstanceType(key, "sensor", event)}
                        />
                    </CSSTransition>
                ))}
            </TransitionGroup>
        );

        return (
            <>
                <h1 className="text-center pt-3 pb-4">TEST</h1>

                <div id="page1" className="d-flex flex-column h-100">
                    <div className="row mt-3">
                        <div id="sensors" className="col-sm">
                            <h2 className="text-center">Add Sensors</h2>
                            {sensorEntries}
                            <div id="add_sensor" className="text-center position-relative">
                                <button className="btn-secondary btn mb-3" onClick={() => this.addInstance('sensor')}>Add Sensor</button>
                            </div>
                        </div>
                        <div id="devices" className="col-sm">
                            <h2 className="text-center">Add Devices</h2>
                            {deviceEntries}
                            <div id="add_device" className="text-center position-relative">
                                <button className="btn-secondary btn mb-3" onClick={() => this.addInstance('device')}>Add Device</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="bottom">
                    <button className="log-button" onClick={() => this.logState()}>Log State</button>
                </div>
            </>
        );
    }

    render() {
        return this.renderLayout();
    }
}


// Called by deleteInstance, decrements IDs of all subsequent instances to prevent gaps
// Example: If device2 is deleted, device3 becomes device2, device4 becomes device3, etc
function update_ids(target, state) {
    // Get category (device or sensor) and index of removed instance
    const category = target.replace(/[0-9]/g, '');
    const index = target.replace(/[a-zA-Z]/g, '');

    // Get list of all instances in same category
    var instances = filterObject(state, category);

    // If target is device get list of sensors (used to update target IDs)
    if (category === 'device') {
        var sensors = filterObject(state, 'sensor');
        // Remove device from all sensor targets
        for (const sensor in sensors) {
            state[sensor]['targets'] = state[sensor]['targets'].filter(item => item !== target);
        };
    };

    // Iterate all instances in category starting from the removed instance index
    for (let i=parseInt(index); i<Object.entries(instances).length+1; i++) {
        // Removed index now available, decrement next index by 1
        const new_id = `${category}${i}`;
        const old_id = `${category}${i+1}`;
        state[new_id] = JSON.parse(JSON.stringify(state[old_id]));
        delete state[old_id];

        // Decrement device index in sensor targets lists to match above
        if (category === 'device') {
            for (const sensor in sensors) {
                if (state[sensor]['targets'].includes(old_id)) {
                    state[sensor]['targets'] = state[sensor]['targets'].filter(item => item !== old_id);
                    state[sensor]['targets'].push(new_id);
                };
            };
        };
    }

    return state;
};


export default App;
