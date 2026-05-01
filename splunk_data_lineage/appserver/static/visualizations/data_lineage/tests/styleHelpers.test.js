const { getLinkThickness, getNodeColor } = require('../src/styleHelpers');

describe('styleHelpers', () => {
    describe('getLinkThickness', () => {
        it('returns proportional thickness based on eps', () => {
            expect(getLinkThickness(10)).toBe(1); // log10(10) = 1
            expect(getLinkThickness(100)).toBe(2); // log10(100) = 2
            expect(getLinkThickness(1000)).toBe(3); // log10(1000) = 3
        });

        it('defaults to 1 if eps is small or falsy', () => {
            expect(getLinkThickness(0)).toBe(1);
            expect(getLinkThickness(null)).toBe(1);
        });
    });

    describe('getNodeColor', () => {
        it('returns distinct crimson color if lossRatio > 0', () => {
            expect(getNodeColor('UF', 0.95)).toBe('#dc143c');
            expect(getNodeColor('HF', 0.1)).toBe('#dc143c');
        });

        it('returns default tier colors when there is no loss', () => {
            expect(getNodeColor('UF', 0)).toBe('#1e90ff');
            expect(getNodeColor('HF', 0)).toBe('#ff8c00');
            expect(getNodeColor('IDX', 0)).toBe('#32cd32');
            expect(getNodeColor('UNKNOWN', 0)).toBe('#cccccc');
        });
    });
});
