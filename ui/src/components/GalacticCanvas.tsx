import { useRef, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Plus } from 'lucide-react';
import type { GoalNode } from '@/types';

interface GalacticCanvasProps {
  nodes: GoalNode[];
  onPivot: (id: string) => void;
}

export default function GalacticCanvas({ nodes, onPivot }: GalacticCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  return (
    <div ref={containerRef} className="flex-1 relative bg-black overflow-hidden cursor-crosshair">
      {/* Background Grid */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: 'radial-gradient(#1A1A1A 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      {/* SVG Data Filaments */}
      <svg className="w-full h-full absolute inset-0 pointer-events-none">
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>
        {nodes.map((node) =>
          node.connections.map((targetId) => {
            const target = nodes.find((n) => n.id === targetId);
            if (!target) return null;

            let strokeColor = '#00F0FF';
            let opacity = 0.4;
            let dashArray = '0';

            if (node.isPivot) {
              strokeColor = '#8B5CF6';
            } else if (node.status === 'approval') {
              strokeColor = '#FFB800';
              dashArray = '4 4';
            } else if (node.status === 'done') {
              strokeColor = '#00F0FF';
              opacity = 0.8;
            }

            return (
              <motion.line
                key={`${node.id}-${targetId}`}
                x1={node.x}
                y1={node.y}
                x2={target.x}
                y2={target.y}
                stroke={strokeColor}
                strokeWidth={1}
                strokeOpacity={opacity}
                initial={{ pathLength: 0 }}
                animate={{
                  pathLength: 1,
                  strokeDasharray: dashArray,
                }}
                style={{ filter: node.status === 'approval' ? 'url(#glow)' : 'none' }}
              />
            );
          }),
        )}
      </svg>

      {/* Top HUD */}
      <div className="absolute top-6 left-8 flex gap-8 items-start z-20">
        <div>
          <span className="text-[9px] uppercase tracking-[0.1em] text-[#444] block mb-1">
            Pipeline
          </span>
          <span className="text-xl font-light text-white uppercase tracking-tighter">
            Agency V3
          </span>
        </div>
        <div className="w-[1px] h-10 bg-[#1A1A1A]"></div>
        <div>
          <span className="text-[9px] uppercase tracking-[0.1em] text-[#444] block mb-1">
            Persona
          </span>
          <span className="text-xl font-light text-white uppercase tracking-tighter">
            Silicon Labor
          </span>
        </div>
      </div>

      {/* Nodes */}
      {nodes.map((node) => (
        <motion.div
          key={node.id}
          className="absolute"
          style={{ left: node.x, top: node.y }}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          onMouseEnter={() => setHoveredNode(node.id)}
          onMouseLeave={() => setHoveredNode(null)}
        >
          <div className="relative -translate-x-1/2 -translate-y-1/2 group">
            {/* Approval Pulse */}
            {node.status === 'approval' && (
              <div
                className="absolute inset-0 rounded-full bg-[#FFB800]/20 animate-ping"
                style={{ width: node.radius * 2, height: node.radius * 2 }}
              />
            )}

            {/* Core Node */}
            <motion.div
              className="rounded-full border flex flex-col items-center justify-center p-2 text-center transition-all duration-500 bg-[#0A0A0A] shadow-[0_0_20px_rgba(0,0,0,0.5)]"
              style={{
                width: node.radius * 1.5,
                height: node.radius * 1.5,
                borderColor: node.isPivot
                  ? '#8B5CF6'
                  : node.status === 'approval'
                    ? '#FFB800'
                    : node.status === 'done'
                      ? '#00F0FF'
                      : '#1A1A1A',
                boxShadow:
                  node.status === 'approval'
                    ? '0 0 20px rgba(255, 184, 0, 0.3)'
                    : node.status === 'done'
                      ? '0 0 15px rgba(0, 240, 255, 0.3)'
                      : 'none',
              }}
              whileHover={{ scale: 1.1 }}
            >
              <div
                className={`w-2 h-2 rounded-full mb-2 ${
                  node.status === 'done'
                    ? 'bg-[#00F0FF]'
                    : node.status === 'approval'
                      ? 'bg-[#FFB800]'
                      : node.status === 'generation'
                        ? 'bg-[#8B5CF6]'
                        : 'bg-[#1A1A1A]'
                } ${node.status === 'research' || node.status === 'generation' ? 'animate-pulse' : ''}`}
              />
              <span
                className={`text-[10px] font-mono tracking-widest uppercase select-none ${
                  node.status === 'approval'
                    ? 'text-[#FFB800]'
                    : node.status === 'done'
                      ? 'text-[#00F0FF]'
                      : node.status === 'research' || node.status === 'generation'
                        ? 'text-white/60'
                        : 'text-[#444]'
                }`}
              >
                {node.status === 'approval'
                  ? 'HITL'
                  : node.status === 'done'
                    ? 'Done'
                    : node.status === 'research'
                      ? 'Active'
                      : node.status === 'generation'
                        ? 'Gen'
                        : node.title.split(' ')[0]}
              </span>
            </motion.div>

            {/* Narrative Tooltip Card */}
            <AnimatePresence>
              {hoveredNode === node.id && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="absolute top-20 left-1/2 -translate-x-1/2 w-64 bg-[#0A0A0A] border border-[#1A1A1A] p-4 z-50 shadow-2xl rounded-sm pointer-events-none"
                >
                  <h4
                    className={`text-[10px] uppercase font-bold mb-1.5 tracking-widest ${
                      node.status === 'approval' ? 'text-[#FFB800]' : 'text-[#00F0FF]'
                    }`}
                  >
                    {node.title}
                  </h4>
                  <p className="text-[9px] font-mono text-[#444] mb-2 uppercase">{node.kpi}</p>
                  <p className="text-[11px] text-[#A0A0A0] leading-snug">{node.summary}</p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      ))}

      {/* Strategic Pivot Tool */}
      <div className="absolute bottom-20 right-12 flex items-center gap-4 z-30">
        <span className="text-[10px] text-[#444] font-mono italic uppercase tracking-wider">
          Strategic Pivot Tool
        </span>
        <motion.div
          drag
          dragConstraints={containerRef}
          onDragEnd={(_, info) => {
            nodes.forEach((node) => {
              const dist = Math.sqrt(
                Math.pow(info.point.x - node.x, 2) + Math.pow(info.point.y - node.y, 2),
              );
              if (dist < 100) {
                onPivot(node.id);
              }
            });
          }}
          className="w-10 h-10 bg-white rounded-full flex items-center justify-center cursor-move shadow-lg"
        >
          <Plus size={20} color="black" strokeWidth={2.5} />
        </motion.div>
      </div>

      {/* Temporal Layer (Bottom Bar) */}
      <div className="absolute bottom-0 w-full h-12 bg-[#0A0A0A]/80 backdrop-blur-md border-t border-[#1A1A1A] flex items-center px-8 z-20">
        <div className="flex-1 flex justify-between">
          {['CRE', 'CRT', 'IMG', 'HITL', 'PUB'].map((d, i) => (
            <span
              key={d}
              className={`text-[9px] font-mono ${
                i < nodes.filter((n) => n.status === 'done').length
                  ? 'text-[#00F0FF]'
                  : 'text-[#444]'
              }`}
            >
              {d}
            </span>
          ))}
        </div>
        <div className="w-px h-6 bg-[#1A1A1A] mx-8"></div>
        <div className="text-[9px] font-mono text-[#00F0FF] tracking-widest uppercase">
          Pipeline Active
        </div>
      </div>
    </div>
  );
}
