import { create } from "zustand";

interface WorkbenchState {
  highlightedExtractionId?: string;
  setHighlightedExtractionId: (value?: string) => void;
  reset: () => void;
}

export const useWorkbenchStore = create<WorkbenchState>((set) => ({
  highlightedExtractionId: undefined,
  setHighlightedExtractionId: (value) => set({ highlightedExtractionId: value }),
  reset: () => set({ highlightedExtractionId: undefined }),
}));

