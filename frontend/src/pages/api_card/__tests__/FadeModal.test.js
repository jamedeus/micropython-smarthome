import React from 'react';
import FadeModal, { showFadeModal } from '../FadeModal';
import { ApiCardContextProvider } from 'root/ApiCardContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockContext } from './mockContext';
import { api_card_metadata } from 'src/testUtils/mockMetadataContext';
import { postHeaders } from 'src/testUtils/headers';

const TestComponent = () => {
    return (
        <>
            <button onClick={() => showFadeModal('device3')}>
                Open Modal
            </button>
            <FadeModal />
        </>
    );
};

describe('FadeModal', () => {
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

        // Reset mock fetch calls (ApiCardContext makes request when rendered)
        jest.clearAllMocks();
    });

    it('sends correct payload when FadeModal is submitted', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
                "device3": "fade/512/600"
            })
        }));

        // Open modal, enter 512 in target brightness field, 600 in duration field
        await user.click(component.getByText('Open Modal'));
        await user.type(component.getByLabelText('Target Brightness'), '512');
        await user.type(component.getByLabelText('Duration (seconds)'), '600');

        // Click start button, confirm correct payload sent
        await user.click(component.getByRole('button', { name: 'Start' }));
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "set_rule",
                "instance": "device3",
                "rule": "fade/512/600",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('submits modal when enter key is pressed in either field', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
                "device3": "fade/512/600"
            })
        }));

        // Open modal, enter 512 in target brightness field, 600 in duration field
        await user.click(component.getByText('Open Modal'));
        await user.type(component.getByLabelText('Target Brightness'), '512');
        await user.type(component.getByLabelText('Duration (seconds)'), '600');

        // Simulate user pressing enter in brightness field, confirm request made
        await userEvent.type(component.getByLabelText('Target Brightness'), '{enter}');
        expect(global.fetch).toHaveBeenCalled();
        jest.clearAllMocks();

        // Reopen, simulate user pressing enter in duration field, confirm request made
        await user.click(component.getByText('Open Modal'));
        await userEvent.type(component.getByLabelText('Duration (seconds)'), '{enter}');
        expect(global.fetch).toHaveBeenCalled();
    });

    it('closes modal when X button or background is clicked', async () => {
        // Confirm modal not shown
        expect(component.queryByText('Start Fade')).toBeNull();

        // Click button, confirm modal appears
        await user.click(component.getByText('Open Modal'));
        expect(component.queryByText('Start Fade')).not.toBeNull();

        // Click close button, confirm modal closes
        await user.click(component.getByText('Start Fade').parentElement.children[2]);
        expect(component.queryByText('Start Fade')).toBeNull();

        // Open modal again, click backdrop, confirm modal closes
        await user.click(component.getByText('Open Modal'));
        await user.click(document.querySelector('.modal-backdrop'));
        expect(component.queryByText('Start Fade')).toBeNull();
    });
});
