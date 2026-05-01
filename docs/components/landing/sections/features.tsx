import { AnchorIcon, BoxIcon, PuzzleIcon } from 'lucide-react';
import { FeatureBentoItem } from '../feature';

export const FeatureSection = () => {
  return (
    <section className="border-b py-10">
      <div className="max-w-layout w-full mx-auto max-xl:px-8">
        <h2 className="text-2xl font-semibold tracking-tight text-fd-muted-foreground max-md:text-xl">
          Works the way{' '}
          <em className="not-italic text-fd-foreground">you expect.</em>
        </h2>
        <p className="mt-1 text-fd-muted-foreground">
          Everything you need for dependency isolation. Simple and powerful.
        </p>
        <div className="mt-8 grid grid-cols-3 gap-x-4 gap-y-2 max-md:grid-cols-1">
          <FeatureBentoItem icon={<BoxIcon />} title="Package-Scoped Isolation">
            Dependencies are isolated only within your package, not across the
            entire Python process.
          </FeatureBentoItem>
          <FeatureBentoItem icon={<AnchorIcon />} title="Native Import System">
            Built directly on Python’s import system. No source rewriting, no
            import renaming.
          </FeatureBentoItem>
          <FeatureBentoItem
            icon={<PuzzleIcon />}
            title="Multiple Versions, One Interpreter"
          >
            Run different versions of the same dependency side by side.
          </FeatureBentoItem>
        </div>
      </div>
    </section>
  );
};
