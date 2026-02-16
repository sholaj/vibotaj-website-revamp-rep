import { Leaf, CheckCircle, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ShipmentDetail } from "@/lib/api/shipment-types";

interface EudrStatusCardProps {
  shipment: ShipmentDetail;
}

export function EudrStatusCard({ shipment }: EudrStatusCardProps) {
  const isCompliant = shipment.eudr_compliant === true;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Leaf className="h-4 w-4 text-green-600" />
          EUDR Status
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground text-sm">Compliance</span>
          {isCompliant ? (
            <Badge className="bg-success/10 text-success border-success/20 gap-1" variant="outline">
              <CheckCircle className="h-3 w-3" />
              Compliant
            </Badge>
          ) : (
            <Badge className="bg-warning/10 text-warning border-warning/20 gap-1" variant="outline">
              <AlertTriangle className="h-3 w-3" />
              {shipment.eudr_compliant === false ? "Non-Compliant" : "Pending"}
            </Badge>
          )}
        </div>

        {shipment.eudr_statement_id && (
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground text-sm">Statement ID</span>
            <span className="font-mono text-sm">
              {shipment.eudr_statement_id}
            </span>
          </div>
        )}

        <p className="text-muted-foreground text-xs">
          This shipment contains products subject to EU Deforestation
          Regulation. Due diligence documentation is required.
        </p>
      </CardContent>
    </Card>
  );
}
