## Problem Statement

Splunk administrators and platform engineers lack visibility into the complex data lineage of their environment. They cannot easily visualize the path data takes from Universal Forwarders (UFs) through Heavy Forwarders (HFs) to Indexers (IDX). This makes it difficult to detect "vanishing" data, isolate routing issues by sourcetype, or understand the holistic topology of the data ingestion pipeline.

## Solution

A custom Splunk Data Lineage Visualizer application that maps the data flow using the `_internal` index. It extracts an Edge List of single-hop relationships and uses a D3.js force-directed graph to visualize the full multi-tier architecture. It provides intelligent aggregation to prevent clutter, Focus Mode to trace specific sourcetypes, and an Inspector Panel for instant metrics drill-downs.

## User Stories

1. As a Splunk administrator, I want to see a visual map of my entire data ingestion topology, so that I can understand the architectural layout of my forwarders and indexers.
2. As a platform engineer, I want the visualization to automatically stitch multi-hop paths (e.g., UF to HF to IDX) together, so that I don't have to manually trace connections across different tiers.
3. As a troubleshooter, I want to see the events-per-second (EPS) volume represented visually on the edges between nodes, so that I can quickly identify high-traffic bottlenecks.
4. As an administrator of a large environment, I want the UI to intelligently aggregate low-volume Universal Forwarders when there are more than 10 in a tier, so that the graph remains readable and uncluttered.
5. As a troubleshooter, I want to be able to expand the "Other" aggregated UF group if needed, so that I can inspect the tail-end of my forwarder fleet.
6. As a data onboarder, I want to use Focus Mode to select a specific `sourcetype`, so that the graph declutters and shows only the exact path that specific data takes through the infrastructure.
7. As a platform engineer, I want nodes and edges irrelevant to my focused sourcetype to completely disappear from the canvas, so that I have zero visual distraction during investigations.
8. As a Splunk user, I want to click on a specific node or edge to open an Inspector Panel, so that I can instantly see its EPS metrics and mocked Loss Ratio without waiting for a new search to run.
9. As a deep-dive investigator, I want the Inspector Panel to provide an "Open in Search" link, so that I can seamlessly jump into the raw `_internal` logs for a specific node if the in-memory metrics indicate a problem.
10. As a platform owner, I want the data engine to use optimized single-hop edge extractions rather than complex multi-hop joins, so that the lineage search scales reliably even in environments exceeding Splunk's 50k subsearch limits.

## Implementation Decisions

- **Data Engine Boundary**: The Splunk backend will return a flat **Edge List** (single hops of `sourceNode -> targetNode`) rather than pre-computing full multi-hop paths.
- **Client-Side Graph Stitching**: The D3.js frontend will ingest the flat Edge List and natively construct the multi-hop directed graph. (See ADR-0001).
- **Intelligent Aggregation**: Grouping of low-volume nodes (UFs > 10) is handled entirely on the client-side using the raw Edge List.
- **Focus Mode Rendering**: When a sourcetype is selected, the UI will completely remove non-matching nodes/edges from the DOM/canvas, rather than just adjusting CSS opacity.
- **Inspector Panel Data**: The panel operates strictly on in-memory data provided by the initial Edge List payload to ensure snappy, low-latency interactions. Ad-hoc Splunk searches are deferred to a separate "Open in Search" workflow.
- **Loss Ratio Mock**: The "Loss Ratio" metric is currently mocked in the SPL using a static low-EPS threshold (`events_per_sec < 0.1`). True ingress vs. egress calculation is deferred to a future iteration.

## Testing Decisions

Good tests for this application should focus on the external behavior and data contracts of the modules, rather than their internal implementation details. We will test all three major modules:

- **Data Engine (Splunk Backend)**:
  - We will write automated tests to verify the SPL query output schema (ensuring `sourceNode`, `targetNode`, `events_per_sec`, `loss_ratio`, and `sourcetype` fields are correctly formatted).
  - Tests will validate that single-hop relationships are accurately extracted from mock `_internal` data.
- **D3.js Visualization Engine**:
  - We will unit test the data transformation layer that converts the Edge List into the D3 node/link format.
  - We will write isolated tests for the **Intelligent Aggregation** logic to ensure it correctly identifies the top 10 nodes and groups the remainder when provided a mock array of UFs.
- **Interaction & State Controller**:
  - We will test the **Focus Mode** filtering function to guarantee it correctly isolates the node/link arrays based on a target sourcetype.
  - We will test the **Inspector Panel** state to ensure it correctly binds in-memory node properties to the UI component state.

## Out of Scope

- True ingress vs. egress volume delta calculations for the Loss Ratio metric.
- Real-time streaming updates to the visualization (it will rely on a scheduled summary index or ad-hoc load).
- Write access or configuration changes to the forwarders via the UI.

## Further Notes

- The domain glossary is maintained in `CONTEXT.md`. All future development should use these terms (Edge List, Loss Ratio, Intelligent Aggregation, Focus Mode, Inspector Panel).
