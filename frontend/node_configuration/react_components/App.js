import React from 'react';
import InstanceCard from './InstanceCard';


class App extends React.Component {
    constructor(props) {
        super(props);
        // Default state object if not received from context
        this.state = {
            metadata: {},
            wifi: {},
            num_sensors: 0,
            num_devices: 0
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
            prevState[`num_${category}s`] += 1;
            const newIndex = prevState[`num_${category}s`];

            // Add key to state object with empty config
            // Will be populated with metadata template when user selects type
            prevState[`${category}${newIndex}`] = {}

            return prevState;
        });
    };

    // Handler for delete button on device and sensor cards
    deleteInstance = (id) => {
        this.setState(prevState => {
            // Delete from state object
            delete prevState[id];

            // Decrement count in state object
            if (id.startsWith('sensor')) {
                prevState.num_sensors -= 1;
            } else {
                prevState.num_devices -= 1;
            };

            // TODO fix gaps in sequential keys

            return prevState;
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
        const deviceEntries = Object.entries(this.state)
        .filter(([key, _]) => key.startsWith('device'))
        .map(([key, config]) => (
            <InstanceCard
                key={key}
                id={key}
                category="device"
                config={config}
                onDelete={() => this.deleteInstance(key)}
                onInputChange={(paramName, value) => this.handleInputChange(key, paramName, value)}
                onTypeChange={(event) => this.changeInstanceType(key, "device", event)}
            />
        ));

        const sensorEntries = Object.entries(this.state)
        .filter(([key, _]) => key.startsWith('sensor'))
        .map(([key, config]) => (
            <InstanceCard
                key={key}
                id={key}
                category="sensor"
                config={config}
                onDelete={() => this.deleteInstance(key)}
                onInputChange={(paramName, value) => this.handleInputChange(key, paramName, value)}
                onTypeChange={(event) => this.changeInstanceType(key, "sensor", event)}
            />
        ));

        return (
            <>
                <h1 className="text-center pt-3 pb-4">TEST</h1>

                <div id="page1" className="d-flex flex-column h-100">
                    <div className="row mt-3">
                        <div id="sensors" className="col-sm">
                            <h2 className="text-center">Add Sensors</h2>
                            <div id="addSensorButton" className="text-center position-relative">
                                <button className="btn-secondary btn mb-3" onClick={() => this.addInstance('sensor')}>Add Sensor</button>
                                {sensorEntries}
                            </div>
                        </div>
                        <div id="devices" className="col-sm">
                            <h2 className="text-center">Add Devices</h2>
                            <div id="addDeviceButton" className="text-center position-relative">
                                <button className="btn-secondary btn mb-3" onClick={() => this.addInstance('device')}>Add Device</button>
                                {deviceEntries}
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

export default App;
