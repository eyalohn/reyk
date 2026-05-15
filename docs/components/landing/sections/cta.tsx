import Link from 'next/link';

export const CTASection = () => {
  return (
    <section className="py-12 max-xl:px-8">
      <div className="max-w-layout w-full mx-auto flex flex-col items-center text-center">
        <h2 className="text-2xl text-center font-semibold mb-3 max-md:text-xl">
          Ready to end the dependency hell?
        </h2>
        <p className="max-w-lg text-fd-muted-foreground">
          Reyk is open source and ready for production. Start isolating your
          dependencies in minutes.
        </p>
        <div className="flex gap-4 mt-4">
          <Link
            href="/docs/quick-start"
            className="bg-fd-primary text-fd-primary-foreground font-medium text-sm text-center px-5 py-2.5 rounded-full no-underline"
          >
            Read the documentation
          </Link>
        </div>
      </div>
    </section>
  );
};
