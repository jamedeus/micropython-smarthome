import React, { useRef } from 'react';
import PropTypes from 'prop-types';
import Modal from 'react-bootstrap/Modal';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';
import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    TimeScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';
import 'chartjs-adapter-date-fns';

ChartJS.register(
    TimeScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

// Used to read CSS variables into options object below
const getCssVariable = (cssVar) => {
    return getComputedStyle(document.documentElement).getPropertyValue(cssVar);
};

const TempHistoryChart = ({ visible, setVisible, tempHistory, tempHistoryLabels }) => {
    const chartRef = useRef(null);

    const data = {
        labels: tempHistoryLabels,
        datasets: [{
            data: tempHistory,
            label: "Temp",
            borderColor: getCssVariable('--chart-line-color'),
            backgroundColor: getCssVariable('--chart-point-color'),
            fill: true
        }]
    };

    const options = {
        plugins: {
            legend: {
                display: false,
            }
        },
        scales: {
            x: {
                type: 'time',
                time: {
                    unit: 'minute',
                    displayFormats: {
                        minute: 'H:mm:ss'
                    }
                },
                ticks: {
                    source: 'data',
                    color: getCssVariable('--chart-tick-color')
                },
            },
            y: {
                suggestedMin: 70,
                suggestedMax: 75,
                ticks: {
                    color: getCssVariable('--chart-tick-color'),
                    stepSize: 1,
                }
            }
        }
    };

    return (
        <Modal show={visible} onHide={() => setVisible(false)} centered size="lg">
            <HeaderWithCloseButton
                title="Temperature History"
                onClose={() => setVisible(false)}
                size="3"
            />

            <Modal.Body className="d-flex m-3">
                <Line ref={chartRef} data={data} options={options} />
            </Modal.Body>
        </Modal>
    );
};

TempHistoryChart.propTypes = {
    visible: PropTypes.bool.isRequired,
    setVisible: PropTypes.func.isRequired,
    tempHistory: PropTypes.array.isRequired,
    tempHistoryLabels: PropTypes.array.isRequired
};

export default TempHistoryChart;
