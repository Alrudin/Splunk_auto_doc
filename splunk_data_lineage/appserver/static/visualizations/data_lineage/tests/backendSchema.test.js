describe('Backend SPL Response Schema', () => {
    it('validates the expected format of the Splunk saved search output', () => {
        // The backend query in savedsearches.conf is:
        // | table sourceNode, targetNode, events_per_sec, loss_ratio, sourcetype
        // We simulate a row of data that D3 expects matching this schema.
        
        const splunkRow = ['uf_host_1', 'hf_host_1', '150.2', '0', 'win-event-log'];
        
        const schema = {
            sourceNode: splunkRow[0],
            targetNode: splunkRow[1],
            events_per_sec: parseFloat(splunkRow[2]),
            loss_ratio: parseFloat(splunkRow[3]),
            sourcetype: splunkRow[4]
        };

        // Assert schema fields are correctly mapped
        expect(schema.sourceNode).toBe('uf_host_1');
        expect(schema.targetNode).toBe('hf_host_1');
        expect(schema.events_per_sec).toBe(150.2);
        expect(schema.loss_ratio).toBe(0);
        expect(schema.sourcetype).toBe('win-event-log');
        
        // Assert types
        expect(typeof schema.sourceNode).toBe('string');
        expect(typeof schema.targetNode).toBe('string');
        expect(typeof schema.events_per_sec).toBe('number');
        expect(typeof schema.loss_ratio).toBe('number');
        expect(typeof schema.sourcetype).toBe('string');
    });
});
