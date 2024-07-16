// Map IR Blaster targets to list of key options
// TODO remove once IR Blaster metadata added
const ir_keys = {
    tv: [
        'power',
        'vol_up',
        'vol_down',
        'mute',
        'up',
        'down',
        'left',
        'right',
        'enter',
        'settings',
        'exit',
        'source'
    ],
    ac: [
        'start',
        'stop',
        'off'
    ]
};

// Valid ESP32 sensor pins (input/output and input only)
const sensorPins = [
    '4',
    '5',
    '13',
    '14',
    '15',
    '16',
    '17',
    '18',
    '19',
    '21',
    '22',
    '23',
    '25',
    '26',
    '27',
    '32',
    '33',
    '34',
    '35',
    '36',
    '39'
];

// Valid ESP32 device pins (input/output)
const devicePins = [
    '4',
    '13',
    '16',
    '17',
    '18',
    '19',
    '21',
    '22',
    '23',
    '25',
    '26',
    '27',
    '32',
    '33'
];

export { ir_keys, sensorPins, devicePins };
