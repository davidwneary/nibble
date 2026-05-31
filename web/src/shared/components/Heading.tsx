interface HeadingProps {
  children: React.ReactNode;
  level?: 1 | 2 | 3 | 4 | 5 | 6;
  className?: string;
}

export function Heading({ children, level = 1, className = '' }: HeadingProps) {
  const Tag = `h${level}` as const;
  const sizeClasses: Record<number, string> = {
    1: 'text-3xl font-semibold',
    2: 'text-2xl font-semibold',
    3: 'text-lg font-semibold',
    4: 'text-base font-semibold',
    5: 'text-sm font-semibold',
    6: 'text-xs font-semibold',
  };

  return (
    <Tag className={`${sizeClasses[level]} text-text-primary ${className}`}>
      {children}
    </Tag>
  );
}
