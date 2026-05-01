import { CodeBlockContent, CodeBlockFrame } from './code-block';

export const DemoCode = () => {
  return (
    <section className="relative z-10">
      <CodeBlockFrame
        className="relative -right-2 pb-3"
        fileName="framework/main.py"
      >
        <CodeBlockContent
          lang="py"
          options={{
            decorations: [
              {
                start: { line: 4, character: 4 },
                end: { line: 4, character: 12 },
                properties: {
                  style:
                    '--shiki-light: var(--color-violet-600); --shiki-dark: var(--color-violet-400)',
                },
              },
              {
                start: { line: 4, character: 13 },
                end: { line: 4, character: 23 },
                properties: {
                  style:
                    '--shiki-light: var(--color-emerald-600); --shiki-dark: var(--color-emerald-400)',
                },
              },
            ],
          }}
          code={`import pydantic
# → resolves vendor/pydantic [2.13.3]

print(pydantic.__version__)
# → '2.13.3' ✓ vendored`}
        />
      </CodeBlockFrame>
      <CodeBlockFrame
        className="relative bottom-3 -left-2 xl:-left-8"
        fileName="user/hook.py"
      >
        <CodeBlockContent
          lang="py"
          options={{
            decorations: [
              {
                start: { line: 4, character: 4 },
                end: { line: 4, character: 13 },
                properties: {
                  style:
                    '--shiki-light: var(--color-violet-600); --shiki-dark: var(--color-violet-400)',
                },
              },
              {
                start: { line: 4, character: 14 },
                end: { line: 4, character: 22 },
                properties: {
                  style:
                    '--shiki-light: var(--color-emerald-600); --shiki-dark: var(--color-emerald-400)',
                },
              },
            ],
          }}
          code={`import pydantic
# → resolves site-packages/pydantic [1.10.26]
 
print(pydantic.__version__)
# → '1.10.26' ✓ global`}
        />
      </CodeBlockFrame>
    </section>
  );
};
