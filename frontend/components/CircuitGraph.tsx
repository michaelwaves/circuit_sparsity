'use client';

import React, { useMemo, useCallback } from 'react';
import CytoscapeComponent from 'react-cytoscapejs';
import { CircuitNode, CircuitEdge } from '@/lib/types';

interface CircuitGraphProps {
  nodes: CircuitNode[];
  edges: CircuitEdge[];
  selectedNodeId: number | null;
  onNodeSelect: (nodeId: number | null) => void;
  edgeThreshold?: number;
}

export function CircuitGraph({
  nodes,
  edges,
  selectedNodeId,
  onNodeSelect,
  edgeThreshold = 0.05,
}: CircuitGraphProps) {
  // Convert nodes and edges to Cytoscape format
  const cytoscapeElements = useMemo(() => {
    const elements: any[] = [];

    // Find max importance for scaling
    const maxImportance = Math.max(...nodes.map((n) => n.importance), 1);

    // Add nodes
    nodes.forEach((node) => {
      const layer = node.location.split('.')[0];
      const layerNum = layer === 'final_resid' ? 13 : parseInt(layer);

      elements.push({
        data: {
          id: `node-${node.node_id}`,
          label: `${node.location}\n${node.neuron_idx}`,
          importance: node.importance,
          location: node.location,
          layer: node.layer,
          component: node.component,
          subloc: node.subloc,
          neuron_idx: node.neuron_idx,
        },
        position: {
          x: layerNum * 150,
          y: nodes.indexOf(node) * 30 - (nodes.length * 15),
        },
      });
    });

    // Filter and add edges
    const filteredEdges = edges.filter((e) => Math.abs(e.weight) > edgeThreshold);
    const maxEdgeWeight = Math.max(...filteredEdges.map((e) => Math.abs(e.weight)), 1);

    filteredEdges.forEach((edge) => {
      elements.push({
        data: {
          id: `edge-${edge.edge_id}`,
          source: `node-${edge.source_node_id}`,
          target: `node-${edge.target_node_id}`,
          weight: edge.weight,
          normalizedWeight: Math.abs(edge.weight) / maxEdgeWeight,
        },
      });
    });

    return elements;
  }, [nodes, edges, edgeThreshold]);

  const stylesheet = [
    {
      selector: 'node',
      style: {
        'background-color': (ele: any) => {
          const importance = ele.data('importance');
          const hue = (1 - importance) * 240; // Blue (low) to Red (high)
          return `hsl(${hue}, 70%, 50%)`;
        },
        'border-width': (ele: any) => (ele.id() === `node-${selectedNodeId}` ? 3 : 1),
        'border-color': '#000',
        width: (ele: any) => 20 + ele.data('importance') * 30,
        height: (ele: any) => 20 + ele.data('importance') * 30,
        'font-size': 10,
        'text-halign': 'center',
        'text-valign': 'center',
        label: (ele: any) => `${ele.data('location')}`,
        'text-wrap': 'wrap',
        'text-max-width': '80px',
        padding: 5,
      },
    },
    {
      selector: 'edge',
      style: {
        'line-color': (ele: any) =>
          ele.data('weight') > 0 ? 'rgba(100, 150, 255, 0.4)' : 'rgba(255, 100, 100, 0.4)',
        'target-arrow-color': (ele: any) =>
          ele.data('weight') > 0 ? 'rgba(100, 150, 255, 0.4)' : 'rgba(255, 100, 100, 0.4)',
        'target-arrow-shape': 'triangle',
        width: (ele: any) => 1 + ele.data('normalizedWeight') * 4,
        'curve-style': 'bezier',
      },
    },
    {
      selector: 'node:selected',
      style: {
        'border-width': 3,
        'border-color': '#000',
      },
    },
  ];

  const layout = {
    name: 'grid',
    rows: Math.ceil(Math.sqrt(nodes.length)),
    cols: Math.ceil(nodes.length / Math.ceil(Math.sqrt(nodes.length))),
  };

  const handleNodeSelect = useCallback(
    (event: any) => {
      if (event.target.isNode && event.target.isNode()) {
        const nodeId = parseInt(event.target.data('id').split('-')[1]);
        onNodeSelect(nodeId);
      }
    },
    [onNodeSelect]
  );

  return (
    <div className="w-full h-full bg-white rounded-lg shadow-sm border border-gray-200">
      <CytoscapeComponent
        elements={cytoscapeElements}
        style={{ width: '100%', height: '100%', minHeight: '600px' }}
        stylesheet={stylesheet}
        layout={layout}
        cy={(cy) => {
          cy.on('tap', handleNodeSelect);
          cy.userPanningEnabled(true);
          cy.userZoomingEnabled(true);
          cy.boxSelectionEnabled(false);
          cy.autounselectify(false);
        }}
      />
    </div>
  );
}
