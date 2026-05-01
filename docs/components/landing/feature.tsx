interface Props {
  icon?: React.ReactNode;
  title: string;
  children: React.ReactNode;
}

export const FeatureGridItem: React.FC<Props> = ({ title, children }) => {
  return (
    <div className="flex flex-col border-l-2 pl-4">
      <h3 className="text-lg/snug font-semibold mb-4">{title}</h3>
      <p className="text-sm text-fd-muted-foreground">{children}</p>
    </div>
  );
};

export const FeatureBentoItem: React.FC<Props> = ({
  icon,
  title,
  children,
}) => {
  return (
    <div className="group border-fd-foreground/8 rounded-[10px] border p-1 transition-colors hover:border-fd-foreground/10">
      <div className="flex h-full flex-col gap-3 rounded-md border border-fd-foreground/6 p-5 transition-colors group-hover:border-fd-foreground/8 group-hover:bg-fd-foreground/1">
        <span className="text-fd-muted-foreground">{icon}</span>
        <div className="flex flex-col gap-1">
          <h3 className="text-sm font-semibold">{title}</h3>
          <p className="text-fd-muted-foreground text-sm leading-relaxed">
            {children}
          </p>
        </div>
      </div>
    </div>
  );
};
