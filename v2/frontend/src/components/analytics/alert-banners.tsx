import { AlertTriangle, Clock, CheckCircle } from "lucide-react";
import type { AnalyticsDashboard } from "@/lib/api/analytics-types";

interface AlertBannersProps {
  dashboard: AnalyticsDashboard;
}

export function AlertBanners({ dashboard }: AlertBannersProps) {
  const { documents, shipments, compliance } = dashboard;
  const hasExpiring = documents.expiring_soon > 0;
  const hasDelays = shipments.with_delays > 0;
  const allCompliant = compliance.needing_attention === 0;

  if (!hasExpiring && !hasDelays && !allCompliant) return null;

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      {hasExpiring && (
        <div className="flex items-center gap-3 rounded-lg border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-800 dark:bg-yellow-950">
          <AlertTriangle className="h-5 w-5 shrink-0 text-yellow-600" />
          <div>
            <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
              {documents.expiring_soon} document(s) expiring soon
            </p>
            <p className="text-xs text-yellow-600 dark:text-yellow-400">
              Within the next 30 days
            </p>
          </div>
        </div>
      )}

      {hasDelays && (
        <div className="flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950">
          <Clock className="h-5 w-5 shrink-0 text-red-600" />
          <div>
            <p className="text-sm font-medium text-red-800 dark:text-red-200">
              {shipments.with_delays} shipment(s) delayed
            </p>
            <p className="text-xs text-red-600 dark:text-red-400">
              May require attention
            </p>
          </div>
        </div>
      )}

      {allCompliant && (
        <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-950">
          <CheckCircle className="h-5 w-5 shrink-0 text-green-600" />
          <div>
            <p className="text-sm font-medium text-green-800 dark:text-green-200">
              All shipments compliant
            </p>
            <p className="text-xs text-green-600 dark:text-green-400">
              No compliance issues detected
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
