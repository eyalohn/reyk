import { highlight } from 'fumadocs-core/highlight';
import type { HighlightOptions } from 'fumadocs-core/highlight';
import type { ComponentProps } from 'react';
import type { BundledTheme } from 'shiki';
import { CodeBlock, type CodeBlockProps, Pre } from '../mdx/codeblock';
import { cn } from '@/lib/utils';

const defaultThemes = {
  themes: {
    light: 'github-light' satisfies BundledTheme,
    dark: 'one-dark-pro' satisfies BundledTheme,
  },
  defaultColor: false as const,
};

const defaultCodeBlockProps: CodeBlockProps = {
  className: 'border-0 my-0 shadow-none bg-transparent dark:bg-transparent',
  keepBackground: true,
  'data-line-numbers': true,
  viewportProps: {
    className: 'overflow-x-auto overflow-y-visible max-h-none',
  },
};

function createPre(codeblock: CodeBlockProps, allowCopy: boolean) {
  return function HighlightedPre(props: ComponentProps<'pre'>) {
    return (
      <CodeBlock
        {...props}
        {...codeblock}
        allowCopy={allowCopy}
        className={cn('my-0', props.className, codeblock.className)}
      >
        <Pre className="py-1">{props.children}</Pre>
      </CodeBlock>
    );
  };
}

export async function CodeBlockContent({
  className,
  lang,
  code,
  codeblock,
  options,
  allowCopy = false,
}: {
  className?: string;
  lang: string;
  code: string;
  codeblock?: CodeBlockProps;
  allowCopy?: boolean;
  options?: Omit<HighlightOptions, 'lang'>;
}) {
  const merged = { ...defaultCodeBlockProps, ...codeblock };
  merged.className = cn(merged.className, className);

  const highlighted = await highlight(code, {
    lang,
    ...defaultThemes,
    ...options,
    components: {
      pre: createPre(merged, allowCopy),
      ...options?.components,
    },
  } satisfies HighlightOptions);

  return highlighted;
}

export const CodeBlockFrame = ({
  fileName,
  className,
  children,
  ...props
}: {
  fileName?: string;
  className?: string;
} & ComponentProps<'div'>) => {
  return (
    <div
      className={cn(
        'border ring ring-offset-4 ring-fd-border bg-white rounded-lg dark:bg-fd-card dark:ring-offset-fd-card',
        className,
      )}
      {...props}
    >
      <div className="relative border-b text-xs text-fd-muted-foreground py-2 text-center">
        <div className="flex items-center gap-1 pl-3 min-w-[62px] absolute -translate-y-1/2 top-1/2">
          <div className="w-2 h-2 rounded-full bg-[#EE6D5E]"></div>
          <div className="w-2 h-2 rounded-full bg-[#F3BF4A]"></div>
          <div className="w-2 h-2 rounded-full bg-[#5DC753]"></div>
        </div>
        {fileName}
      </div>
      {children}
    </div>
  );
};
