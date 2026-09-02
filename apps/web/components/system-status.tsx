import type { ComponentType } from "react";

import { Boxes, Database, HardDrive } from "lucide-react";

import type { HealthSnapshot } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/status-badge";
import { describeCheck, formatLatency, impactOf, orderedChecks } from "@/lib/health";

type IconComponent = ComponentType<{ className?: string }>;

const COMPONENT_META: Record<string, { label: string; icon: IconComponent; role: string }> = {
  database: { label: "PostgreSQL", icon: Database, role: "System of record" },
  redis: { label: "Redis", icon: HardDrive, role: "Cache and Celery broker" },
  celery: { label: "Celery worker", icon: Boxes, role: "Background jobs" },
};

const IMPACT_NOTE = {
  blocking: "Required - the API returns 503 while this is down.",
  reduced: "Optional - the API keeps serving requests without it.",
  none: "",
} as const;

/**
 * PHASE 0 status tiles: one per dependency, plus the service verdict.
 *
 * Not a chart - three labelled values do not need a plot. Each tile pairs an
 * icon, a text status and a latency figure, which is also why the tiles stay
 * readable for a colourblind reader and in a monochrome print.
 */
export function SystemStatus({ snapshot }: { snapshot: HealthSnapshot }) {
  if (!snapshot.reachable) {
    return (
      <Card className="border-destructive/40">
        <CardHeader>
          <CardTitle>Backend unreachable</CardTitle>
          <CardDescription>{snapshot.error}</CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Start the stack with <code className="font-mono">docker compose up</code>, then reload.
        </CardContent>
      </Card>
    );
  }

  const { report } = snapshot;
  const checks = orderedChecks(report.checks);

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <CardTitle>{report.service}</CardTitle>
              <CardDescription>
                v{report.version} · {report.environment} · HTTP {snapshot.httpStatus}
              </CardDescription>
            </div>
            <StatusBadge status={report.status} />
          </div>
        </CardHeader>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {checks.map(({ name, health }) => {
          const meta = COMPONENT_META[name];
          const Icon = meta?.icon;
          const impact = impactOf({ name, health });

          return (
            <Card key={name}>
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    {Icon ? <Icon className="size-4 text-muted-foreground" /> : null}
                    <CardTitle>{meta?.label ?? name}</CardTitle>
                  </div>
                  <StatusBadge status={health.status} />
                </div>
                <CardDescription>{meta?.role ?? "Dependency"}</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-1">
                <dl className="flex items-baseline gap-2">
                  <dt className="text-xs text-muted-foreground uppercase">Latency</dt>
                  <dd className="font-mono text-lg tabular-nums">
                    {formatLatency(health.latency_ms)}
                  </dd>
                </dl>
                <p className="text-sm text-muted-foreground">{describeCheck({ name, health })}</p>
                {impact !== "none" ? (
                  <p className="text-xs text-muted-foreground">{IMPACT_NOTE[impact]}</p>
                ) : null}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
