// src/dataTransformer.js

function formatData(responseData) {
    if (!responseData || !responseData.rows || responseData.rows.length === 0) {
        return null;
    }
    const nodes = [];
    const links = [];
    const nodeMap = new Map();

    responseData.rows.forEach(function(row) {
        const sourceId = row[0];
        const targetId = row[1];
        const eps = parseFloat(row[2]) || 0;
        const lossRatio = parseFloat(row[3]) || 0;

        let sourceType = sourceId.includes('uf') ? 'UF' : (sourceId.includes('hf') ? 'HF' : 'IDX');
        let targetType = targetId.includes('uf') ? 'UF' : (targetId.includes('hf') ? 'HF' : 'IDX');

        if (!nodeMap.has(sourceId)) {
            nodeMap.set(sourceId, { id: sourceId, type: sourceType, eps: eps, lossRatio: lossRatio });
            nodes.push(nodeMap.get(sourceId));
        } else {
            nodeMap.get(sourceId).lossRatio = Math.max(nodeMap.get(sourceId).lossRatio || 0, lossRatio);
        }
        if (!nodeMap.has(targetId)) {
            nodeMap.set(targetId, { id: targetId, type: targetType, eps: eps, lossRatio: 0 });
            nodes.push(nodeMap.get(targetId));
        }
        links.push({
            source: sourceId,
            target: targetId,
            eps: eps,
            lossRatio: lossRatio,
            label: row[4] || ''
        });
    });

    // UF Aggregation Logic
    const ufNodes = nodes.filter(n => n.type === 'UF');
    if (ufNodes.length > 10) {
        ufNodes.sort((a, b) => b.eps - a.eps);
        const top10 = new Set(ufNodes.slice(0, 10).map(n => n.id));
        const otherUfId = "Aggregated UFs (" + (ufNodes.length - 10) + ")";
        nodeMap.set(otherUfId, { id: otherUfId, type: 'UF', eps: 0 });
        nodes.push(nodeMap.get(otherUfId));

        for (let i = links.length - 1; i >= 0; i--) {
            if (nodeMap.get(links[i].source).type === 'UF' && !top10.has(links[i].source)) {
                links[i].source = otherUfId;
            }
        }
        
        for (let i = nodes.length - 1; i >= 0; i--) {
            if (nodes[i].type === 'UF' && !top10.has(nodes[i].id) && nodes[i].id !== otherUfId) {
                nodes.splice(i, 1);
            }
        }
    }

    return { nodes: nodes, links: links };
}

module.exports = { formatData };
