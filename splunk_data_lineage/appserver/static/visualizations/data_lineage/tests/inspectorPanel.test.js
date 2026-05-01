/**
 * @jest-environment jsdom
 */
// tests/inspectorPanel.test.js

const inspectorPanel = require('../src/inspectorPanel');

describe('inspectorPanel', () => {
    let container;

    beforeEach(() => {
        // Set up a DOM element as a render target
        document.body.innerHTML = '';
        container = document.createElement('div');
        container.id = 'visualization-container';
        document.body.appendChild(container);
    });

    test('renders node details and constructs correct search URL', () => {
        const nodeData = {
            id: 'host-a',
            type: 'UF',
            eps: 15.5,
            lossRatio: 0.1
        };

        inspectorPanel.render(container, nodeData, 'node');

        const panel = container.querySelector('#inspector-panel');
        expect(panel).not.toBeNull();
        expect(panel.style.display).toBe('block');

        // Check properties
        expect(panel.querySelector('.prop-id').textContent).toBe('host-a');
        expect(panel.querySelector('.prop-type').textContent).toBe('UF');
        expect(panel.querySelector('.prop-eps').textContent).toBe('15.50');
        expect(panel.querySelector('.prop-loss').textContent).toBe('10.0%');

        // Check search URL
        const searchLink = panel.querySelector('.search-link');
        const expectedUrl = 'search?q=search%20' + encodeURIComponent('host="host-a"');
        expect(searchLink.getAttribute('href')).toBe(expectedUrl);
    });

    test('renders edge details and constructs correct search URL', () => {
        const linkData = {
            source: { id: 'host-a' },
            target: { id: 'host-b' },
            eps: 12.0,
            lossRatio: 0.05,
            label: 'Network'
        };

        inspectorPanel.render(container, linkData, 'link');

        const panel = container.querySelector('#inspector-panel');
        expect(panel).not.toBeNull();
        expect(panel.style.display).toBe('block');

        // Check properties
        expect(panel.querySelector('.prop-source').textContent).toBe('host-a');
        expect(panel.querySelector('.prop-target').textContent).toBe('host-b');
        expect(panel.querySelector('.prop-eps').textContent).toBe('12.00');
        expect(panel.querySelector('.prop-loss').textContent).toBe('5.0%');
        expect(panel.querySelector('.prop-label').textContent).toBe('Network');

        // Check search URL
        const searchLink = panel.querySelector('.search-link');
        const expectedUrl = 'search?q=search%20' + encodeURIComponent('host="host-a" OR host="host-b"');
        expect(searchLink.getAttribute('href')).toBe(expectedUrl);
    });

    test('hides the panel when close button is clicked', () => {
        const nodeData = { id: 'host-a', type: 'UF', eps: 15.5, lossRatio: 0.1 };
        inspectorPanel.render(container, nodeData, 'node');

        const panel = container.querySelector('#inspector-panel');
        const closeBtn = panel.querySelector('.inspector-close');
        
        closeBtn.click();
        expect(panel.style.display).toBe('none');
    });

    test('hide() function hides the panel', () => {
        const nodeData = { id: 'host-a', type: 'UF', eps: 15.5, lossRatio: 0.1 };
        inspectorPanel.render(container, nodeData, 'node');

        const panel = container.querySelector('#inspector-panel');
        expect(panel.style.display).toBe('block');

        inspectorPanel.hide(container);
        expect(panel.style.display).toBe('none');
    });
});
