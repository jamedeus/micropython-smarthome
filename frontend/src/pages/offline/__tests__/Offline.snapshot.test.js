import React from 'react';
import App from '../Offline';

describe('Offline', () => {
    it('matches snapshot', () => {
        // Render App, confirm matches snapshot
        const app = render(<App />);
        expect(app).toMatchSnapshot();
    });
});
