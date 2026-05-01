## Parent

PRD: `PRD.md`

## What to build

Add visual weighting to the base graph by tying the Edge List metrics to the D3 rendering logic. The thickness of the links should scale dynamically based on the `events_per_sec` (EPS), and nodes should be conditionally colored based on the `loss_ratio` threshold to flag potential "vanishing" data. This adds critical monitoring context to the basic topology map.

## Acceptance criteria

- [ ] D3 link thickness is proportional to the EPS value provided in the Edge List.
- [ ] Nodes exceeding the Loss Ratio mock threshold (e.g., > 0) are highlighted with a distinct color (e.g., purple/red).
- [ ] Automated tests verify the styling functions correctly interpret the EPS and Loss Ratio values from the mock data payload.

## Blocked by

- Issue 01: Basic Lineage Topology
