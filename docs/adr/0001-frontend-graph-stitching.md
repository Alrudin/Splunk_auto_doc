# 1. Frontend Graph Stitching

Date: 2026-05-01

## Status

Accepted

## Context

We need to map the full multi-tier data lineage (UF -> HF -> IDX). Doing this purely in Splunk SPL requires `join` or complex subsearches, which are either slow, brittle, or subject to the 50,000 subsearch result limit. Returning complete multi-hop paths directly from the Splunk data engine is difficult to scale for large environments.

## Decision

We will extract a global, flat **Edge List** (single hops of `sourceNode -> targetNode`) using a single optimized `stats` command in Splunk. The D3.js visualization layer on the frontend will take this flat list and natively construct and stitch the full multi-hop directed graph.

## Consequences

* **Positive**: Bypasses the 50k `join` limit in Splunk, making the search much more scalable and performant.
* **Positive**: Simplifies the Splunk SPL search drastically.
* **Negative**: Shifts computational complexity to the client's browser (D3.js will have to process potentially thousands of edges to construct the graph).
