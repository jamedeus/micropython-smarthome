import React from 'react';
import App from '../ApiCard';
import { ApiCardContextProvider } from 'root/ApiCardContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockContext } from './mockContext';
import { api_card_metadata } from 'src/testUtils/mockMetadataContext';

describe('UpdateStatus', () => {
    let app;

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
        // Use fake timers
        jest.useFakeTimers();

        // Render app
        app = render(
            <MetadataContextProvider>
                <ApiCardContextProvider>
                    <App />
                </ApiCardContextProvider>
            </MetadataContextProvider>
        );
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    it('requests a status update every 5 seconds', async () => {
        // Mock fetch function to return simulated status update
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: mockContext.status
            })
        }));

        // Confirm has not fetched status update
        expect(global.fetch).not.toHaveBeenCalledWith('/get_status/Test Node');

        // Fast forward 5 seconds, confirm fetched status update
        jest.advanceTimersByTime(5000);
        expect(global.fetch).toHaveBeenCalledWith('/get_status/Test Node');
    });

    it('shows error modal if status update fails', async () => {
        // Mock fetch function to simulate offline node
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 502,
            json: () => Promise.resolve({
                status: 'error',
                message: 'Unable to connect'
            })
        }));

        // Confirm has not fetched status update
        expect(global.fetch).not.toHaveBeenCalledWith('/get_status/Test Node');

        // Fast forward 5 seconds, confirm fetched status update
        jest.advanceTimersByTime(5000);
        expect(global.fetch).toHaveBeenCalledWith('/get_status/Test Node');

        // Confirm error modal is visible
        await waitFor(() => {
            expect(app.queryByText('Attempting to reestablish connection...')).not.toBeNull();
        });

        // Fast forward another 5 seconds, confirm fetched status update again
        jest.advanceTimersByTime(5000);
        expect(global.fetch.mock.calls).toEqual([
            ['/get_status/Test Node'],
            ['/get_status/Test Node'],
        ]);

        // Confirm error modal is still visible
        await waitFor(() => {
            expect(app.queryByText('Attempting to reestablish connection...')).not.toBeNull();
        });
    });

    it('hides error modal once able to update status', async () => {
        // Mock fetch function to simulate offline node
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 502,
            json: () => Promise.resolve({
                status: 'error',
                message: 'Unable to connect'
            })
        }));

        // Fast forward 5 seconds, confirm error modal is visible
        jest.advanceTimersByTime(5000);
        await waitFor(() => {
            expect(app.queryByText('Attempting to reestablish connection...')).not.toBeNull();
        });

        // Mock fetch function to simulate node coming back online
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: mockContext.status
            })
        }));

        // Fast forward another 5 seconds, confirm error modal disappeared
        jest.advanceTimersByTime(5000);
        await waitFor(() => {
            expect(app.queryByText('Attempting to reestablish connection...')).toBeNull();
        });
    });
});
