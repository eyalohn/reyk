export const Footer = () => {
  return (
    <footer className="border-t px-8 py-6 text-fd-muted-foreground">
      <p className="text-xs font-mono">
        © {new Date().getFullYear()} Reyk. All rights reserved.
      </p>
    </footer>
  );
};
