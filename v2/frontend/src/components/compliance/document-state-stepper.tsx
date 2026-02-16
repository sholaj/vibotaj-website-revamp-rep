import { CheckCircle, Circle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { DocumentTransition } from "@/lib/api/compliance-types";
import { getStateLabel, getStateColor } from "@/lib/api/compliance-types";

interface DocumentStateStepperProps {
  transitions: DocumentTransition[];
}

function formatTimestamp(ts: string | null): string {
  if (!ts) return "";
  const d = new Date(ts);
  return d.toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function DocumentStateStepper({ transitions }: DocumentStateStepperProps) {
  if (transitions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">State History</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No state transitions recorded.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          State History ({transitions.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ol className="relative border-l border-border ml-3 space-y-6">
          {transitions.map((t, idx) => {
            const isLast = idx === transitions.length - 1;

            return (
              <li key={t.id} className="ml-6" data-testid={`transition-${idx}`}>
                <span
                  className={cn(
                    "absolute -left-3 flex h-6 w-6 items-center justify-center rounded-full ring-4 ring-background",
                    isLast ? "bg-primary" : "bg-muted",
                  )}
                >
                  {isLast ? (
                    <CheckCircle className="h-3.5 w-3.5 text-primary-foreground" />
                  ) : (
                    <Circle className="h-3.5 w-3.5 text-muted-foreground" />
                  )}
                </span>

                <div className="flex flex-col">
                  <div className="flex items-center gap-2">
                    <span className={cn("text-sm font-medium", getStateColor(t.from_state))}>
                      {getStateLabel(t.from_state)}
                    </span>
                    <span className="text-xs text-muted-foreground">&rarr;</span>
                    <span className={cn("text-sm font-medium", getStateColor(t.to_state))}>
                      {getStateLabel(t.to_state)}
                    </span>
                  </div>

                  {t.created_at && (
                    <time className="text-xs text-muted-foreground">
                      {formatTimestamp(t.created_at)}
                    </time>
                  )}

                  {t.reason && (
                    <p className="mt-1 text-xs text-muted-foreground italic">
                      {t.reason}
                    </p>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
      </CardContent>
    </Card>
  );
}
