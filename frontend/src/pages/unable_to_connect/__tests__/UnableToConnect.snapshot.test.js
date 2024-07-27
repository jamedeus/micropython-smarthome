import React from 'react';
import App from '../UnableToConnect';
import createMockContext from 'src/testUtils/createMockContext';

describe('UnableToConnect', () => {
    it('matches snapshot', () => {
        // Create mock state object
        createMockContext('target_node', 'Bedroom');

        // Render App, confirm matches snapshot
        const app = render(<App />);
        expect(app).toMatchSnapshot();
    });
});
