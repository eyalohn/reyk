import {
  FeatureBentoItem,
  FeatureGridItem,
} from '@/components/landing/feature';
import Hero from '@/components/landing/hero';
import { AnchorIcon, BoxIcon, PuzzleIcon, ShieldIcon } from 'lucide-react';

export function HomePageContent() {
  return (
    <div className="[grid-area:main]">
      <Hero />

      <section className="border-b py-12">
        <div className="divide-x divide-fd-border max-w-layout w-full mx-auto grid grid-cols-2 px-4 max-md:divide-y max-md:grid-cols-1">
          <div className="md:pr-8 max-md:pb-8">
            <h3 className="text-xl font-semibold mb-6">
              <span className="text-fd-muted-foreground">//</span> You’re
              Building a Plugin System
            </h3>
            <p className="text-fd-foreground/85">
              Your application loads third-party plugins in the process.
            </p>
            <p className="mt-2 text-fd-foreground/85">
              Each plugin is developed independently, with its own dependencies
              and versions. Any dependency conflicts between plugins can cause
              crashes and unexpected behavior.
            </p>
            <p className="font-bold mt-2">
              Without isolation, one plugin’s dependencies can break another —
              or the host itself.
            </p>
          </div>
          <div className="md:pl-8 max-md:pt-8">
            <h3 className="text-xl font-semibold mb-6">
              <span className="text-fd-muted-foreground">//</span> You Run User
              Code Inside a Framework
            </h3>
            <p className="text-fd-foreground/85">
              Your framework executes user-provided Python code.
            </p>
            <p className="mt-2 text-fd-foreground/85">
              Framework internals need strict dependency versions, but user code
              may require different versions. Any dependency mismatches break
              the entire application.
            </p>
            <p className="font-bold mt-2">
              Mixing both leads to dependency conflicts and runtime errors.
            </p>
          </div>
        </div>
      </section>

      <section className="border-b py-12">
        <div className="max-w-layout w-full mx-auto px-4">
          <h2 className="text-3xl text-center font-semibold mb-12 text-fd-muted-foreground max-md:text-2xl">
            Works the way{' '}
            <em className="not-italic text-fd-foreground">you expect</em>
          </h2>
          <div className="grid grid-cols-3 gap-x-16 gap-y-8 max-md:grid-cols-1">
            <FeatureBentoItem
              icon={<BoxIcon />}
              title="Package-Scoped Isolation"
            >
              Dependencies are isolated only within your package, not across the
              entire Python process.
            </FeatureBentoItem>
            <FeatureBentoItem
              icon={<AnchorIcon />}
              title="Native Import System"
            >
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
    </div>
  );
}
