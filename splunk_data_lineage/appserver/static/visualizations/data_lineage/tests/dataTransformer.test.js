const { formatData } = require('../src/dataTransformer');

describe('dataTransformer', () => {
    it('returns null for empty or invalid data', () => {
        expect(formatData(null)).toBeNull();
        expect(formatData({})).toBeNull();
        expect(formatData({ rows: [] })).toBeNull();
    });

    it('successfully parses an Edge List into nodes and links', () => {
        const responseData = {
            rows: [
                ['uf_server_1', 'hf_server_1', '10.5', '0', 'syslog'],
                ['hf_server_1', 'idx_server_1', '10.5', '0', 'syslog']
            ]
        };

        const result = formatData(responseData);
        
        expect(result.nodes).toHaveLength(3);
        expect(result.nodes).toEqual(expect.arrayContaining([
            expect.objectContaining({ id: 'uf_server_1', type: 'UF', eps: 10.5 }),
            expect.objectContaining({ id: 'hf_server_1', type: 'HF', eps: 10.5 }),
            expect.objectContaining({ id: 'idx_server_1', type: 'IDX', eps: 10.5 })
        ]));

        expect(result.links).toHaveLength(2);
        expect(result.links[0]).toEqual({
            source: 'uf_server_1',
            target: 'hf_server_1',
            eps: 10.5,
            lossRatio: 0,
            label: 'syslog'
        });
    });

    it('correctly parses Loss Ratio and handles missing label', () => {
         const responseData = {
            rows: [
                ['uf_server_2', 'idx_server_1', '0.05', '0.95', null]
            ]
        };
        const result = formatData(responseData);
        expect(result.links[0].lossRatio).toBe(0.95);
        expect(result.links[0].label).toBe('');
    });
});
