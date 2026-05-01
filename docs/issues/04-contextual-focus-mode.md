## Parent

PRD: `PRD.md`

## What to build

Introduce a global "Focus Mode" dropdown filter allowing users to select a specific `sourcetype`. When a sourcetype is selected, the UI controller must completely remove all nodes and edges from the D3.js DOM/canvas that do not participate in that sourcetype's lineage path, thereby aggressively decluttering the view.

## Acceptance criteria

- [ ] A dropdown menu populated with all distinct sourcetypes available in the current dataset.
- [ ] Selecting a sourcetype completely removes non-matching nodes and edges from the visual graph.
- [ ] Clearing the filter restores the full topology instantly without querying the backend.
- [ ] Automated tests verify the filtering function correctly isolates the node/link arrays based on the target string.

## Blocked by

- Issue 01: Basic Lineage Topology
