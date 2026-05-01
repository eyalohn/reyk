import Hero from '@/components/landing/hero';
import { CTASection } from './sections/cta';
import { Footer } from './sections/footer';
import { FeatureSection } from './sections/features';
import { UseCasesSection } from './sections/use-cases';

export function HomePageContent() {
  return (
    <div className="[grid-area:main]">
      <Hero />
      <UseCasesSection />
      <FeatureSection />
      <CTASection />
      <Footer />
    </div>
  );
}
