export const UseCasesSection = () => {
  return (
    <section className="border-b divide-y max-xl:px-4">
      <div className="divide-fd-border max-w-layout w-full mx-auto grid grid-cols-2 border-x min-lg:divide-x max-lg:divide-y max-lg:grid-cols-1">
        <div className="text-sm p-8">
          <h3 className="text-lg font-medium mb-4">
            You’re building a plugin system
          </h3>
          <p className="text-fd-muted-foreground">
            Your application loads third-party plugins in the process.
          </p>
          <p className="mt-2 text-fd-muted-foreground">
            Each plugin is developed independently, with its own dependencies
            and versions. Any dependency conflicts between plugins can cause
            crashes and unexpected behavior.
          </p>
          <p className="font-medium mt-2">
            Without isolation, one plugin’s dependencies can break another — or
            the host itself.
          </p>
        </div>
        <div className="text-sm p-8">
          <h3 className="text-lg font-medium mb-4">
            You run user code inside a framework
          </h3>
          <p className="text-fd-muted-foreground">
            Your framework executes user-provided Python code.
          </p>
          <p className="mt-2 text-fd-muted-foreground">
            Framework internals need strict dependency versions, but user code
            may require different versions. Any dependency mismatches break the
            entire application.
          </p>
          <p className="font-medium mt-2">
            Mixing both leads to dependency conflicts and runtime errors.
          </p>
        </div>
      </div>
    </section>
  );
};
