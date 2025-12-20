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
    <div className="flex flex-col gap-2 [&>svg]:size-4">
      {icon}
      <h3 className="text-md/snug fmont-seibold">{title}</h3>
      <p className="text-sm text-fd-muted-foreground">{children}</p>
    </div>
  );
};
