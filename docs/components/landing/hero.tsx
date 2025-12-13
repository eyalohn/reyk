import Link from 'fumadocs-core/link';
import { BoxIcon } from 'lucide-react';

export default function Hero() {
  return (
    <section className="relative w-full flex md:items-center md:justify-center bg-white/96 dark:bg-black/96 antialiased min-h-120">
      {/* Background Grid */}
      <div className="absolute inset-0 left-5 right-5 lg:left-16 lg:right-14 xl:left-16 xl:right-14">
        <div className="absolute inset-0 bg-grid text-muted/50 text-black/2 dark:text-white/3" />
        <div className="absolute inset-0 bg-linear-to-b from-transparent via-transparent to-background" />
      </div>

      {/* Content */}
      <div className="mx-auto grid lg:max-w-8xl xl:max-w-8/12 grid-cols-1 items-center gap-x-8 gap-y-16 px-4 py-2 lg:grid-cols-2 lg:px-8 lg:py-4 xl:gap-x-16 xl:px-0">
        <div className="relative z-10 text-left lg:mt-0">
          <div className="mb-2 flex items-center gap-1">
            <BoxIcon className="size-3" />
            <span className="text-xs text-opacity-75">Vendor dependencies</span>
          </div>

          <p className="text-zinc-800 dark:text-zinc-300 tracking-tight text-2xl font-medium md:text-3xl text-pretty">
            Ship Python libraries without dependency fear.
          </p>

          <div className="mt-4 relative flex items-center justify-between gap-2 w-full sm:w-[90%] rounded-lg border border-black/5 dark:border-white/10 px-4 py-2">
            <p className="relative inline tracking-tight opacity-90 md:text-sm text-xs dark:text-white font-mono text-black">
              pip install{' '}
              <span className="dark:text-fuchsia-300 text-fuchsia-800">
                pyisolate
              </span>
            </p>

            <div className="flex gap-2 items-center">
              <Link
                href="https://pypi.org/project/pyisolate"
                rel="noopener noreferrer"
                target="_blank"
              >
                <img src="/pypi-icon.svg" className="size-4" alt="PyPI" />
              </Link>
              <Link
                href="https://github.com/OughtToPrevail/PyIsolate"
                target="_blank"
              >
                <img src="/github-icon.svg" className="size-4" alt="GitHub" />
              </Link>
            </div>
          </div>

          <div className="mt-8 flex w-fit flex-col gap-4 font-sans md:flex-row md:justify-center lg:justify-start items-center">
            <Link
              href="/docs"
              className="bg-fd-primary text-fd-primary-foreground font-semibold text-sm px-3 py-1.5 rounded-lg "
            >
              Get Started
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
