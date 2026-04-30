define([
    'api/SplunkVisualizationBase',
    'api/SplunkVisualizationUtils',
    'd3'
],
function(
    SplunkVisualizationBase,
    SplunkVisualizationUtils,
    d3
) {

    return SplunkVisualizationBase.extend({
        initialize: function() {
            SplunkVisualizationBase.prototype.initialize.apply(this, arguments);
            this.$el = $(this.el);
            this.svg = d3.select(this.el).append('svg')
                .attr('width', '100%')
                .attr('height', '100%');
        },

        getInitialDataParams: function() {
            return {
                outputMode: SplunkVisualizationBase.ROW_MAJOR_OUTPUT_MODE,
                count: 10000
            };
        },

        formatData: function(responseData, config) {
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

                if (!nodeMap.has(sourceId)) {
                    nodeMap.set(sourceId, { id: sourceId, type: 'UF', eps: eps });
                    nodes.push(nodeMap.get(sourceId));
                }
                if (!nodeMap.has(targetId)) {
                    nodeMap.set(targetId, { id: targetId, type: 'HF_IDX', eps: eps });
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
        },

        updateView: function(data, config) {
            if (!data) return;
            
            const width = this.$el.width() || 800;
            const height = this.$el.height() || 600;

            this.svg.selectAll('*').remove();
            
            const colorScale = d3.scaleSequential(d3.interpolateOranges)
                .domain([0, d3.max(data.links, d => d.eps) || 1]);

            const simulation = d3.forceSimulation(data.nodes)
                .force('link', d3.forceLink(data.links).id(d => d.id).distance(150))
                .force('charge', d3.forceManyBody().strength(-300))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collide', d3.forceCollide().radius(25).iterations(2))
                .force('x', d3.forceX().strength(0.1))
                .force('y', d3.forceY().strength(0.1));

            this.svg.append('defs').append('marker')
                .attr('id', 'arrow')
                .attr('viewBox', '0 -5 10 10')
                .attr('refX', 20)
                .attr('refY', 0)
                .attr('markerWidth', 6)
                .attr('markerHeight', 6)
                .attr('orient', 'auto')
                .append('path')
                .attr('d', 'M0,-5L10,0L0,5')
                .attr('fill', '#999');

            const link = this.svg.append('g')
                .attr('stroke-opacity', 0.6)
                .selectAll('line')
                .data(data.links)
                .enter().append('line')
                .attr('stroke', d => d.lossRatio > 0.9 ? 'red' : colorScale(d.eps))
                .attr('stroke-width', d => Math.max(1, Math.log10(d.eps || 10)))
                .attr('stroke-dasharray', d => d.lossRatio > 0.9 ? '5,5' : 'none')
                .attr('marker-end', 'url(#arrow)')
                .on('click', (event, d) => this._drilldown(d, 'link'));

            const edgeLabel = this.svg.append('g')
                .selectAll('text')
                .data(data.links)
                .enter().append('text')
                .attr('font-size', '10px')
                .attr('fill', '#ccc')
                .attr('text-anchor', 'middle')
                .text(d => d.label);

            const node = this.svg.append('g')
                .attr('stroke', '#fff')
                .attr('stroke-width', 1.5)
                .selectAll('circle')
                .data(data.nodes)
                .enter().append('circle')
                .attr('r', 20)
                .attr('fill', d => d.type === 'UF' ? '#1e90ff' : '#32cd32')
                .call(d3.drag()
                    .on('start', dragstarted)
                    .on('drag', dragged)
                    .on('end', dragended))
                .on('click', (event, d) => this._drilldown(d, 'node'));

            const label = this.svg.append('g')
                .selectAll('text')
                .data(data.nodes)
                .enter().append('text')
                .attr('dx', 25)
                .attr('dy', '.35em')
                .style('font-size', '12px')
                .style('fill', '#fff')
                .text(d => d.id);

            simulation.on('tick', () => {
                data.nodes.forEach(d => {
                    if (d.type === 'UF') d.x = Math.max(20, Math.min(width * 0.4, d.x));
                    else d.x = Math.max(width * 0.6, Math.min(width - 20, d.x));
                });

                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);
                    
                edgeLabel
                    .attr('x', d => (d.source.x + d.target.x) / 2)
                    .attr('y', d => (d.source.y + d.target.y) / 2 - 5);

                node
                    .attr('cx', d => d.x)
                    .attr('cy', d => d.y);
                    
                label
                    .attr('x', d => d.x)
                    .attr('y', d => d.y);
            });

            function dragstarted(event, d) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x; d.fy = d.y;
            }

            function dragged(event, d) {
                d.fx = event.x; d.fy = event.y;
            }

            function dragended(event, d) {
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null; d.fy = null;
            }
        },
        
        _drilldown: function(d, type) {
            let drilldownData = {};
            if (type === 'link') {
                drilldownData = {
                    action: SplunkVisualizationBase.FIELD_VALUE_DRILLDOWN,
                    data: {
                        'source': d.source.id,
                        'target': d.target.id,
                        'eps': String(d.eps),
                        'loss_ratio': String(d.lossRatio)
                    }
                };
            } else {
                drilldownData = {
                    action: SplunkVisualizationBase.FIELD_VALUE_DRILLDOWN,
                    data: {
                        'node': d.id,
                        'type': d.type
                    }
                };
            }
            this.drilldown(drilldownData);
        }
    });
});
