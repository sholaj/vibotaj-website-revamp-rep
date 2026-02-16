"use client";

import { useState, useCallback, useEffect } from "react";
import { Bell, Mail, Save, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  type NotificationPreference,
  type NotificationCategory,
  ALL_EVENT_TYPES,
  EVENT_TYPE_LABELS,
  CATEGORY_LABELS,
  groupByCategory,
} from "@/lib/api/notification-types";

interface NotificationPreferencesProps {
  preferences: NotificationPreference[];
  onSave: (preferences: NotificationPreference[]) => void;
  isSaving?: boolean;
}

export function NotificationPreferences({
  preferences,
  onSave,
  isSaving,
}: NotificationPreferencesProps) {
  const [localPrefs, setLocalPrefs] = useState<NotificationPreference[]>([]);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    setLocalPrefs(preferences);
    setHasChanges(false);
  }, [preferences]);

  const togglePref = useCallback(
    (eventType: string, field: "email_enabled" | "in_app_enabled") => {
      setLocalPrefs((prev) =>
        prev.map((p) =>
          p.event_type === eventType ? { ...p, [field]: !p[field] } : p,
        ),
      );
      setHasChanges(true);
    },
    [],
  );

  const handleSave = useCallback(() => {
    onSave(localPrefs);
  }, [localPrefs, onSave]);

  const grouped = groupByCategory(ALL_EVENT_TYPES);
  const prefMap = Object.fromEntries(
    localPrefs.map((p) => [p.event_type, p]),
  );

  const categories = Object.entries(grouped) as [
    NotificationCategory,
    string[],
  ][];

  return (
    <div className="space-y-6">
      {categories.map(([category, events]) => (
        <div key={category} className="space-y-3">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            {CATEGORY_LABELS[category]}
          </h3>
          <div className="rounded-lg border">
            {/* Header */}
            <div className="flex items-center justify-between border-b bg-muted/30 px-4 py-2">
              <span className="text-sm font-medium">Event</span>
              <div className="flex items-center gap-8">
                <div className="flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">Email</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Bell className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">In-App</span>
                </div>
              </div>
            </div>
            {/* Rows */}
            {events.map((eventType) => {
              const pref = prefMap[eventType];
              if (!pref) return null;
              return (
                <div
                  key={eventType}
                  className="flex items-center justify-between px-4 py-3 border-b last:border-b-0"
                >
                  <Label className="text-sm">
                    {EVENT_TYPE_LABELS[eventType as keyof typeof EVENT_TYPE_LABELS]}
                  </Label>
                  <div className="flex items-center gap-8">
                    <Switch
                      checked={pref.email_enabled}
                      onCheckedChange={() =>
                        togglePref(eventType, "email_enabled")
                      }
                      size="sm"
                      aria-label={`Email for ${eventType}`}
                    />
                    <Switch
                      checked={pref.in_app_enabled}
                      onCheckedChange={() =>
                        togglePref(eventType, "in_app_enabled")
                      }
                      size="sm"
                      aria-label={`In-app for ${eventType}`}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}

      <Button
        onClick={handleSave}
        disabled={!hasChanges || isSaving}
        className="w-full sm:w-auto"
      >
        {isSaving ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Saving...
          </>
        ) : (
          <>
            <Save className="mr-2 h-4 w-4" />
            Save Preferences
          </>
        )}
      </Button>
    </div>
  );
}
