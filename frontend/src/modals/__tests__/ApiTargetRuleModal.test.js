import React from 'react';
import ApiTargetRuleModal, { showApiTargetRuleModal } from '../ApiTargetRuleModal';

let checkOutput;

const mockApiTargetOptions = {
    "device1": {
        "display": "Air Conditioner (api-target)",
        "options": [
            "enable",
            "disable",
            "enable_in",
            "disable_in",
            "set_rule",
            "reset_rule",
            "turn_on",
            "turn_off"
        ]
    },
    "sensor1": {
        "display": "Thermostat (si7021)",
        "options": [
            "enable",
            "disable",
            "enable_in",
            "disable_in",
            "set_rule",
            "reset_rule"
        ]
    },
    "ir_key": {
        "display": "Ir Blaster",
        "options": [
            "tv",
            "ac"
        ],
        "keys": {
            "tv": [
                "power",
                "vol_up",
                "vol_down",
                "mute",
                "up",
                "down",
                "left",
                "right",
                "enter",
                "settings",
                "exit",
                "source"
            ],
            "ac": [
                "start",
                "stop",
                "off"
            ]
        }
    },
    "ignore": {
        "display": "Ignore action"
    }
};

const TestComponent = () => {
    // Create mock called when submit button clicked
    checkOutput = jest.fn();

    const existingRule = {
        "on": [
            "enable",
            "device1"
        ],
        "off": [
            "disable",
            "device1"
        ]
    };

    const openNewRule = () => {
        showApiTargetRuleModal('', mockApiTargetOptions, checkOutput);
    };

    const openExistingRule = () => {
        showApiTargetRuleModal(existingRule, mockApiTargetOptions, checkOutput);
    };

    return (
        <>
            <button onClick={openNewRule}>
                Add New Rule
            </button>
            <button onClick={openExistingRule}>
                Edit Existing Rule
            </button>
            <ApiTargetRuleModal />
        </>
    );
};

describe('ApiTargetRuleModal', () => {
    let component, user;

    beforeEach(() => {
        // Render component + create userEvent instance to use in tests
        user = userEvent.setup();
        component = render(
            <TestComponent />
        );
    });

    it('returns the correct object when rule targets a device', async () => {
        // Open modal with existing rule, click submit
        await user.click(component.getByText('Edit Existing Rule'));
        await user.click(component.getByText('Submit'));

        // Confirm correct rule
        expect(checkOutput).toHaveBeenCalledWith({
            "on": [
                "enable",
                "device1"
            ],
            "off": [
                "disable",
                "device1"
            ]
        });
    });

    it('returns the correct object when rule targets an IR Blaster', async () => {
        // Open modal with blank prompt
        await user.click(component.getByText('Add New Rule'));

        // Select IR Blaster, TV remote, power key
        await user.selectOptions(component.getAllByRole('combobox')[0], 'ir_key');
        await user.selectOptions(component.getAllByRole('combobox')[1], 'tv');
        await user.selectOptions(component.getAllByRole('combobox')[2], 'power');

        // Change to off action, select same options
        await user.click(component.getByText('Off Action'));
        await user.selectOptions(component.getAllByRole('combobox')[0], 'ir_key');
        await user.selectOptions(component.getAllByRole('combobox')[1], 'tv');
        await user.selectOptions(component.getAllByRole('combobox')[2], 'power');

        // Click submit, confirm correct rule
        await user.click(component.getByText('Submit'));
        expect(checkOutput).toHaveBeenCalledWith({
            "on": [
                "ir_key",
                "tv",
                "power"
            ],
            "off": [
                "ir_key",
                "tv",
                "power"
            ]
        });
    });

    it('returns the correct object when rule includes argument', async () => {
        // Open modal with blank prompt
        await user.click(component.getByText('Add New Rule'));

        // Select sensor1, enable_in, enter 60 in argument input
        await user.selectOptions(component.getAllByRole('combobox')[0], 'sensor1');
        await user.selectOptions(component.getAllByRole('combobox')[1], 'enable_in');
        await user.type(component.getByRole('textbox'), '60');

        // Change to off action, select sensor1, disable_in, enter 60 in argument input
        await user.click(component.getByText('Off Action'));
        await user.selectOptions(component.getAllByRole('combobox')[0], 'sensor1');
        await user.selectOptions(component.getAllByRole('combobox')[1], 'disable_in');
        await user.type(component.getByRole('textbox'), '60');

        // Click submit, confirm correct rule
        await user.click(component.getByText('Submit'));
        expect(checkOutput).toHaveBeenCalledWith({
            "on": [
                "enable_in",
                "sensor1",
                "60"
            ],
            "off": [
                "disable_in",
                "sensor1",
                "60"
            ]
        });
    });

    it('returns the correct object when actions are ignore', async () => {
        // Open modal with existing rule
        await user.click(component.getByText('Edit Existing Rule'));

        // Change to off action, select ignore
        await user.click(component.getByText('Off Action'));
        await user.selectOptions(component.getAllByRole('combobox')[0], 'ignore');

        // Change to on action, select ignore
        await user.click(component.getByText('On Action'));
        await user.selectOptions(component.getAllByRole('combobox')[0], 'ignore');

        // Click submit, confirm correct rule
        await user.click(component.getByText('Submit'));
        expect(checkOutput).toHaveBeenCalledWith({
            "on": [
                "ignore"
            ],
            "off": [
                "ignore"
            ]
        });
    });

    it('opens collapse with instructions when help button is clicked', async () => {
        // Open modal
        await user.click(component.getByText('Add New Rule'));

        // Get help button, collapses containing instructions
        const helpButton = component.getByRole('button', { name: 'Help' });
        const helpCollapse = helpButton.parentElement.children[1];
        const examplesCollapse = helpCollapse.children[4];

        // Confirm both collapses are closed
        expect(helpCollapse.classList).not.toContain('show');
        expect(examplesCollapse.classList).not.toContain('show');

        // Click help button, confirm help collapse opens but not examples
        await user.click(helpButton);
        expect(helpCollapse.classList).toContain('show');
        expect(examplesCollapse.classList).not.toContain('show');

        // Click examples button, confirm both collapses are open
        await user.click(component.getByRole('button', { name: 'Examples' }));
        expect(helpCollapse.classList).toContain('show');
        expect(examplesCollapse.classList).toContain('show');

        // Click close button, confirm main collapse closes
        await user.click(component.getByRole('button', { name: 'Close' }));
        expect(helpCollapse.classList).not.toContain('show');
    });

    it('closes modal when X button or background is clicked', async () => {
        // Confirm modal not shown
        expect(component.queryByText('API Target Rule')).toBeNull();

        // Click button, confirm modal appears
        await user.click(component.getByText('Add New Rule'));
        expect(component.queryByText('API Target Rule')).not.toBeNull();

        // Click close button, confirm modal closes
        await user.click(component.getByText('API Target Rule').parentElement.children[2]);
        expect(component.queryByText('API Target Rule')).toBeNull();

        // Open modal again, click backdrop, confirm modal closes
        await user.click(component.getByText('Add New Rule'));
        await user.click(document.querySelector('.modal-backdrop'));
        expect(component.queryByText('API Target Rule')).toBeNull();
    });
});
