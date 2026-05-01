// tests/filterHelpers.test.js

const { filterGraph } = require('../src/filterHelpers');

describe('filterGraph', () => {
    const nodes = [
        { id: 'node1' },
        { id: 'node2' },
        { id: 'node3' },
        { id: 'node4' }
    ];

    const links = [
        { source: 'node1', target: 'node2', sourcetype: 'typeA' },
        { source: { id: 'node2' }, target: { id: 'node3' }, sourcetype: 'typeB' }, // simulate D3 mutated link
        { source: 'node3', target: 'node4', sourcetype: 'typeA' }
    ];

    test('returns original arrays if sourcetype is not provided or is "All"', () => {
        let result = filterGraph(nodes, links, null);
        expect(result.filteredNodes).toEqual(nodes);
        expect(result.filteredLinks).toEqual(links);

        result = filterGraph(nodes, links, 'All');
        expect(result.filteredNodes).toEqual(nodes);
        expect(result.filteredLinks).toEqual(links);
    });

    test('filters graph correctly for a specific sourcetype', () => {
        const result = filterGraph(nodes, links, 'typeA');

        expect(result.filteredLinks).toHaveLength(2);
        expect(result.filteredLinks[0].sourcetype).toBe('typeA');
        expect(result.filteredLinks[1].sourcetype).toBe('typeA');

        // Should include node1, node2, node3, node4 (all are involved in typeA links)
        expect(result.filteredNodes).toHaveLength(4);
    });

    test('filters graph correctly for a different sourcetype with D3 objects', () => {
        const result = filterGraph(nodes, links, 'typeB');

        expect(result.filteredLinks).toHaveLength(1);
        expect(result.filteredLinks[0].sourcetype).toBe('typeB');

        // Should include only node2 and node3
        expect(result.filteredNodes).toHaveLength(2);
        expect(result.filteredNodes.map(n => n.id)).toEqual(expect.arrayContaining(['node2', 'node3']));
    });

    test('returns empty arrays if sourcetype does not match any link', () => {
        const result = filterGraph(nodes, links, 'typeC');

        expect(result.filteredLinks).toHaveLength(0);
        expect(result.filteredNodes).toHaveLength(0);
    });
});
