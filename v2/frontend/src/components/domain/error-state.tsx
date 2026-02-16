import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <AlertCircle className="text-destructive mb-4 h-12 w-12" />
      <h3 className="text-lg font-medium">{title}</h3>
      <p className="text-muted-foreground mt-2 max-w-sm">{message}</p>
      {onRetry && (
        <Button variant="outline" onClick={onRetry} className="mt-4">
          Try again
        </Button>
      )}
    </div>
  );
}
