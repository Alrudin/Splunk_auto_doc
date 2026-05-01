// src/aggregationHelpers.js

/**
 * Applies intelligent node aggregation to the Universal Forwarder tier.
 * If there are more than 10 UFs, the top 10 by EPS are kept, and the rest are aggregated into a single "Other" node.
 * @param {Array} nodes - Array of all nodes.
 * @param {Array} links - Array of all links.
 * @param {boolean} isExpanded - If true, bypasses aggregation.
 * @returns {Object} { aggregatedNodes, aggregatedLinks }
 */
function aggregateGraph(nodes, links, isExpanded) {
    if (isExpanded) {
        return { aggregatedNodes: nodes, aggregatedLinks: links };
    }

    // Identify UFs
    const ufNodes = nodes.filter(n => n.type === 'UF');

    // If 10 or fewer, no aggregation needed
    if (ufNodes.length <= 10) {
        return { aggregatedNodes: nodes, aggregatedLinks: links };
    }

    // Sort UFs by EPS descending
    ufNodes.sort((a, b) => b.eps - a.eps);

    const top10 = new Set(ufNodes.slice(0, 10).map(n => n.id));
    const otherUfId = `Aggregated UFs (${ufNodes.length - 10})`;

    // Create a new node map from the non-UF and top-10 UF nodes
    const outNodesMap = new Map();
    nodes.forEach(n => {
        if (n.type !== 'UF' || top10.has(n.id)) {
            outNodesMap.set(n.id, Object.assign({}, n));
        }
    });

    // Create the Aggregate node
    const aggregateNode = {
        id: otherUfId,
        type: 'UF',
        eps: 0,
        lossRatio: 0,
        isAggregated: true
    };
    outNodesMap.set(otherUfId, aggregateNode);

    // Process links
    const outLinks = [];
    links.forEach(l => {
        const linkObj = Object.assign({}, l);
        const sourceId = typeof linkObj.source === 'object' ? linkObj.source.id : linkObj.source;
        const targetId = typeof linkObj.target === 'object' ? linkObj.target.id : linkObj.target;

        let isSourceAggregated = false;
        let isTargetAggregated = false;

        if (!outNodesMap.has(sourceId)) {
            linkObj.source = otherUfId;
            isSourceAggregated = true;
        } else if (typeof linkObj.source === 'object') {
            linkObj.source = sourceId; // Flatten back to ID for clean re-binding
        }

        if (!outNodesMap.has(targetId)) {
            linkObj.target = otherUfId;
            isTargetAggregated = true;
        } else if (typeof linkObj.target === 'object') {
            linkObj.target = targetId;
        }

        if (isSourceAggregated || isTargetAggregated) {
            aggregateNode.eps += linkObj.eps;
            aggregateNode.lossRatio = Math.max(aggregateNode.lossRatio, linkObj.lossRatio || 0);
        }

        outLinks.push(linkObj);
    });

    return {
        aggregatedNodes: Array.from(outNodesMap.values()),
        aggregatedLinks: outLinks
    };
}

module.exports = { aggregateGraph };
