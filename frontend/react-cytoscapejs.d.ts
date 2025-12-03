declare module 'react-cytoscapejs' {
  import { FC, ReactNode } from 'react';

  export interface CytoscapeComponentProps {
    elements?: any[];
    style?: React.CSSProperties;
    stylesheet?: any[];
    layout?: any;
    cy?: (cy: any) => void;
    pan?: { x: number; y: number };
    zoom?: number;
    panningEnabled?: boolean;
    userPanningEnabled?: boolean;
    minZoom?: number;
    maxZoom?: number;
    zoomingEnabled?: boolean;
    userZoomingEnabled?: boolean;
    boxSelectionEnabled?: boolean;
    autoungrabify?: boolean;
    autolock?: boolean;
    autounselectify?: boolean;
    id?: string;
    className?: string;
    [key: string]: any;
  }

  const CytoscapeComponent: FC<CytoscapeComponentProps>;

  export default CytoscapeComponent;
}
