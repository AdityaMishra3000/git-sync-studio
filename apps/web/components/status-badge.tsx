import type { ComponentType } from "react";

import { CircleCheck, CircleX, TriangleAlert } from "lucide-react";

import type { ComponentStatus } from "@/types";

import { Badge } from "@/components/ui/badge";
import { STATUS_LABEL, statusTone, type Tone } from "@/lib/health";
import { cn } from "@/lib/utils";

type IconComponent = ComponentType<{ className?: string }>;

const TONE_ICON: Record<Tone, IconComponent> = {
  positive: CircleCheck,
  caution: TriangleAlert,
  negative: CircleX,
};

/**
 * Status colours come from the reserved status palette and are mode-invariant.
 * They sit on the *icon* only: the label stays in a text token so it keeps full
 * contrast, and meaning never depends on colour alone.
 */
const TONE_ICON_COLOR: Record<Tone, string> = {
  positive: "text-status-good",
  caution: "text-status-warning",
  negative: "text-status-critical",
};

export function StatusBadge({
  status,
  className,
}: {
  status: ComponentStatus;
  className?: string;
}) {
  const tone = statusTone(status);
  const Icon = TONE_ICON[tone];

  return (
    <Badge variant="outline" className={cn("gap-1.5", className)}>
      <Icon className={cn("size-3", TONE_ICON_COLOR[tone])} />
      <span>{STATUS_LABEL[status]}</span>
    </Badge>
  );
}
