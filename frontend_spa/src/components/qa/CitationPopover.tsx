import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { Citation } from "@/api/types";

interface CitationPopoverProps {
  citation: Citation;
}

export function CitationPopover({ citation }: CitationPopoverProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className="p-2 bg-muted rounded text-xs cursor-pointer hover:bg-muted/80 transition-colors">
          [{citation.id}] {citation.filename || `文档 ${citation.document_id}`}
          {citation.chunk_index !== undefined && ` - 第 ${citation.chunk_index} 段`}
        </div>
      </TooltipTrigger>
      <TooltipContent side="left" className="max-w-sm">
        <div className="space-y-1">
          <p className="font-medium">{citation.filename}</p>
          {citation.snippet && (
            <p className="text-xs text-muted-foreground line-clamp-3">
              {citation.snippet}
            </p>
          )}
        </div>
      </TooltipContent>
    </Tooltip>
  );
}
