export function BrandMark({ green = false }: { green?: boolean }) {
  const colors = green ? ['#24a47a', '#07875f', '#0a7253'] : ['#7da9d9', '#1872ce', '#0753a7'];
  return (
    <div className="flex h-12 w-12 shrink-0 items-end justify-center gap-1 rounded-xl bg-slate-50 p-2" aria-hidden="true">
      {[19, 31, 39].map((height, index) => (
        <span key={height} className="w-2 rounded-t-[2px]" style={{ height, backgroundColor: colors[index] }} />
      ))}
    </div>
  );
}
