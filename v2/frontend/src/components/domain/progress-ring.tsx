interface ProgressRingProps {
  value: number;
  max?: number;
  label: string;
  color?: string;
  size?: number;
}

export function ProgressRing({
  value,
  max = 100,
  label,
  color = "hsl(var(--primary))",
  size = 96,
}: ProgressRingProps) {
  const radius = (size - 16) / 2;
  const circumference = 2 * Math.PI * radius;
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  const strokeDashoffset = circumference - (percentage / 100) * circumference;
  const center = size / 2;

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          className="-rotate-90"
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
        >
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="hsl(var(--muted))"
            strokeWidth="8"
          />
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xl font-bold" data-testid="ring-value">
            {Math.round(percentage)}%
          </span>
        </div>
      </div>
      <span className="text-muted-foreground mt-2 text-sm">{label}</span>
    </div>
  );
}
