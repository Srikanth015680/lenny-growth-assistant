import { AlertTriangle } from "lucide-react";
import { Button } from "./Button";

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex items-start gap-3 rounded-md border border-danger/30 bg-danger-soft px-4 py-3 text-sm text-danger">
      <AlertTriangle size={16} className="mt-0.5 flex-shrink-0" />
      <div className="flex-1">
        <p>{message}</p>
        {onRetry && (
          <Button variant="ghost" onClick={onRetry} className="mt-2 px-0 text-danger hover:bg-transparent hover:underline">
            Try again
          </Button>
        )}
      </div>
    </div>
  );
}
