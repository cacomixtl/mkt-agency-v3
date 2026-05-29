//Trigger clean build
import { useState } from 'react';
import { motion } from 'motion/react';
import type { SSEEventBreakpoint, MarketingContent, HITLDecision } from '@/types';

interface BreakpointGateProps {
  breakpoint: SSEEventBreakpoint;
  preview: MarketingContent | null;
  onDecision: (decision: HITLDecision, feedback?: string) => void;
}

export default function BreakpointGate({ breakpoint, preview, onDecision }: BreakpointGateProps) {
  const [feedback, setFeedback] = useState('');
  const [activeAction, setActiveAction] = useState<HITLDecision | null>(null);

  const isPassive = breakpoint.approval_mode === 'passive';

  const getImageUrl = (url: string | undefined) => {
    if (!url) return '';
    if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
      return url;
    }
    const BASE_URL = import.meta.env.DEV
      ? (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000')
      : '/api';
    const cleanUrl = url.startsWith('/') ? url : `/${url}`;
    return `${BASE_URL}${cleanUrl}`;
  };

  const handleSubmit = (decision: HITLDecision) => {
    if ((decision === 'reject' || decision === 'request_revision') && !feedback.trim()) {
      setActiveAction(decision);
      return; // Force them to write feedback
    }
    onDecision(decision, feedback || undefined);
    setFeedback('');
    setActiveAction(null);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      {/* Header */}
      <div className="flex items-center gap-2">
        <motion.div
          className={`w-2 h-2 rounded-full ${isPassive ? 'bg-[#00F0FF]' : 'bg-[#FFB800]'}`}
          animate={{ opacity: [1, 0.3, 1] }}
          transition={{ duration: 1.2, repeat: Infinity }}
        />
        <span
          className={`text-[10px] font-bold uppercase tracking-widest ${
            isPassive ? 'text-[#00F0FF]' : 'text-[#FFB800]'
          }`}
        >
          {isPassive ? 'Passive Approval' : 'Active Approval Required'}
        </span>
      </div>

      {/* Content Preview */}
      {preview && (
        <div className="space-y-3">
          {/* Caption */}
          <div>
            <span className="text-[9px] text-[#444] uppercase tracking-widest block mb-1">
              Caption
            </span>
            <div className="p-3 bg-black border border-[#1A1A1A] rounded text-[11px] text-white/70 leading-relaxed font-mono">
              {preview.caption}
            </div>
          </div>

          {/* Image Prompt */}
          <div>
            <span className="text-[9px] text-[#444] uppercase tracking-widest block mb-1">
              Image Directive
            </span>
            <div className="p-3 bg-black border border-[#1A1A1A] rounded text-[10px] text-[#8B5CF6]/80 leading-relaxed font-mono">
              {preview.image_prompt}
            </div>
          </div>

          {/* Generated Visual */}
          <div>
            <span className="text-[9px] text-[#444] uppercase tracking-widest block mb-1">
              Generated Visual
            </span>
            {preview.image_urls && preview.image_urls.length > 0 ? (
              <div className="border border-[#1A1A1A] rounded overflow-hidden bg-black flex items-center justify-center">
                <img
                  src={getImageUrl(preview.image_urls[0])}
                  alt="Generated content asset"
                  className="w-full h-auto object-cover max-h-[300px]"
                />
              </div>
            ) : (
              <div className="h-40 bg-black border border-[#1A1A1A] rounded flex items-center justify-center">
                <span className="text-[9px] font-mono text-[#333] uppercase tracking-widest">
                  Awaiting Asset
                </span>
              </div>
            )}
          </div>

          {/* Metadata Row */}
          <div className="flex gap-4 text-[9px] font-mono">
            <div>
              <span className="text-[#444]">VIBE </span>
              <span className="text-[#00F0FF]">{preview.vibe_score?.toFixed(1) ?? '—'}</span>
            </div>
            <div>
              <span className="text-[#444]">RATIO </span>
              <span className="text-white/60">{preview.aspect_ratio}</span>
            </div>
            <div>
              <span className="text-[#444]">TARGET </span>
              <span className="text-white/60">{preview.publish_targets.join(', ')}</span>
            </div>
          </div>
        </div>
      )}

      {/* Feedback Textarea */}
      {(activeAction === 'reject' || activeAction === 'request_revision') && (
        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
          <span className="text-[9px] text-[#FFB800] uppercase tracking-widest block mb-1">
            Director Notes (Required)
          </span>
          <textarea
            id="input-feedback"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Provide specific feedback..."
            className="w-full h-20 p-3 bg-black border border-[#FFB800]/30 rounded text-[11px] text-white/70 font-mono resize-none focus:outline-none focus:border-[#FFB800] placeholder:text-[#333] transition-colors"
          />
        </motion.div>
      )}

      {/* Action Buttons */}
      <div className="grid grid-cols-3 gap-2">
        <motion.button
          id="btn-approve"
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          onClick={() => handleSubmit('approve')}
          className="h-9 rounded border border-[#00F0FF]/40 bg-[#00F0FF]/5 text-[#00F0FF] text-[9px] font-bold uppercase tracking-widest hover:bg-[#00F0FF]/10 hover:border-[#00F0FF] transition-all"
        >
          Approve
        </motion.button>

        <motion.button
          id="btn-reject"
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          onClick={() => {
            if (activeAction === 'reject' && feedback.trim()) {
              handleSubmit('reject');
            } else {
              setActiveAction('reject');
            }
          }}
          className="h-9 rounded border border-[#FF3B30]/40 bg-[#FF3B30]/5 text-[#FF3B30] text-[9px] font-bold uppercase tracking-widest hover:bg-[#FF3B30]/10 hover:border-[#FF3B30] transition-all"
        >
          Reject
        </motion.button>

        <motion.button
          id="btn-revise"
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          onClick={() => {
            if (activeAction === 'request_revision' && feedback.trim()) {
              handleSubmit('request_revision');
            } else {
              setActiveAction('request_revision');
            }
          }}
          className="h-9 rounded border border-[#FFB800]/40 bg-[#FFB800]/5 text-[#FFB800] text-[9px] font-bold uppercase tracking-widest hover:bg-[#FFB800]/10 hover:border-[#FFB800] transition-all"
        >
          Revise
        </motion.button>
      </div>
    </motion.div>
  );
}
