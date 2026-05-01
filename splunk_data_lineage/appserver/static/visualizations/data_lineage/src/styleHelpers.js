// src/styleHelpers.js

function getLinkThickness(eps) {
    return Math.max(1, Math.log10(eps || 10));
}

function getNodeColor(type, lossRatio) {
    if (lossRatio > 0) {
        return '#dc143c'; // Crimson red for loss
    }
    
    switch(type) {
        case 'UF': return '#1e90ff';
        case 'HF': return '#ff8c00';
        case 'IDX': return '#32cd32';
        default: return '#cccccc';
    }
}

module.exports = {
    getLinkThickness,
    getNodeColor
};
