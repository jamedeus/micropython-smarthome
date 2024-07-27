import React from 'react';
import RuleSlider from '../RuleSlider';

describe('RuleSlider', () => {
    it('displays max value if rule exceeds max', async () => {
        // Render component with rule exceeding maximum (eg motion sensor set
        // to 100 by CLI client or API call)
        const component = render(
            <RuleSlider
                rule={100}
                setRule={jest.fn}
                min={0}
                max={60}
                displayMin={1}
                displayMax={100}
                scaleDisplayValue={false}
            />
        );

        // Confirm slider handle shows max (60), not rule (100)
        expect(component.container.querySelector('.sliderHandle').innerHTML).toBe('60');
    });

    it('displays min value if rule exceeds min', async () => {
        // Render component with rule exceeding minimum
        const component = render(
            <RuleSlider
                rule={10}
                setRule={jest.fn}
                min={20}
                max={80}
                displayMin={1}
                displayMax={100}
                scaleDisplayValue={false}
            />
        );

        // Confirm slider handle shows min (20), not rule (10)
        expect(component.container.querySelector('.sliderHandle').innerHTML).toBe('20');
    });
});
