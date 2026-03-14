import React, { useRef, useState, useCallback, useEffect, memo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Building2, User, MapPin, AlertTriangle, X, Download, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

const ForceGraph = ({ data }) => {
  const fgRef = useRef();
  const [selectedNode, setSelectedNode] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  if (!data || !data.nodes || data.nodes.length === 0) return null;

  // Transformovať edges na links (react-force-graph-2d očakáva 'links' namiesto 'edges')
  const graphData = {
    nodes: data.nodes || [],
    links: (data.edges || []).map(edge => ({
      source: edge.source,
      target: edge.target,
      type: edge.type || 'RELATED'
    }))
  };

  // Farba uzla podľa typu
  const getNodeColor = (node) => {
    if (!node || !node.type) return '#D4AF37';
    switch (node.type) {
      case 'company':
        return (node.risk_score || 0) > 5 ? '#ef4444' : '#D4AF37';
      case 'person':
        return '#60a5fa';
      case 'address':
        return '#34d399';
      case 'debt':
        return '#f87171';
      default:
        return '#D4AF37';
    }
  };

  // Veľkosť uzla podľa typu
  const getNodeSize = (node) => {
    if (!node || !node.type) return 8;
    switch (node.type) {
      case 'company':
        return 12;
      case 'person':
        return 8;
      case 'address':
        return 6;
      case 'debt':
        return 10;
      default:
        return 8;
    }
  };

  // Ikona uzla
  const getNodeIcon = (node) => {
    switch (node.type) {
      case 'company':
        return Building2;
      case 'person':
        return User;
      case 'address':
        return MapPin;
      case 'debt':
        return AlertTriangle;
      default:
        return Building2;
    }
  };

  // Farba hrany podľa typu
  const getLinkColor = (link) => {
    if (!link) return '#D4AF37';
    const linkType = link.type || 'RELATED';
    switch (linkType) {
      case 'OWNED_BY':
        return '#D4AF37';
      case 'MANAGED_BY':
        return '#60a5fa';
      case 'LOCATED_AT':
        return '#34d399';
      case 'HAS_DEBT':
        return '#ef4444';
      default:
        return '#D4AF37';
    }
  };

  // Kliknutie na uzol
  const handleNodeClick = useCallback((node) => {
    setSelectedNode(node);
    setIsModalOpen(true);
  }, []);

  // ESC key handling
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape' && isModalOpen) {
        setIsModalOpen(false);
      }
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isModalOpen]);

  // Export do PNG
  const handleExportPNG = () => {
    if (!fgRef.current) return;
    try {
      // react-force-graph-2d poskytuje canvas cez ref
      const canvas = fgRef.current.getGraphCanvas ? fgRef.current.getGraphCanvas() : document.querySelector('canvas');
      if (canvas) {
        const url = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.download = 'iluminati-graph.png';
        link.href = url;
        link.click();
      } else {
        // Fallback: screenshot celého grafu pomocou window.print alebo canvas
        const graphContainer = document.querySelector('.force-graph-container');
        if (graphContainer) {
          // Jednoduchý fallback - otvoriť print dialog
          window.print();
        } else {
          alert('Canvas sa nenašiel. Použite Print Screen (Cmd+Shift+4 / Win+Shift+S).');
        }
      }
    } catch (error) {
      console.error('Export error:', error);
      alert('Export sa nepodaril. Použite Print Screen alebo Developer Tools.');
    }
  };

  // Zoom funkcie
  const handleZoomIn = () => {
    if (fgRef.current) {
      fgRef.current.zoom(1.5, 200);
    }
  };

  const handleZoomOut = () => {
    if (fgRef.current) {
      fgRef.current.zoom(0.75, 200);
    }
  };

  const handleReset = () => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(400);
    }
  };

  return (
    <>
      <div className="relative border border-brand-border rounded bg-brand-navy shadow-sm overflow-hidden mt-6 force-graph-container">
        {/* Toolbar */}
        <div className="absolute top-4 right-4 z-10 flex gap-2">
          <button
            onClick={handleZoomIn}
            className="p-2 bg-brand-navy border border-brand-border rounded text-brand-slate hover:text-brand-gold hover:border-brand-gold transition-all"
            title="Priblížiť"
          >
            <ZoomIn size={16} />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-2 bg-brand-navy border border-brand-border rounded text-brand-slate hover:text-brand-gold hover:border-brand-gold transition-all"
          >
            <ZoomOut size={16} />
          </button>
          <button
            onClick={handleReset}
            className="p-2 bg-brand-navy border border-brand-border rounded text-brand-slate hover:text-brand-gold hover:border-brand-gold transition-all"
          >
            <RotateCcw size={16} />
          </button>
          <button
            onClick={handleExportPNG}
            className="p-2 bg-brand-navy border border-brand-border rounded text-brand-slate hover:text-brand-gold hover:border-brand-gold transition-all"
          >
            <Download size={16} />
          </button>
        </div>

        {/* Graph */}
        <ForceGraph2D
          ref={fgRef}
          graphData={graphData}
          nodeLabel={(node) => `${node.label || node.id}`}
          nodeColor={getNodeColor}
          nodeVal={getNodeSize}
          nodeRelSize={6}
          linkColor={(link) => getLinkColor(link)}
          linkWidth={1.5}
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          linkCurvature={0.2}
          onNodeClick={handleNodeClick}
          onNodeHover={(node) => {
            document.body.style.cursor = node ? 'pointer' : 'default';
          }}
          cooldownTicks={100}
          onEngineStop={() => {
            if (fgRef.current) fgRef.current.zoomToFit(400);
          }}
          backgroundColor="transparent"
          width={800}
          height={600}
        />
      </div>

      {/* Modal s detailom uzla - Enterprise Style */}
      {isModalOpen && selectedNode && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center bg-brand-navy/90 backdrop-blur-sm"
          onClick={() => setIsModalOpen(false)}
        >
          <div 
            className="bg-brand-navy border border-brand-border rounded p-8 max-w-md w-full mx-4 shadow-xl relative"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-6 right-6 p-2 text-brand-slate hover:text-brand-white transition-all"
            >
              <X size={20} />
            </button>

            <div className="flex items-start gap-4 mb-6">
              <div
                className="p-4 rounded border"
                style={{
                  backgroundColor: `${getNodeColor(selectedNode)}10`,
                  borderColor: `${getNodeColor(selectedNode)}30`,
                }}
              >
                {React.createElement(getNodeIcon(selectedNode), {
                  size: 24,
                  className: 'text-brand-gold',
                })}
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-brand-white mb-1 tracking-tight">
                  {selectedNode.label}
                </h3>
                <div className="flex gap-2 items-center">
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-brand-slate text-[10px] font-bold uppercase tracking-wider">
                    {selectedNode.type}
                  </span>
                  {selectedNode.country && (
                    <span className="px-2 py-0.5 rounded bg-blue-900/20 text-blue-400 text-[10px] font-bold tracking-wider">
                      {selectedNode.country}
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-4 pt-4 border-t border-brand-border">
              {selectedNode.details && (
                <div>
                  <p className="text-[10px] uppercase font-bold text-brand-slate mb-1">Popis:</p>
                  <p className="text-sm text-brand-white/80 leading-relaxed">{selectedNode.details}</p>
                </div>
              )}

              {selectedNode.ico && (
                <div>
                  <p className="text-[10px] uppercase font-bold text-brand-slate mb-1">Identifikátor (IČO):</p>
                  <p className="text-sm font-mono text-brand-white">{selectedNode.ico}</p>
                </div>
              )}

              {selectedNode.risk_score !== undefined && selectedNode.risk_score > 0 && (
                <div>
                  <p className="text-[10px] uppercase font-bold text-brand-slate mb-1">Analýza rizika:</p>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 bg-slate-800 rounded-full h-1.5">
                      <div
                        className="h-1.5 rounded-full"
                        style={{
                          width: `${(selectedNode.risk_score / 10) * 100}%`,
                          backgroundColor: selectedNode.risk_score > 5 ? '#ef4444' : '#fbbf24',
                        }}
                      />
                    </div>
                    <span className="text-xs font-bold text-brand-white">{selectedNode.risk_score}/10</span>
                  </div>
                </div>
              )}
            </div>

            <div className="mt-8 text-[10px] text-brand-slate text-center uppercase tracking-widest">
              V4-Finstat Intelligence Report
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// Memoize component pre performance
export default memo(ForceGraph, (prevProps, nextProps) => {
  // Custom comparison - re-render len ak sa zmenili dáta
  return (
    prevProps.data === nextProps.data &&
    prevProps.width === nextProps.width &&
    prevProps.height === nextProps.height
  );
});

