// src/filterHelpers.js

/**
 * Filters the graph data to include only nodes and links associated with a specific sourcetype.
 * @param {Array} nodes - Array of all nodes.
 * @param {Array} links - Array of all links.
 * @param {string} sourcetype - The sourcetype to filter by. If falsy or 'All', returns original arrays.
 * @returns {Object} { filteredNodes, filteredLinks }
 */
function filterGraph(nodes, links, sourcetype) {
    if (!sourcetype || sourcetype === 'All') {
        return { filteredNodes: nodes, filteredLinks: links };
    }

    const filteredLinks = links.filter(link => link.sourcetype === sourcetype);

    const activeNodeIds = new Set();
    filteredLinks.forEach(link => {
        // D3 might have mutated source/target to be objects
        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
        const targetId = typeof link.target === 'object' ? link.target.id : link.target;
        activeNodeIds.add(sourceId);
        activeNodeIds.add(targetId);
    });

    const filteredNodes = nodes.filter(node => activeNodeIds.has(node.id));

    return { filteredNodes, filteredLinks };
}

module.exports = { filterGraph };
