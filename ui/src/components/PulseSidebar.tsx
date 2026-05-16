import { motion, AnimatePresence } from 'motion/react';
import { Activity } from 'lucide-react';
import type { Thought, CampaignStage } from '@/types';

interface PulseSidebarProps {
  thoughts: Thought[];
  currentNode: string | null;
  stage: CampaignStage;
  isStreaming: boolean;
  onStartSimulation: () => void;
  onReset: () => void;
}

const STAGE_LABELS: Record<CampaignStage, string> = {
  draft: 'DRAFTING',
  reviewing: 'REVIEWING',
  revising: 'REVISING',
  generating_image: 'IMAGING',
  awaiting_approval: 'AWAITING HITL',
  approved: 'APPROVED',
  published: 'PUBLISHED',
  vetoed: 'VETOED',
  failed: 'FAILED',
};

const STAGE_COLORS: Record<CampaignStage, string> = {
  draft: 'text-white/40',
  reviewing: 'text-[#00F0FF]',
  revising: 'text-[#FFB800]',
  generating_image: 'text-[#8B5CF6]',
  awaiting_approval: 'text-[#FFB800]',
  approved: 'text-[#00F0FF]',
  published: 'text-emerald-400',
  vetoed: 'text-[#FF3B30]',
  failed: 'text-[#FF3B30]',
};

export default function PulseSidebar({
  thoughts,
  currentNode,
  stage,
  isStreaming,
  onStartSimulation,
  onReset,
}: PulseSidebarProps) {
  return (
    <aside className="w-[220px] border-r border-[#1A1A1A] bg-[#0A0A0A] flex flex-col h-screen h-svh overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-[#1A1A1A]">
        <h1 className="text-[10px] tracking-[0.2em] font-bold text-[#00F0FF] uppercase">
          The Pulse
        </h1>
        <p className="text-[9px] text-[#444] font-mono mt-1 uppercase">
          AGENCY_V3 // COCKPIT
        </p>
      </div>

      {/* Stage Badge */}
      <div className="px-4 py-3 border-b border-[#1A1A1A]">
        <span className="text-[9px] text-[#444] uppercase tracking-widest block mb-1">
          Campaign Stage
        </span>
        <div className="flex items-center gap-2">
          {isStreaming && (
            <motion.div
              className="w-1.5 h-1.5 rounded-full bg-[#00F0FF]"
              animate={{ opacity: [1, 0.3, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
          )}
          <span className={`text-[11px] font-mono uppercase tracking-wider ${STAGE_COLORS[stage]}`}>
            {STAGE_LABELS[stage]}
          </span>
        </div>
      </div>

      {/* Active Node Indicator */}
      {currentNode && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="px-4 py-2 border-b border-[#1A1A1A] bg-[#00F0FF]/5"
        >
          <div className="flex items-center gap-2">
            <Activity size={10} className="text-[#00F0FF]" />
            <span className="text-[9px] font-mono text-[#00F0FF] uppercase tracking-wider truncate">
              {currentNode}
            </span>
          </div>
        </motion.div>
      )}

      {/* Thought Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-none">
        <AnimatePresence initial={false}>
          {thoughts.map((thought) => (
            <motion.div
              key={thought.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              className="space-y-1"
            >
              <div className="flex items-center gap-1.5 overflow-hidden font-mono text-[10px]">
                <span className="text-[#444] shrink-0">
                  [{new Date(thought.timestamp).toLocaleTimeString([], { hour12: false })}]
                </span>
                <span
                  className={`uppercase truncate ${
                    thought.agent === 'Error'
                      ? 'text-[#FF3B30]'
                      : thought.agent === 'System'
                        ? 'text-[#444]'
                        : thought.agent === 'Director'
                          ? 'text-[#FFB800]'
                          : 'text-[#00F0FF]'
                  }`}
                >
                  {thought.agent}:
                </span>
              </div>
              <p className={`text-[10px] font-mono leading-relaxed break-words pl-2 ${
                thought.agent === 'Error' ? 'text-[#FF3B30]' : 'text-white/40'
              }`}>
                {thought.text}
              </p>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Controls */}
      <div className="p-4 space-y-2 border-t border-[#1A1A1A]">
        {!isStreaming && stage === 'draft' && (
          <motion.button
            id="btn-start-campaign"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onStartSimulation}
            className="w-full h-10 rounded bg-transparent border border-[#00F0FF] flex items-center justify-center group relative overflow-hidden transition-all hover:bg-[#00F0FF]/5"
          >
            <div className="absolute inset-0 bg-[#00F0FF] opacity-5 blur-md" />
            <span className="text-[#00F0FF] text-[10px] font-bold tracking-[0.3em] uppercase relative">
              Start Campaign
            </span>
          </motion.button>
        )}

        {(stage === 'published' || stage === 'vetoed' || stage === 'failed') && (
          <motion.button
            id="btn-reset"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onReset}
            className="w-full h-10 rounded bg-transparent border border-[#444] flex items-center justify-center group relative overflow-hidden transition-all hover:bg-white/5"
          >
            <span className="text-[#444] text-[10px] font-bold tracking-[0.3em] uppercase relative group-hover:text-white/60">
              New Campaign
            </span>
          </motion.button>
        )}

        <motion.button
          id="btn-kill-switch"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onReset}
          className="w-full h-10 rounded bg-transparent border border-[#FF3B30] flex items-center justify-center group relative overflow-hidden transition-all hover:bg-[#FF3B30]/5"
        >
          <div className="absolute inset-0 bg-[#FF3B30] opacity-10 blur-md" />
          <span className="text-[#FF3B30] text-[10px] font-bold tracking-[0.3em] uppercase relative">
            Kill Switch
          </span>
        </motion.button>
      </div>
    </aside>
  );
}
