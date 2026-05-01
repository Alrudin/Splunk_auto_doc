## Parent

PRD: `PRD.md`

## What to build

Wire up the refactored `stats` SPL query to a basic D3.js force-directed graph. This slice delivers the core architecture: it executes the backend query to retrieve the raw Edge List and renders all nodes and edges on the client side natively. It establishes the end-to-end data pipeline without any advanced styling, aggregation, or interactivity.

## Acceptance criteria

- [x] SPL query in backend executes and returns the flat Edge List.
- [x] Frontend successfully parses the Edge List into D3 nodes and links.
- [x] D3 force-directed graph renders on screen showing the topological lineage.
- [x] Automated tests verify the schema of the backend response and the D3 node/link transformation logic.

## Blocked by

None - can start immediately.
