import { ArrowRight, Ship, FileText, MapPin, Calendar, Package, User } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ShipmentDetail } from "@/lib/api/shipment-types";

interface ShipmentInfoProps {
  shipment: ShipmentDetail;
}

function formatDate(iso: string | null): string {
  if (!iso) return "TBD";
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function InfoRow({
  icon: Icon,
  label,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-3">
      <Icon className="text-muted-foreground mt-0.5 h-4 w-4 shrink-0" />
      <div>
        <p className="text-muted-foreground text-sm">{label}</p>
        <div className="text-sm font-medium">{children}</div>
      </div>
    </div>
  );
}

export function ShipmentInfo({ shipment }: ShipmentInfoProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Shipment Details</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-6 sm:grid-cols-2">
        <InfoRow icon={Ship} label="Vessel / Voyage">
          {shipment.vessel_name ?? "TBD"} / {shipment.voyage_number ?? "TBD"}
        </InfoRow>

        <InfoRow icon={FileText} label="B/L Number">
          <span className="font-mono">
            {shipment.bl_number ?? "—"}
          </span>
        </InfoRow>

        <InfoRow icon={MapPin} label="Route">
          <span className="flex items-center gap-2">
            {shipment.pol_name ?? shipment.pol_code ?? "—"}
            <ArrowRight className="h-3 w-3" />
            {shipment.pod_name ?? shipment.pod_code ?? "—"}
          </span>
        </InfoRow>

        <InfoRow icon={Calendar} label="ETD / ETA">
          {formatDate(shipment.etd)} — {formatDate(shipment.eta)}
        </InfoRow>

        {(shipment.exporter_name || shipment.exporter_address) && (
          <InfoRow icon={User} label="Shipper">
            {shipment.exporter_name ?? "—"}
            {shipment.exporter_address && (
              <p className="text-muted-foreground text-xs">
                {shipment.exporter_address}
              </p>
            )}
          </InfoRow>
        )}

        {(shipment.importer_name || shipment.importer_address) && (
          <InfoRow icon={User} label="Consignee">
            {shipment.importer_name ?? "—"}
            {shipment.importer_address && (
              <p className="text-muted-foreground text-xs">
                {shipment.importer_address}
              </p>
            )}
          </InfoRow>
        )}

        {shipment.products.length > 0 && (
          <div className="sm:col-span-2">
            <InfoRow icon={Package} label="Cargo">
              <div className="mt-1 space-y-1">
                {shipment.products.map((p, i) => (
                  <div
                    key={i}
                    className="text-muted-foreground flex items-center gap-2 text-xs"
                  >
                    <span className="rounded bg-muted px-1.5 py-0.5 font-mono">
                      {p.hs_code}
                    </span>
                    <span>{p.description}</span>
                    {p.weight_kg && <span>({p.weight_kg} kg)</span>}
                    {p.packaging_type && <span>— {p.packaging_type}</span>}
                  </div>
                ))}
              </div>
            </InfoRow>
          </div>
        )}

        {shipment.incoterms && (
          <InfoRow icon={FileText} label="Incoterms">
            {shipment.incoterms}
          </InfoRow>
        )}

        {shipment.carrier_name && (
          <InfoRow icon={Ship} label="Carrier">
            {shipment.carrier_name}
            {shipment.carrier_code && (
              <span className="text-muted-foreground ml-1 text-xs">
                ({shipment.carrier_code})
              </span>
            )}
          </InfoRow>
        )}
      </CardContent>
    </Card>
  );
}
