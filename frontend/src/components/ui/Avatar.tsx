interface AvatarProps {
  name: string;
  color?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function Avatar({ name, color = '#1268c4', size = 'md' }: AvatarProps) {
  const initials = name
    .split(' ')
    .map((part) => part[0])
    .slice(0, 2)
    .join('');
  const sizes = { sm: 'h-5 w-5 text-[8px]', md: 'h-8 w-8 text-[10px]', lg: 'h-11 w-11 text-sm' };
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center rounded-full font-bold text-white ${sizes[size]}`}
      style={{ backgroundColor: color }}
      aria-hidden="true"
    >
      {initials}
    </span>
  );
}
