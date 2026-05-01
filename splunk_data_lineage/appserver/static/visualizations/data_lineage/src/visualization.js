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
    const dataTransformer = require('./dataTransformer');
    const styleHelpers = require('./styleHelpers');
    const inspectorPanel = require('./inspectorPanel');

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
            return dataTransformer.formatData(responseData);
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
                .force('charge', d3.forceManyBody().strength(-800))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collide', d3.forceCollide().radius(60).iterations(3))
                .force('x', d3.forceX().strength(0.05))
                .force('y', d3.forceY().strength(0.05));

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
                .attr('stroke-width', d => styleHelpers.getLinkThickness(d.eps))
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
                .attr('fill', d => styleHelpers.getNodeColor(d.type, d.lossRatio))
                .call(d3.drag()
                    .on('start', dragstarted)
                    .on('drag', dragged)
                    .on('end', dragended))
                .on('click', (event, d) => this._drilldown(d, 'node'));

            const label = this.svg.append('g')
                .selectAll('text')
                .data(data.nodes)
                .enter().append('text')
                .attr('dy', 35)
                .style('font-size', '14px')
                .style('font-weight', 'bold')
                .style('fill', '#fff')
                .style('text-anchor', 'middle')
                .style('stroke', '#000')
                .style('stroke-width', '3px')
                .style('paint-order', 'stroke')
                .text(d => d.id);

            simulation.on('tick', () => {
                data.nodes.forEach(d => {
                    if (d.type === 'UF') d.y = Math.max(20, Math.min(height * 0.2, d.y));
                    else if (d.type === 'HF') d.y = height * 0.5;
                    else d.y = Math.max(height * 0.8, Math.min(height - 20, d.y));
                    d.x = Math.max(20, Math.min(width - 20, d.x));
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
            inspectorPanel.render(this.el, d, type);
        }
    });
});
