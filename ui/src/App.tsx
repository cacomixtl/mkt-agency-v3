import { useAgentStream } from '@/hooks/useAgentStream';
import PulseSidebar from '@/components/PulseSidebar';
import GalacticCanvas from '@/components/GalacticCanvas';
import CreativeCockpit from '@/components/CreativeCockpit';

export default function App() {
  const stream = useAgentStream();

  return (
    <main className="flex h-screen h-svh bg-black text-[#E0E0E0] font-sans overflow-hidden select-none">
      <PulseSidebar
        thoughts={stream.thoughts}
        currentNode={stream.currentNode}
        stage={stream.stage}
        isStreaming={stream.isStreaming}
        onStartSimulation={stream.startSimulation}
        onReset={stream.reset}
      />
      <GalacticCanvas
        nodes={stream.nodes}
        onPivot={stream.triggerPivot}
      />
      <CreativeCockpit
        breakpoint={stream.breakpoint}
        preview={stream.preview}
        onDecision={stream.submitDecision}
        isSubmitting={stream.isSubmitting}
      />
    </main>
  );
}
