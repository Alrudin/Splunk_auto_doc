# Splunk Data Lineage Visualizer: Project Overview

This document outlines the modular development plan for an application that maps Splunk data flow using the `_internal` index.

---

## 1. Task Sequence & Implementation Map

| Sequence | Task ID | Description | Concurrency Notes |
| :--- | :--- | :--- | :--- |
| **1** | 1.1 | **Multi-Tier Relationship Mapping**: Link `tcpin` to `per_sourcetype` stats to define edges. | Baseline - Required first. |
| **2** | 1.2 | **Throughput & Loss Metrics**: Calculate `kbps` and detect "vanishing" data (Loss Ratio). | Can start after 1.1 schema is set. |
| **3** | 2.1 | **Force-Directed Viz**: Build the D3.js component with hierarchical flow. | **Concurrent** with Task 1.2. |
| **4** | 2.2 | **Intelligent Aggregation**: Create the UF collapse logic (Threshold = 10). | Requires 2.1 UI to be functional. |
| **5** | 3.1 | **Contextual Filtering**: Implement Sourcetype/Index global filters. | Requires 1.1 & 2.1. |
| **6** | 3.2 | **Inspector Panel**: Detail view for node/edge drill-downs. | Final Polish. |

---

## 2. Core Feature Specifications

### Task 1.1 & 1.2: The Data Engine
* **Source**: `index=_internal sourcetype=splunkd`
* **Groups**: `tcpin_connections`, `tcpout_connections`, `per_sourcetype_stats`.
* **Logic**: 
    * Identify "Data Sinks" where Ingress >> Egress.
    * Pathing: `UF -> HF -> IDX`.

### Task 2.1 & 2.2: Visualization (The Picture)
* **Heatmap Edges**: Color gradient based on volume.
* **UF Aggregation**: 
    * If `distinct_count(UF) > 10`: Show "Top 10 UFs by Volume" and group the rest.
    * If `distinct_count(UF) <= 10`: Show individual host nodes.
* **Vanishing Alert**: Highlight nodes where a sourcetype enters but does not exit (Purple/Dashed lines).

### Task 3.1: Selective Lineage
* Enable a "Focus Mode" where selecting a single `sourcetype` isolates its specific path through the infrastructure, highlighting exactly which HFs and Indexers handle that specific data.

---

## 3. Reference Material
* [Splunk Docs: metrics.log](https://docs.splunk.com/Documentation/Splunk/latest/Troubleshooting/Aboutmetrics.log)
* [D3.js Force Gallery](https://observablehq.com/@d3/force-directed-graph)
