import Link from 'fumadocs-core/link';
import { BoxIcon } from 'lucide-react';
import { DemoCode } from './demo-code';

export default function Hero() {
  return (
    <section className="relative w-full flex items-center justify-center antialiased min-h-100 border-b">
      {/* Background Grid */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-grid text-black/2 dark:text-white/2" />
        <div className="absolute inset-0 bg-linear-to-b from-transparent via-transparent to-background" />
      </div>

      {/* Content */}
      <div className="max-w-layout w-full mx-auto grid grid-cols-1 items-center gap-x-16 gap-y-16 py-12 max-xl:px-8 xl:grid-cols-2">
        <div className="relative z-10 text-left lg:mt-0">
          <div className="mb-2 flex items-center gap-1 mb-3">
            <BoxIcon className="size-3" />
            <span className="text-sm text-opacity-75">Vendor dependencies</span>
          </div>

          <h1 className="text-zinc-800 dark:text-zinc-300 tracking-tight text-2xl font-semibold md:text-3xl text-pretty">
            Ship Python libraries without dependency fear.
          </h1>

          <p className="mt-2 text-fd-muted-foreground min-md:text-balance">
            Run plugins and frameworks with their own dependencies — safely,
            inside one Python process.
          </p>

          <div className="flex gap-2 mt-8">
            <Link
              href="/docs/quick-start"
              className="bg-fd-primary text-fd-primary-foreground font-medium text-sm text-center px-5 py-2.5 rounded-full no-underline"
            >
              Get Started
            </Link>
            <a
              href="https://github.com/eyalohn/reyk"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-fd-secondary text-fd-secondary-foreground border font-medium text-sm text-center px-5 py-2.5 rounded-full no-underline"
            >
              View on GitHub
            </a>
          </div>
        </div>
        <DemoCode />
      </div>
    </section>
  );
}
