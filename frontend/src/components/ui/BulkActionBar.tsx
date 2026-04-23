import { 
  CheckCircle2, 
  X, 
  ArrowRightLeft, 
  Tag, 
  EyeOff, 
  Share2,
  ChevronDown
} from 'lucide-react';

interface BulkActionBarProps {
  selectedCount: number;
  onClear: () => void;
  onAction: (action: string) => void;
}

export function BulkActionBar({ selectedCount, onClear, onAction }: BulkActionBarProps) {
  if (selectedCount === 0) return null;

  return (
    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-[100] animate-in slide-in-from-bottom-8 duration-300">
      <div className="bg-brand-dark/95 backdrop-blur-md border border-brand-green-500/30 rounded-2xl shadow-2xl shadow-brand-green-500/10 px-6 py-4 flex items-center gap-6 min-w-[500px]">
        <div className="flex items-center gap-3 pr-6 border-r border-white/10">
          <div className="w-8 h-8 rounded-full bg-brand-green-500 text-brand-dark flex items-center justify-center text-xs font-bold">
            {selectedCount}
          </div>
          <span className="text-sm font-syne font-medium text-white">Selected</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onAction('TRANSFER')}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-bold text-white/80 hover:text-white hover:bg-white/5 transition-all"
          >
            <ArrowRightLeft className="w-4 h-4" />
            Mark as Transfer
          </button>
          
          <button
            onClick={() => onAction('TAG')}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-bold text-white/80 hover:text-white hover:bg-white/5 transition-all"
          >
            <Tag className="w-4 h-4" />
            Change Tag
            <ChevronDown className="w-3 h-3 opacity-50" />
          </button>

          <button
            onClick={() => onAction('IGNORE')}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-bold text-white/80 hover:text-white hover:bg-white/5 transition-all"
          >
            <EyeOff className="w-4 h-4" />
            Ignore
          </button>

          <button
            onClick={() => onAction('AUTO')}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-bold text-brand-green-400 hover:text-brand-green-300 hover:bg-brand-green-500/10 transition-all border border-brand-green-500/20"
          >
            <Share2 className="w-4 h-4" />
            Auto-categorize similar
          </button>
        </div>

        <button
          onClick={onClear}
          className="ml-auto p-2 rounded-xl text-white/40 hover:text-white/80 hover:bg-white/5 transition-all"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
