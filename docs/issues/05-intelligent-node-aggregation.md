## Parent

PRD: `PRD.md`

## What to build

Implement the client-side "Intelligent Aggregation" logic for Universal Forwarders. Before rendering the D3 nodes, the state controller should evaluate if a tier contains more than 10 UF nodes. If true, it must identify the top 10 by volume to render individually, and group the remaining nodes into a single, clickable "Other" aggregate node. This ensures the graph remains readable at scale.

## Acceptance criteria

- [ ] Logic correctly identifies if a node tier exceeds the 10-node threshold.
- [ ] Logic correctly sorts nodes by EPS volume and splices the top 10.
- [ ] Remaining nodes are visually represented as a single "Other" node.
- [ ] Clicking the "Other" node expands it, revealing the hidden tail-end nodes.
- [ ] Automated isolated tests verify the aggregation sorting and slicing math when provided an array of mock nodes.

## Blocked by

- Issue 04: Contextual Focus Mode
