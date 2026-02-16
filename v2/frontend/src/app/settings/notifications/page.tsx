"use client";

import { PageHeader } from "@/components/domain/page-header";
import { NotificationPreferences } from "@/components/settings/notification-preferences";
import {
  useNotificationPreferences,
  useUpdateNotificationPreferences,
  getDefaultPreferences,
} from "@/lib/api/notifications";
import type { NotificationPreference } from "@/lib/api/notification-types";

export default function NotificationSettingsPage() {
  const { data, isLoading } = useNotificationPreferences();
  const updateMutation = useUpdateNotificationPreferences();

  const preferences = data?.preferences ?? getDefaultPreferences();

  const handleSave = (prefs: NotificationPreference[]) => {
    updateMutation.mutate({ preferences: prefs });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Notification Settings"
        description="Choose which events trigger email and in-app notifications."
      />

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <p className="text-muted-foreground">Loading preferences...</p>
        </div>
      ) : (
        <NotificationPreferences
          preferences={preferences}
          onSave={handleSave}
          isSaving={updateMutation.isPending}
        />
      )}
    </div>
  );
}
