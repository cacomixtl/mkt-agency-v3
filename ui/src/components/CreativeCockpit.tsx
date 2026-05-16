import { useState } from 'react';
import { motion } from 'motion/react';
import type { SSEEventBreakpoint, MarketingContent, HITLDecision } from '@/types';
import BreakpointGate from './BreakpointGate';

interface CreativeCockpitProps {
  breakpoint: SSEEventBreakpoint | null;
  preview: MarketingContent | null;
  onDecision: (decision: HITLDecision, feedback?: string) => void;
}

export default function CreativeCockpit({ breakpoint, preview, onDecision }: CreativeCockpitProps) {
  const [activeTab, setActiveTab] = useState<'preview' | 'inspector'>('preview');

  return (
    <aside className="w-[340px] bg-[#0A0A0A] border-l border-[#1A1A1A] flex flex-col h-screen h-svh overflow-hidden">
      {/* Tab Header */}
      <div className="flex p-2 border-b border-[#1A1A1A] bg-black">
        <button
          id="tab-preview"
          onClick={() => setActiveTab('preview')}
          className={`flex-1 py-2 text-[10px] uppercase tracking-widest font-bold transition-all ${
            activeTab === 'preview'
              ? 'text-white border-b border-[#00F0FF]'
              : 'text-[#444] hover:text-white/50'
          }`}
        >
          Preview
        </button>
        <button
          id="tab-inspector"
          onClick={() => setActiveTab('inspector')}
          className={`flex-1 py-2 text-[10px] uppercase tracking-widest font-bold transition-all ${
            activeTab === 'inspector'
              ? 'text-white border-b border-[#00F0FF]'
              : 'text-[#444] hover:text-white/50'
          }`}
        >
          Technical
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6 flex flex-col scrollbar-none">
        {activeTab === 'preview' ? (
          <div className="w-full flex flex-col items-center space-y-6">
            {/* Breakpoint Gate (HITL Interface) */}
            {breakpoint ? (
              <BreakpointGate
                breakpoint={breakpoint}
                preview={preview}
                onDecision={onDecision}
              />
            ) : (
              <>
                {/* Ghost UI: Mobile Frame */}
                <div className="w-[240px] h-[480px] bg-black rounded-[40px] border-[6px] border-[#1A1A1A] relative flex flex-col overflow-hidden shadow-2xl">
                  <div className="h-6 w-full flex items-center justify-center">
                    <div className="w-12 h-1 bg-[#1A1A1A] rounded-full"></div>
                  </div>

                  {/* Instagram Feed Mock */}
                  <div className="flex-1 overflow-y-auto scrollbar-none">
                    <div className="p-3 flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-yellow-400 to-purple-600"></div>
                      <div className="h-2 w-20 bg-[#1A1A1A] rounded"></div>
                    </div>

                    <div className="w-full aspect-square bg-[#111] border-y border-[#1A1A1A] relative group overflow-hidden">
                      <div className="w-full h-full bg-gradient-to-br from-[#111] via-[#0A0A0A] to-[#1A1A1A] flex items-center justify-center">
                        <span className="text-[9px] font-mono text-[#333] uppercase tracking-widest">
                          Awaiting Asset
                        </span>
                      </div>
                      <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px] opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center p-4">
                        <span className="text-[8px] font-mono uppercase text-center tracking-tighter">
                          Tactical Continuity: Active
                        </span>
                      </div>
                    </div>

                    <div className="p-3 space-y-2">
                      <div className="flex gap-2">
                        <div className="w-4 h-4 bg-[#1A1A1A] rounded-full"></div>
                        <div className="w-4 h-4 bg-[#1A1A1A] rounded-full"></div>
                        <div className="w-4 h-4 bg-[#1A1A1A] rounded-full"></div>
                      </div>
                      <div className="h-2 w-full bg-[#1A1A1A] rounded"></div>
                      <div className="h-2 w-3/4 bg-[#1A1A1A] rounded"></div>
                    </div>

                    {/* Grid View */}
                    <div className="mt-4 grid grid-cols-3 gap-0.5">
                      {[...Array(6)].map((_, i) => (
                        <div
                          key={i}
                          className="aspect-square bg-[#0D0D0D] overflow-hidden"
                        >
                          <div className="w-full h-full bg-gradient-to-br from-[#111] to-[#0A0A0A]" />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                <p className="text-[10px] text-[#444] font-mono uppercase tracking-widest">
                  Director_Cockpit_V3
                </p>
              </>
            )}
          </div>
        ) : (
          /* Inspector / Technical Tab */
          <div className="w-full space-y-6 font-mono text-[10px]">
            <div className="space-y-2">
              <div className="text-[#444] tracking-widest uppercase">Metadata Analysis</div>
              <div className="p-3 bg-black border border-[#1A1A1A] rounded space-y-2 text-white/60">
                <div className="flex justify-between">
                  <span>PERSONA</span>
                  <span className="text-[#00F0FF]">Silicon Labor</span>
                </div>
                <div className="flex justify-between">
                  <span>TONE</span>
                  <span className="text-[#00F0FF]">Stoic</span>
                </div>
                <div className="flex justify-between">
                  <span>VISUAL_MOOD</span>
                  <span className="text-[#00F0FF]">High-Contrast B&W</span>
                </div>
                <div className="flex justify-between">
                  <span>ASPECT_RATIO</span>
                  <span className="text-[#00F0FF]">9:16</span>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="text-[#444] tracking-widest uppercase">Guardrail Config</div>
              <div className="p-3 bg-black border border-[#1A1A1A] rounded space-y-2 text-white/60">
                <div className="flex justify-between">
                  <span>MAX_REVISIONS</span>
                  <span className="text-[#00F0FF]">3</span>
                </div>
                <div className="flex justify-between">
                  <span>RECURSION_LIMIT</span>
                  <span className="text-[#00F0FF]">15</span>
                </div>
                <div className="flex justify-between">
                  <span>PASSIVE_THRESHOLD</span>
                  <span className="text-[#00F0FF]">8.5</span>
                </div>
                <div className="flex justify-between">
                  <span>CREATIVE_TOKEN_CAP</span>
                  <span className="text-[#00F0FF]">5,000</span>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="text-[#444] tracking-widest uppercase">System Stability</div>
              <div className="h-32 bg-black border border-[#1A1A1A] rounded flex items-end justify-around p-2 gap-1 overflow-hidden">
                {[40, 70, 45, 90, 65, 85, 30].map((h, i) => (
                  <motion.div
                    key={i}
                    initial={{ height: 0 }}
                    animate={{ height: `${h}%` }}
                    className="w-full bg-[#00F0FF]/10 border-t border-[#00F0FF]/30"
                  />
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Stability Footer */}
      <div className="p-4 bg-black border-t border-[#1A1A1A]">
        <div className="flex justify-between items-center mb-2">
          <span className="text-[10px] text-[#444] uppercase tracking-widest">
            Pipeline Integrity
          </span>
          <span className="text-[10px] text-[#00F0FF] font-mono">98.4%</span>
        </div>
        <div className="w-full h-1 bg-[#1A1A1A] rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: '98.4%' }}
            className="h-full bg-[#00F0FF]"
          />
        </div>
      </div>
    </aside>
  );
}
