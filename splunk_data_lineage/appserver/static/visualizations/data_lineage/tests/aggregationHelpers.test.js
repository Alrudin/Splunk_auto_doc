// tests/aggregationHelpers.test.js

const { aggregateGraph } = require('../src/aggregationHelpers');

describe('aggregateGraph', () => {
    let nodes, links;

    beforeEach(() => {
        nodes = [];
        links = [];
        
        // Add 15 UF nodes
        for (let i = 1; i <= 15; i++) {
            nodes.push({ id: `uf${i}`, type: 'UF', eps: i * 10 }); // uf15 has highest eps (150)
            links.push({ source: `uf${i}`, target: 'hf1', eps: i * 10, lossRatio: 0.1 });
        }
        
        // Add 1 HF node
        nodes.push({ id: 'hf1', type: 'HF', eps: 0 });
    });

    test('bypasses aggregation if isExpanded is true', () => {
        const result = aggregateGraph(nodes, links, true);
        expect(result.aggregatedNodes).toEqual(nodes);
        expect(result.aggregatedLinks).toEqual(links);
    });

    test('bypasses aggregation if there are 10 or fewer UFs', () => {
        // Remove 5 UFs
        const smallNodes = nodes.slice(5); // 10 UFs + 1 HF
        const smallLinks = links.slice(5);
        
        const result = aggregateGraph(smallNodes, smallLinks, false);
        expect(result.aggregatedNodes).toEqual(smallNodes);
        expect(result.aggregatedLinks).toEqual(smallLinks);
    });

    test('aggregates UFs correctly when there are more than 10', () => {
        const result = aggregateGraph(nodes, links, false);
        
        // We expect 11 nodes (top 10 UFs + 1 HF + 1 Aggregated UF node) -> wait, 10 + 1 + 1 = 12 nodes total
        expect(result.aggregatedNodes).toHaveLength(12);

        // Check if top 10 are kept (uf15 down to uf6)
        const keptUfIds = result.aggregatedNodes.filter(n => n.type === 'UF' && !n.isAggregated).map(n => n.id);
        expect(keptUfIds).toHaveLength(10);
        expect(keptUfIds).toContain('uf15');
        expect(keptUfIds).toContain('uf6');
        expect(keptUfIds).not.toContain('uf5');

        // Check the aggregated node
        const aggNode = result.aggregatedNodes.find(n => n.isAggregated);
        expect(aggNode).toBeDefined();
        expect(aggNode.id).toBe('Aggregated UFs (5)');
        
        // The aggregated node should have the sum of EPS of hidden nodes (uf1..uf5 = 10+20+30+40+50 = 150)
        expect(aggNode.eps).toBe(150);

        // Check links
        // We should still have 15 links, but 5 of them now point from 'Aggregated UFs (5)'
        expect(result.aggregatedLinks).toHaveLength(15);
        const aggLinks = result.aggregatedLinks.filter(l => l.source === 'Aggregated UFs (5)');
        expect(aggLinks).toHaveLength(5);
    });
});
