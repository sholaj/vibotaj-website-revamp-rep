"use client";

import { useState } from "react";
import { PageHeader } from "@/components/domain/page-header";
import { IntegrationCard } from "@/components/settings/integration-card";
import { IntegrationLogTable } from "@/components/settings/integration-log-table";
import {
  useIntegrations,
  useIntegrationLogs,
  useTestConnection,
} from "@/lib/api/integrations";
import {
  type IntegrationType,
  INTEGRATION_TYPES,
  INTEGRATION_LABELS,
} from "@/lib/api/integration-types";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function IntegrationsPage() {
  const { data, isLoading } = useIntegrations();
  const testMutation = useTestConnection();
  const [testResults, setTestResults] = useState<
    Record<string, { success: boolean; message: string } | null>
  >({});
  const [activeTab, setActiveTab] = useState<IntegrationType>("customs");
  const customsLogs = useIntegrationLogs("customs");
  const bankingLogs = useIntegrationLogs("banking");

  const handleTestConnection = (type: IntegrationType) => {
    setTestResults((prev) => ({ ...prev, [type]: null }));
    testMutation.mutate(type, {
      onSuccess: (result) => {
        setTestResults((prev) => ({
          ...prev,
          [type]: { success: result.success, message: result.message },
        }));
      },
      onError: (error) => {
        setTestResults((prev) => ({
          ...prev,
          [type]: { success: false, message: (error as Error).message },
        }));
      },
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Integrations"
        description="Connect customs and banking APIs for automated trade operations."
      />

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <p className="text-muted-foreground">Loading integrations...</p>
        </div>
      ) : (
        <>
          {/* Integration cards */}
          <div className="grid gap-4 md:grid-cols-2">
            {INTEGRATION_TYPES.map((type) => (
              <IntegrationCard
                key={type}
                type={type}
                config={data?.[type] ?? null}
                onTestConnection={handleTestConnection}
                isTesting={
                  testMutation.isPending &&
                  testMutation.variables === type
                }
                testResult={testResults[type]}
              />
            ))}
          </div>

          {/* Activity logs */}
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Recent Activity
            </h3>
            <Tabs
              value={activeTab}
              onValueChange={(v) => setActiveTab(v as IntegrationType)}
            >
              <TabsList>
                {INTEGRATION_TYPES.map((type) => (
                  <TabsTrigger key={type} value={type}>
                    {INTEGRATION_LABELS[type]}
                  </TabsTrigger>
                ))}
              </TabsList>
              <TabsContent value="customs">
                <IntegrationLogTable
                  logs={customsLogs.data?.logs ?? []}
                />
              </TabsContent>
              <TabsContent value="banking">
                <IntegrationLogTable
                  logs={bankingLogs.data?.logs ?? []}
                />
              </TabsContent>
            </Tabs>
          </div>
        </>
      )}
    </div>
  );
}
