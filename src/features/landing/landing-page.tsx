import { PageTransition } from "@/components/animation/page-transition";
import { Footer } from "@/features/landing/sections/footer";
import { HeroSection } from "@/features/landing/sections/hero-section";
import { IntelligenceSection } from "@/features/landing/sections/intelligence-section";
import { OperationsSection } from "@/features/landing/sections/operations-section";
import { StatsSection } from "@/features/landing/sections/stats-section";
import { ShowcaseSection } from "@/features/landing/sections/showcase-section";
import { CtaSection } from "@/features/landing/sections/cta-section";

export function LandingPage() {
  return (
    <PageTransition>
      <HeroSection />
      <StatsSection />
      <IntelligenceSection />
      <OperationsSection />
      <ShowcaseSection />
      <CtaSection />
      <Footer />
    </PageTransition>
  );
}
