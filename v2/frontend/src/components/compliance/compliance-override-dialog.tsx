"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

interface ComplianceOverrideDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (reason: string) => void;
  isSubmitting?: boolean;
}

export function ComplianceOverrideDialog({
  open,
  onOpenChange,
  onSubmit,
  isSubmitting = false,
}: ComplianceOverrideDialogProps) {
  const [reason, setReason] = useState("");

  const isValid = reason.trim().length >= 5;

  const handleSubmit = () => {
    if (!isValid) return;
    onSubmit(reason.trim());
    setReason("");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent aria-describedby="override-description">
        <DialogHeader>
          <DialogTitle>Override Compliance</DialogTitle>
          <DialogDescription id="override-description">
            Override the compliance decision for this shipment. Provide a clear
            reason for the override. This action is logged.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label htmlFor="override-reason">Reason for override</Label>
            <Textarea
              id="override-reason"
              placeholder="Explain why this compliance check should be overridden..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
            />
            {reason.length > 0 && !isValid && (
              <p className="text-xs text-destructive">
                Reason must be at least 5 characters.
              </p>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!isValid || isSubmitting}
          >
            {isSubmitting ? "Submitting..." : "Submit Override"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
