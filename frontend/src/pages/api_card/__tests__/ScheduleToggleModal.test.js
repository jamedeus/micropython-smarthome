import React from 'react';
import ScheduleToggleModal, { showScheduleToggle } from '../ScheduleToggleModal';
import { ApiCardContextProvider } from 'root/ApiCardContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockContext } from './mockContext';
import { api_card_metadata } from 'src/testUtils/mockMetadataContext';
import { postHeaders } from 'src/testUtils/headers';

const TestComponent = () => {
    return (
        <>
            <button onClick={() => showScheduleToggle('device3', true)}>
                Schedule Disable
            </button>
            <button onClick={() => showScheduleToggle('device3', false)}>
                Schedule Enable
            </button>
            <ScheduleToggleModal />
        </>
    );
};

describe('ScheduleToggleModal', () => {
    let component, user;

    beforeAll(() => {
        // Create mock state objects
        createMockContext('status', mockContext.status);
        createMockContext('target_ip', mockContext.target_ip);
        createMockContext('recording', mockContext.recording);
        createMockContext('ir_macros', {});
        createMockContext('instance_metadata', api_card_metadata);
        createMockContext('api_target_options', mockContext.api_target_options);
    });

    beforeEach(() => {
        // Render component + create userEvent instance to use in tests
        user = userEvent.setup();
        component = render(
            <MetadataContextProvider>
                <ApiCardContextProvider>
                    <TestComponent />
                </ApiCardContextProvider>
            </MetadataContextProvider>
        );
    });

    it('sends correct payload when ScheduleToggleModal is submitted', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
                "Disable_in_seconds": 900,
                "Disabled": "device3"
            })
        }));

        // Click open button, confirm modal appeared
        await user.click(component.getByText('Schedule Disable'));
        expect(component.queryByText('Schedule Toggle')).not.toBeNull();

        // Click submit button, confirm correct payload sent
        await user.click(component.getByRole('button', { name: 'Schedule' }));
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "disable_in",
                "instance": "device3",
                "delay": "15",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('converts seconds to minutes before making request', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
                "Disable_in_seconds": 600,
                "Disabled": "device3"
            })
        }));

        // Open modal, get inputs
        await user.click(component.getByText('Schedule Disable'));
        const group = document.querySelector('.input-group');
        const action = group.children[0];
        const duration = group.children[2];
        const unitSelect = group.children[3];

        // Change units to seconds and enter 600 in duration field
        await user.selectOptions(unitSelect, 'seconds');
        await user.clear(duration);
        await user.type(duration, '600');

        // Click submit button, confirm payload delay is 10 (minutes)
        await user.click(component.getByRole('button', { name: 'Schedule' }));
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "disable_in",
                "instance": "device3",
                "delay": "10",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('converts hours to minutes before making request', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
                "Enable_in_seconds": 3600,
                "Enabled": "device3"
            })
        }));

        // Open modal, get inputs
        await user.click(component.getByText('Schedule Disable'));
        const group = document.querySelector('.input-group');
        const action = group.children[0];
        const duration = group.children[2];
        const unitSelect = group.children[3];

        // Change action to enable, units to hours, enter 1 in duration field
        await user.click(component.getByText('Schedule Disable'));
        await user.selectOptions(action, 'enable_in');
        await user.selectOptions(unitSelect, 'hours');
        await user.clear(duration);
        await user.type(duration, '1');

        // Click submit button, confirm payload delay is 60 (minutes)
        await user.click(component.getByRole('button', { name: 'Schedule' }));
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "enable_in",
                "instance": "device3",
                "delay": "60",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('limmits the delay field to approximately 1 day', async () => {
        // Open modal, get inputs
        await user.click(component.getByText('Schedule Disable'));
        const group = document.querySelector('.input-group');
        const duration = group.children[2];
        const unitSelect = group.children[3];

        // Simulate user typing a long string, confirm limited to 4 digits
        await user.clear(duration);
        await user.type(duration, '9a9a9a9a9a9a9a9a9a9a9');
        expect(duration.value).toBe('9999');

        // Change units to seconds, confirm duration now accepts 5 digits
        await user.selectOptions(unitSelect, 'seconds');
        await user.clear(duration);
        await user.type(duration, '9a9a9a9a9a9a9a9a9a9a9');
        expect(duration.value).toBe('99999');

        // Change units to hours, confirm duration now accepts 2 digits
        await user.selectOptions(unitSelect, 'hours');
        await user.clear(duration);
        await user.type(duration, '9a9a9a9a9a9a9a9a9a9a9');
        expect(duration.value).toBe('99');
    });

    it('closes modal when X button or background is clicked', async () => {
        // Confirm modal not shown
        expect(component.queryByText('Schedule Toggle')).toBeNull();

        // Click button, confirm modal appears
        await user.click(component.getByText('Schedule Disable'));
        expect(component.queryByText('Schedule Toggle')).not.toBeNull();

        // Click close button, confirm modal closes
        await user.click(component.getByText('Schedule Toggle').parentElement.children[2]);
        expect(component.queryByText('Schedule Toggle')).toBeNull();

        // Open modal again, click backdrop, confirm modal closes
        await user.click(component.getByText('Schedule Disable'));
        await user.click(document.querySelector('.modal-backdrop'));
        expect(component.queryByText('Schedule Toggle')).toBeNull();
    });
});
