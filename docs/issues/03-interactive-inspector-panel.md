## Parent

PRD: `PRD.md`

## What to build

Implement the Inspector Panel component that appears when a user clicks on a node or edge. The panel must immediately display the in-memory properties (EPS, Source, Target, Mocked Loss) bound to that specific element. It must also generate a dynamic "Open in Search" URL that deep-links into the Splunk standard search view for the targeted node. No ad-hoc backend searches should be executed on click.

## Acceptance criteria

- [ ] Clicking a node or edge opens the Inspector Panel on the side of the canvas.
- [ ] Panel populates instantly with in-memory data associated with the clicked element.
- [ ] Panel includes a functional "Open in Search" hyperlink containing the host/sourcetype parameters.
- [ ] Automated tests verify the UI component's state correctly binds to the selected node's properties.

## Blocked by

- Issue 02: Visualizing Throughput & Loss Metrics
