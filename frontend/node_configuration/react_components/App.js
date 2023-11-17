import React from 'react';
import InstanceCard from './InstanceCard';
import MetadataSection from './MetadataSection';
import IrBlasterSection from './IrBlasterSection';
import { TransitionGroup, CSSTransition } from 'react-transition-group';


// Takes object and key prefix, returns all keys that begin with prefix
function filterObject(obj, prefix) {
    return Object.entries(obj).reduce((acc, [key, value]) => {
        if (key.startsWith(prefix)) {
            acc[key] = value;
        }
        return acc;
    }, {});
};


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
};


class App extends React.Component {
    constructor(props) {
        super(props);
        // Default state object if not received from context
        this.state = {
            metadata: {
                id: '',
                floor: '',
                location: '',
                schedule_keywords: {}
            },
            wifi: {
                ssid: '',
                password: ''
            },
            ir_blaster: {
                configured: false,
                pin: '',
                target: []
            }
        };
    }

    componentDidMount() {
        // Overwrite state with config received from context (if present)
        const config = JSON.parse(document.getElementById("config").textContent);
        console.log(config)
        if (config) {
            if (config.ir_blaster !== undefined) {
                config.ir_blaster.configured = true;
            }
            for (const i in config) {
                if (i.startsWith('device') || i.startsWith('sensor')) {
                    config[i]['uniqueID'] = Math.random();
                };
            }
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
    startDeletingInstance = async (id) => {
        // Get category (device or sensor) and index of deleted card
        const category = id.replace(/[0-9]/g, '');
        const index = id.replace(/[a-zA-z]/g, '');

        // Get reference to deleted card, array of cards in category, and category add button
        const card = document.getElementById(`${id}-card`);
        const cards = Array.from(document.getElementById(`${category}s`).children);
        const button = document.getElementById(`add_${category}`);

        // Get animation height (card height + 1.5rem spacing), set CSS var used in animation
        const remPx = parseFloat(getComputedStyle(document.documentElement).fontSize)
        const animation_height = card.clientHeight / remPx + 1.5;
        document.documentElement.style.setProperty('--animation-height', `${animation_height}rem`);

        // Wait for animation to complete before removing from state object
        await delete_animation(cards, index, button);
        this.deleteInstance(id)
    }

    // Called from delete button handler after animation completes
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
    handleInputChange = (id, param, value) => {
        console.log(param)
        this.setState(prevState => {
            prevState[id][param] = value;
            return prevState;
        });
    };

    // Handler for IR target checkboxes
    handleIrTargetSelect = (target, checked) => {
        this.setState(prevState => {
            // Add target if not already present
            if (checked) {
                if (prevState.ir_blaster.target.indexOf(target) === -1) {
                    prevState.ir_blaster.target.push(target);
                }

            // Remove target
            } else {
                console.log(`Remove ${target}`)
                prevState.ir_blaster.target = prevState.ir_blaster.target.filter(existing => existing !== target);
            };
            return prevState;
        });
    }

    // Render 2 column layout with device and sensor cards
    renderLayout = () => {
        const deviceEntries = (
            <>
                {Object.entries(this.state)
                .filter(([id, _]) => id.startsWith('device'))
                .map(([id, config]) => (
                    <InstanceCard
                        key={config.uniqueID}
                        id={id}
                        category="device"
                        config={config}
                        onDelete={() => this.startDeletingInstance(id)}
                        onInputChange={(paramName, value) => this.handleInputChange(id, paramName, value)}
                        onTypeChange={(event) => this.changeInstanceType(id, "device", event)}
                    />
                ))}
            </>
        );

        const sensorEntries = (
            <>
                {Object.entries(this.state)
                .filter(([id, _]) => id.startsWith('sensor'))
                .map(([id, config]) => (
                    <InstanceCard
                        key={config.uniqueID}
                        id={id}
                        category="sensor"
                        config={config}
                        onDelete={() => this.startDeletingInstance(id)}
                        onInputChange={(paramName, value) => this.handleInputChange(id, paramName, value)}
                        onTypeChange={(event) => this.changeInstanceType(id, "sensor", event)}
                    />
                ))}
            </>
        );

        return (
            <>
                <h1 className="text-center pt-3 pb-4">{document.title}</h1>

                <MetadataSection
                    key="metadata"
                    id={this.state.metadata.id}
                    floor={this.state.metadata.floor}
                    location={this.state.metadata.location}
                    ssid={this.state.wifi.ssid}
                    password={this.state.wifi.password}
                    onChange={this.handleInputChange}
                />

                <IrBlasterSection
                    key="ir_blaster"
                    configured={this.state.ir_blaster.configured}
                    pin={this.state.ir_blaster.pin}
                    target={this.state.ir_blaster.target}
                    onChange={this.handleInputChange}
                    onTargetSelect={this.handleIrTargetSelect}
                />

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


// Delete instance card animation
// Takes array of card divs, index of card to delete, add instance button
// Fades out card to delete, slides up all cards below + add button
async function delete_animation(cards, index, button) {
    return new Promise(async resolve => {
        // Fade out card to be deleted
        cards[index].classList.add('fade-out');

        // Slide up all cards below, wait for animation to complete
        for (let i=parseInt(index)+1; i<cards.length; i++) {
            cards[i].children[0].classList.add('slide-up');
        };
        button.classList.add('slide-up');
        await sleep(800);

        // Prevent cards jumping higher when hidden card is actually deleted
        for (let i=parseInt(index)+1; i<cards.length; i++) {
            cards[i].children[0].classList.remove('slide-up');
        };
        button.classList.remove('slide-up');
        resolve();
    });
};


export default App;
