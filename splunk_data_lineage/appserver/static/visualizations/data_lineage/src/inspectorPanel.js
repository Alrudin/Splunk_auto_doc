// src/inspectorPanel.js

function render(container, data, type) {
    let panel = container.querySelector('#inspector-panel');
    if (!panel) {
        panel = document.createElement('div');
        panel.id = 'inspector-panel';
        panel.style.position = 'absolute';
        panel.style.top = '10px';
        panel.style.right = '10px';
        panel.style.width = '250px';
        panel.style.backgroundColor = 'rgba(30, 30, 30, 0.9)';
        panel.style.color = '#fff';
        panel.style.border = '1px solid #444';
        panel.style.borderRadius = '4px';
        panel.style.padding = '15px';
        panel.style.fontFamily = 'sans-serif';
        panel.style.boxShadow = '0 4px 6px rgba(0,0,0,0.3)';
        panel.style.zIndex = '1000';
        container.appendChild(panel);
        container.style.position = 'relative'; // Ensure relative positioning for absolute child
    }

    panel.style.display = 'block';

    let html = '<div class="inspector-close" style="position:absolute; top:10px; right:10px; cursor:pointer; font-size:16px; color:#ccc;">&times;</div>';
    
    let searchUrl = 'search?q=search%20';

    if (type === 'node') {
        html += '<h3 style="margin-top:0; font-size:16px; border-bottom:1px solid #555; padding-bottom:5px;">Node Inspector</h3>';
        html += '<p><strong>ID:</strong> <span class="prop-id">' + data.id + '</span></p>';
        html += '<p><strong>Type:</strong> <span class="prop-type">' + data.type + '</span></p>';
        html += '<p><strong>EPS:</strong> <span class="prop-eps">' + (data.eps || 0).toFixed(2) + '</span></p>';
        html += '<p><strong>Loss:</strong> <span class="prop-loss">' + ((data.lossRatio || 0) * 100).toFixed(1) + '%</span></p>';
        
        searchUrl += encodeURIComponent(`host="${data.id}"`);
    } else if (type === 'link') {
        html += '<h3 style="margin-top:0; font-size:16px; border-bottom:1px solid #555; padding-bottom:5px;">Edge Inspector</h3>';
        html += '<p><strong>Source:</strong> <span class="prop-source">' + data.source.id + '</span></p>';
        html += '<p><strong>Target:</strong> <span class="prop-target">' + data.target.id + '</span></p>';
        html += '<p><strong>EPS:</strong> <span class="prop-eps">' + (data.eps || 0).toFixed(2) + '</span></p>';
        html += '<p><strong>Loss:</strong> <span class="prop-loss">' + ((data.lossRatio || 0) * 100).toFixed(1) + '%</span></p>';
        if (data.label) {
            html += '<p><strong>Label:</strong> <span class="prop-label">' + data.label + '</span></p>';
        }
        
        searchUrl += encodeURIComponent(`host="${data.source.id}" OR host="${data.target.id}"`);
    }

    html += '<a class="search-link" href="' + searchUrl + '" target="_blank" style="display:inline-block; margin-top:10px; padding:6px 12px; background:#0073e6; color:white; text-decoration:none; border-radius:3px; font-size:12px;">Open in Search <span style="font-size: 10px;">&#x2197;</span></a>';

    panel.innerHTML = html;

    panel.querySelector('.inspector-close').addEventListener('click', function() {
        panel.style.display = 'none';
    });
}

function hide(container) {
    const panel = container.querySelector('#inspector-panel');
    if (panel) {
        panel.style.display = 'none';
    }
}

module.exports = { render, hide };
