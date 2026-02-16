"use client";

import { Loader2, Plug, Unplug, CircleDot } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  type IntegrationConfig,
  type IntegrationType,
  INTEGRATION_LABELS,
  INTEGRATION_DESCRIPTIONS,
  getConnectionStatus,
  STATUS_LABELS,
} from "@/lib/api/integration-types";

interface IntegrationCardProps {
  type: IntegrationType;
  config: IntegrationConfig | null;
  onTestConnection: (type: IntegrationType) => void;
  isTesting?: boolean;
  testResult?: { success: boolean; message: string } | null;
}

export function IntegrationCard({
  type,
  config,
  onTestConnection,
  isTesting,
  testResult,
}: IntegrationCardProps) {
  const status = getConnectionStatus(config);
  const label = INTEGRATION_LABELS[type];
  const description = INTEGRATION_DESCRIPTIONS[type];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {status === "connected" ? (
              <Plug className="h-5 w-5 text-green-600" />
            ) : (
              <Unplug className="h-5 w-5 text-muted-foreground" />
            )}
            <div>
              <CardTitle className="text-base">{label}</CardTitle>
              <CardDescription className="text-xs mt-0.5">
                {description}
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <CircleDot
              className={`h-3 w-3 ${status === "connected" ? "text-green-500" : status === "disconnected" ? "text-red-500" : "text-gray-400"}`}
            />
            <span className="text-xs text-muted-foreground">
              {STATUS_LABELS[status]}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* Provider info */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Provider</span>
            <span className="font-medium">
              {config?.provider ?? "Not configured"}
            </span>
          </div>

          {/* Active status */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Status</span>
            <span className="font-medium">
              {config?.is_active ? "Active" : "Inactive"}
            </span>
          </div>

          {/* Last tested */}
          {config?.last_tested_at && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Last Tested</span>
              <span className="font-medium">
                {new Date(config.last_tested_at).toLocaleString()}
              </span>
            </div>
          )}

          {/* Test result message */}
          {testResult && (
            <div
              className={`text-xs px-3 py-2 rounded-md ${
                testResult.success
                  ? "bg-green-50 text-green-700 border border-green-200"
                  : "bg-red-50 text-red-700 border border-red-200"
              }`}
            >
              {testResult.message}
            </div>
          )}

          {/* Test connection button */}
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={() => onTestConnection(type)}
            disabled={isTesting}
          >
            {isTesting ? (
              <>
                <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
                Testing...
              </>
            ) : (
              "Test Connection"
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
