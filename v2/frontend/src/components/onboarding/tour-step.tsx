"use client";

import {
  Package,
  FileText,
  Shield,
  BarChart3,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface TourStepProps {
  onComplete: () => void;
  onBack: () => void;
}

const FEATURES = [
  {
    icon: Package,
    title: "Shipment Tracking",
    description:
      "Track containers in real-time from port to port with live carrier updates.",
  },
  {
    icon: FileText,
    title: "Document Management",
    description:
      "Upload, validate, and manage compliance documents for every shipment.",
  },
  {
    icon: Shield,
    title: "Compliance Monitoring",
    description:
      "Automatic HS code classification and EU TRACES compliance checks.",
  },
  {
    icon: BarChart3,
    title: "Analytics Dashboard",
    description:
      "Operational metrics, shipment trends, and compliance scores at a glance.",
  },
];

export function TourStep({ onComplete, onBack }: TourStepProps) {
  return (
    <div className="space-y-6 py-4">
      <div className="text-center space-y-2">
        <h2 className="text-xl font-semibold">Quick Tour</h2>
        <p className="text-sm text-muted-foreground">
          Here&apos;s what you can do with TraceHub
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {FEATURES.map((feature) => (
          <div
            key={feature.title}
            className="rounded-lg border p-4 space-y-2"
          >
            <div className="flex items-center gap-2">
              <feature.icon className="h-5 w-5 text-primary" />
              <h3 className="font-medium text-sm">{feature.title}</h3>
            </div>
            <p className="text-xs text-muted-foreground">
              {feature.description}
            </p>
          </div>
        ))}
      </div>

      <div className="flex gap-3 pt-2">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button className="flex-1" onClick={onComplete}>
          Finish Setup
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}
