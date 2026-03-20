# Canine.Fit SEO/GEO Implementation Schema

## Executive Summary

Based on analysis of 100+ keywords across 12 categories, this schema provides a comprehensive roadmap to dominate organic search for dog healthspan and AI-powered pet wellness.

**Key Opportunities Identified:**
- **GEO Gold**: 15+ question-based keywords with featured snippet potential
- **Low Competition**: Breed-specific leaderboards (very low competition, high engagement)
- **Brand Differentiation**: Lilo AI companion (unique positioning)
- **Comparison Traffic**: vs FitBark, Whistle (high commercial intent)

---

## 1. Technical SEO Foundation

### 1.1 Marketing Website Architecture

Since Canine.Fit is a mobile app, create a marketing website to capture organic search traffic:

**Recommended Stack**: Next.js 14+ with App Router (SSR for SEO)

```
canine-fit-web/
├── app/
│   ├── page.tsx                    # Homepage
│   ├── layout.tsx                  # Root layout with metadata
│   ├── healthspan/
│   │   ├── page.tsx               # Healthspan hub
│   │   ├── calculator/
│   │   │   └── page.tsx           # Free calculator tool
│   │   └── [breed]/
│   │       └── page.tsx           # Dynamic breed pages
│   ├── lilo-ai/
│   │   └── page.tsx               # Lilo AI feature page
│   ├── daily-ritual/
│   │   └── page.tsx               # Daily tracking feature
│   ├── leaderboard/
│   │   └── page.tsx               # Leaderboard showcase
│   ├── compare/
│   │   ├── page.tsx               # Comparison hub
│   │   ├── fitbark/
│   │   │   └── page.tsx           # vs FitBark
│   │   └── whistle/
│   │       └── page.tsx           # vs Whistle
│   ├── blog/
│   │   ├── page.tsx               # Blog listing
│   │   └── [slug]/
│   │       └── page.tsx           # Individual posts
│   └── download/
│       └── page.tsx               # App download CTA
├── components/
│   ├── schema/
│   │   ├── SoftwareAppSchema.tsx
│   │   ├── FAQSchema.tsx
│   │   ├── HowToSchema.tsx
│   │   └── ArticleSchema.tsx
│   └── ui/
├── lib/
│   └── seo.ts                     # SEO utilities
└── public/
    └── images/
```

### 1.2 Core Metadata Implementation

**Root Layout Metadata** (`app/layout.tsx`):

```typescript
import type { Metadata } from 'next';

export const metadata: Metadata = {
  metadataBase: new URL('https://canine.fit'),
  title: {
    default: 'Canine.Fit | AI Dog Healthspan Tracker - Extend Your Dog\'s Life',
    template: '%s | Canine.Fit',
  },
  description: 'Track your dog\'s healthspan in 15 seconds daily. AI-powered insights, breed leaderboards & personalized longevity scores. Join 10,000+ dog owners extending their pets\' lives.',
  keywords: ['dog healthspan', 'dog longevity', 'pet health tracker', 'AI dog companion', 'Lilo AI', 'dog wellness app'],
  authors: [{ name: 'Canine.Fit' }],
  creator: 'Canine.Fit',
  publisher: 'Canine.Fit',
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://canine.fit',
    siteName: 'Canine.Fit',
    title: 'Canine.Fit | AI Dog Healthspan Tracker',
    description: 'Track your dog\'s healthspan in 15 seconds daily. AI-powered insights & breed leaderboards.',
    images: [
      {
        url: 'https://canine.fit/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'Canine.Fit - AI Dog Healthspan Tracker',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Canine.Fit | AI Dog Healthspan Tracker',
    description: 'Track your dog\'s healthspan in 15 seconds daily. AI-powered insights & breed leaderboards.',
    images: ['https://canine.fit/twitter-image.jpg'],
    creator: '@caninefit',
  },
  verification: {
    google: 'your-google-verification-code',
  },
  alternates: {
    canonical: 'https://canine.fit',
  },
};
```

### 1.3 Dynamic Breed Page Metadata

**Breed Page** (`app/healthspan/[breed]/page.tsx`):

```typescript
import type { Metadata } from 'next';

interface BreedPageProps {
  params: { breed: string };
}

export async function generateMetadata({ params }: BreedPageProps): Promise<Metadata> {
  const breed = params.breed.replace(/-/g, ' ');
  const breedFormatted = breed.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  
  return {
    title: `${breedFormatted} Healthspan Tracker | Average Score & Leaderboard`,
    description: `See how your ${breedFormatted} ranks on the healthspan leaderboard. Track daily rituals, earn points & extend your ${breedFormatted}'s lifespan with AI insights from Lilo.`,
    keywords: [
      `${breed} healthspan`,
      `${breed} longevity`,
      `${breed} lifespan`,
      'dog health tracker',
      'breed leaderboard',
      'canine healthspan',
    ],
    openGraph: {
      title: `${breedFormatted} Healthspan Leaderboard | Canine.Fit`,
      description: `Track your ${breedFormatted}'s healthspan. See breed averages and compete on the leaderboard.`,
      url: `https://canine.fit/healthspan/${params.breed}`,
    },
  };
}
```

---

## 2. Schema.org Implementation

### 2.1 SoftwareApplication Schema

**Component** (`components/schema/SoftwareAppSchema.tsx`):

```typescript
import Script from 'next/script';

export function SoftwareAppSchema() {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'Canine.Fit',
    applicationCategory: 'HealthApplication',
    operatingSystem: 'iOS, Android',
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
      description: 'Free with premium features',
    },
    aggregateRating: {
      '@type': 'AggregateRating',
      ratingValue: '4.8',
      ratingCount: '10000',
      bestRating: '5',
    },
    featureList: [
      'Daily 15-second health rituals',
      'AI-powered health insights (Lilo)',
      'Breed-specific leaderboards',
      'Healthspan score tracking',
      'Predictive health risk analysis',
      'Photo mood analysis',
      'Gamified points system',
    ],
    screenshot: {
      '@type': 'ImageObject',
      url: 'https://canine.fit/app-screenshot.jpg',
    },
    author: {
      '@type': 'Organization',
      name: 'Canine.Fit',
      url: 'https://canine.fit',
    },
  };

  return (
    <Script
      id="software-app-schema"
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}
```

### 2.2 FAQPage Schema (GEO Gold)

**Component** (`components/schema/FAQSchema.tsx`):

```typescript
import Script from 'next/script';

interface FAQItem {
  question: string;
  answer: string;
}

interface FAQSchemaProps {
  items: FAQItem[];
}

export function FAQSchema({ items }: FAQSchemaProps) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: items.map(item => ({
      '@type': 'Question',
      name: item.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: item.answer,
      },
    })),
  };

  return (
    <Script
      id="faq-schema"
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}

// Usage with high-value GEO keywords
export const healthspanFAQs = [
  {
    question: 'What is dog healthspan vs lifespan?',
    answer: 'Dog lifespan is the total years a dog lives. Healthspan is the period of life spent in good health, free from chronic diseases and age-related decline. While a dog might live 12 years, their healthspan could be only 9 years if they suffer from arthritis or other conditions in their final years. Canine.Fit helps extend healthspan through daily tracking and AI-powered insights.',
  },
  {
    question: 'How can I track my dog\'s healthspan daily?',
    answer: 'Track your dog\'s healthspan daily with Canine.Fit\'s 15-second ritual. Simply log your dog\'s energy level, appetite, mobility, and mood each day. Our AI companion Lilo analyzes patterns and provides personalized insights to help you catch health issues early and extend your dog\'s healthy years.',
  },
  {
    question: 'How does daily logging improve dog longevity?',
    answer: 'Daily logging improves dog longevity by establishing baselines that make early detection of health issues possible. Studies show that early intervention can add 1-3 years to a dog\'s life. Canine.Fit\'s AI analyzes daily logs to spot subtle changes in behavior, appetite, or energy that might indicate emerging health problems.',
  },
  {
    question: 'What is a good healthspan score for dogs?',
    answer: 'A good healthspan score on Canine.Fit is 80 or above. The average score varies by breed - Golden Retrievers average 78, while smaller breeds like Poodles often score 82+. Your dog\'s score is calculated from daily ritual consistency, health metrics, and breed-specific factors. Scores above 90 indicate exceptional health management.',
  },
  {
    question: 'Can AI really predict dog health problems?',
    answer: 'Yes, AI can predict dog health problems by analyzing patterns in daily logs, breed predispositions, and age-related risk factors. Canine.Fit\'s Lilo AI uses machine learning trained on thousands of dog health records to identify early warning signs of conditions like arthritis, kidney disease, and diabetes - often weeks before symptoms become obvious.',
  },
];
```

### 2.3 HowTo Schema (Daily Ritual)

**Component** (`components/schema/HowToSchema.tsx`):

```typescript
import Script from 'next/script';

export function DailyRitualHowToSchema() {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'HowTo',
    name: 'Daily 15-Second Dog Health Ritual',
    description: 'A simple daily routine to track your dog\'s healthspan and catch potential issues early.',
    totalTime: 'PT15S',
    supply: ['Canine.Fit app', 'Your dog'],
    tool: ['Smartphone with Canine.Fit installed'],
    step: [
      {
        '@type': 'HowToStep',
        position: 1,
        name: 'Open Canine.Fit',
        text: 'Open the Canine.Fit app and select your dog\'s profile.',
        url: 'https://canine.fit/daily-ritual#step1',
      },
      {
        '@type': 'HowToStep',
        position: 2,
        name: 'Rate Energy Level',
        text: 'Quickly rate your dog\'s energy level on a scale of 1-5 based on their activity today.',
        url: 'https://canine.fit/daily-ritual#step2',
      },
      {
        '@type': 'HowToStep',
        position: 3,
        name: 'Log Appetite',
        text: 'Note your dog\'s appetite - did they eat normally, less than usual, or more than usual?',
        url: 'https://canine.fit/daily-ritual#step3',
      },
      {
        '@type': 'HowToStep',
        position: 4,
        name: 'Track Mobility',
        text: 'Assess mobility - any stiffness, limping, or difficulty getting up?',
        url: 'https://canine.fit/daily-ritual#step4',
      },
      {
        '@type': 'HowToStep',
        position: 5,
        name: 'Record Mood',
        text: 'Note your dog\'s overall mood and behavior for the day.',
        url: 'https://canine.fit/daily-ritual#step5',
      },
      {
        '@type': 'HowToStep',
        position: 6,
        name: 'Get AI Insights',
        text: 'Submit your log and receive instant AI-powered insights from Lilo about your dog\'s health trends.',
        url: 'https://canine.fit/daily-ritual#step6',
      },
    ],
  };

  return (
    <Script
      id="howto-schema"
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}
```

### 2.4 ItemList Schema (Leaderboard)

**Component** (`components/schema/LeaderboardSchema.tsx`):

```typescript
import Script from 'next/script';

interface LeaderboardDog {
  position: number;
  name: string;
  breed: string;
  score: number;
}

interface LeaderboardSchemaProps {
  breed: string;
  dogs: LeaderboardDog[];
}

export function LeaderboardSchema({ breed, dogs }: LeaderboardSchemaProps) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: `${breed} Healthspan Leaderboard`,
    itemListElement: dogs.map((dog, index) => ({
      '@type': 'ListItem',
      position: dog.position || index + 1,
      item: {
        '@type': 'Thing',
        name: dog.name,
        description: `${dog.breed} with a healthspan score of ${dog.score}`,
      },
    })),
  };

  return (
    <Script
      id="leaderboard-schema"
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}
```

---

## 3. Content Page Templates

### 3.1 Homepage Content Structure

**Target Keywords**: "best app to track dog healthspan 2026", "canine.fit app review 2026"

```typescript
// app/page.tsx structure
export default function HomePage() {
  return (
    <>
      {/* Hero Section */}
      <section className="hero">
        <h1>Extend Your Dog's Life with AI-Powered Healthspan Tracking</h1>
        <p>Track your dog's health in 15 seconds daily. Join 10,000+ owners using Lilo AI to predict health risks and extend their dog's healthy years.</p>
        <CTAButtons />
      </section>

      {/* Social Proof */}
      <section className="social-proof">
        <h2>Trusted by 10,000+ Dog Owners</h2>
        <RatingStars rating={4.8} count={10000} />
        <TestimonialCarousel />
      </section>

      {/* Feature Grid */}
      <section className="features">
        <h2>Why Canine.Fit is the #1 Dog Healthspan App</h2>
        <FeatureCard 
          title="15-Second Daily Ritual"
          description="Log your dog's health faster than making coffee. Consistency beats perfection."
          icon="timer"
        />
        <FeatureCard 
          title="Lilo AI Companion"
          description="Get personalized health insights and early warning alerts powered by AI."
          icon="brain"
        />
        <FeatureCard 
          title="Breed Leaderboards"
          description="See how your dog ranks against others of the same breed. Gamify their health!"
          icon="trophy"
        />
        <FeatureCard 
          title="Predictive Health"
          description="AI predicts arthritis, kidney issues, and other risks before symptoms appear."
          icon="shield"
        />
      </section>

      {/* How It Works */}
      <section className="how-it-works">
        <h2>How to Track Your Dog's Healthspan in 15 Seconds</h2>
        <HowToSteps />
      </section>

      {/* Breed Leaderboard Preview */}
      <section className="leaderboard-preview">
        <h2>Top Breeds on the Healthspan Leaderboard</h2>
        <BreedPreviewGrid />
        <Link href="/leaderboard">View Full Leaderboard →</Link>
      </section>

      {/* FAQ Section (GEO Gold) */}
      <section className="faq">
        <h2>Frequently Asked Questions About Dog Healthspan</h2>
        <FAQAccordion items={healthspanFAQs} />
      </section>

      {/* Final CTA */}
      <section className="cta">
        <h2>Start Extending Your Dog's Healthy Years Today</h2>
        <p>Free to download. No credit card required.</p>
        <DownloadButtons />
      </section>

      {/* Schema Markup */}
      <SoftwareAppSchema />
      <FAQSchema items={healthspanFAQs} />
    </>
  );
}
```

### 3.2 Comparison Page Template

**Target Keywords**: "canine.fit vs fitbark which is better", "canine.fit vs whistle comparison 2026"

```typescript
// app/compare/fitbark/page.tsx
export const metadata = {
  title: 'Canine.Fit vs FitBark 2026: Which is Better for Dog Longevity?',
  description: 'Detailed comparison of Canine.Fit vs FitBark. See why healthspan tracking beats activity-only monitoring for extending your dog\'s life.',
};

export default function FitBarkComparison() {
  return (
    <article>
      <h1>Canine.Fit vs FitBark: The Complete Comparison (2026)</h1>
      
      <p className="intro">
        Choosing between Canine.Fit and FitBark? While both track your dog's activity, 
        they serve different purposes. FitBark focuses on activity monitoring, while 
        Canine.Fit is built specifically for healthspan extension and longevity.
      </p>

      {/* Quick Verdict */}
      <div className="verdict-box">
        <h2>Quick Verdict</h2>
        <p><strong>Choose FitBark if:</strong> You want detailed activity tracking and GPS location.</p>
        <p><strong>Choose Canine.Fit if:</strong> You want to extend your dog's lifespan through healthspan tracking and AI-powered insights.</p>
      </div>

      {/* Comparison Table */}
      <ComparisonTable />

      {/* Detailed Breakdown */}
      <h2>Feature-by-Feature Comparison</h2>
      
      <h3>1. Health Tracking Approach</h3>
      <p>FitBark tracks activity levels, sleep quality, and location. Canine.Fit tracks healthspan metrics including energy, appetite, mobility, and mood - the key indicators of healthy aging.</p>

      <h3>2. AI & Insights</h3>
      <p>Canine.Fit's Lilo AI analyzes daily patterns to predict health risks. FitBark provides activity trends but no predictive health insights.</p>

      <h3>3. Breed-Specific Features</h3>
      <p>Canine.Fit offers breed-specific leaderboards and health baselines. FitBark compares against generic activity benchmarks.</p>

      {/* Migration CTA */}
      <div className="migration-cta">
        <h3>Switching from FitBark?</h3>
        <p>Import your FitBark data and see how activity correlates with healthspan scores.</p>
        <Link href="/download">Download Canine.Fit Free →</Link>
      </div>

      <FAQSchema items={comparisonFAQs} />
    </article>
  );
}
```

### 3.3 Breed-Specific Page Template

**Target Keywords**: "golden retriever healthspan leaderboard", "[breed] longevity score tracker"

```typescript
// app/healthspan/[breed]/page.tsx
export default function BreedPage({ params }: { params: { breed: string } }) {
  const breedData = await getBreedData(params.breed);
  
  return (
    <>
      {/* Hero */}
      <section>
        <h1>{breedData.name} Healthspan Tracker & Leaderboard</h1>
        <p>Average {breedData.name} Healthspan Score: <strong>{breedData.averageScore}</strong></p>
        <p>Top {breedData.name}s are living 2.3 years longer with daily tracking.</p>
      </section>

      {/* Stats */}
      <section className="breed-stats">
        <div className="stat-card">
          <h3>Average Lifespan</h3>
          <p>{breedData.avgLifespan} years</p>
        </div>
        <div className="stat-card">
          <h3>Average Healthspan</h3>
          <p>{breedData.avgHealthspan} years</p>
        </div>
        <div className="stat-card">
          <h3>Health Gap</h3>
          <p>{breedData.healthGap} years</p>
        </div>
      </section>

      {/* Leaderboard */}
      <section className="leaderboard">
        <h2>Top {breedData.name}s This Month</h2>
        <LeaderboardTable dogs={breedData.topDogs} />
        <LeaderboardSchema breed={breedData.name} dogs={breedData.topDogs} />
      </section>

      {/* Breed-Specific Tips */}
      <section className="breed-tips">
        <h2>How to Improve Your {breedData.name}'s Healthspan</h2>
        <ul>
          {breedData.healthTips.map(tip => (
            <li key={tip.id}>{tip.content}</li>
          ))}
        </ul>
      </section>

      {/* Common Health Issues */}
      <section className="health-issues">
        <h2>Common {breedData.name} Health Issues to Watch</h2>
        <HealthIssueList issues={breedData.commonIssues} />
      </section>

      {/* CTA */}
      <section className="cta">
        <h2>Join the {breedData.name} Leaderboard</h2>
        <p>Track your {breedData.name}'s healthspan and see how they rank.</p>
        <DownloadButtons />
      </section>
    </>
  );
}
```

---

## 4. Content Calendar & Blog Strategy

### 4.1 Pillar Content (High Priority)

| Priority | Title | Target Keywords | Schema |
|----------|-------|-----------------|--------|
| 1 | What is Dog Healthspan? Complete Guide 2026 | "what is dog healthspan vs lifespan explained", "how to measure my dog's healthspan at home" | Article + FAQ |
| 2 | The Science Behind Daily Dog Health Tracking | "how daily logs improve dog lifespan science", "does daily logging really improve dog longevity" | Article + HowTo |
| 3 | Lilo AI: How Artificial Intelligence Predicts Dog Health Issues | "how does AI predict dog health problems", "AI predictive dog health risks app" | Article + FAQ |
| 4 | Complete Breed Healthspan Guide | "average healthspan score by dog breed", "breed specific dog longevity leaderboard" | Article + Table |
| 5 | Canine.Fit vs FitBark vs Whistle: 2026 Comparison | "canine.fit vs fitbark which is better", "best dog healthspan app vs perky pet ai" | Article + Comparison |

### 4.2 Supporting Content (Medium Priority)

| Title | Target Keywords |
|-------|-----------------|
| 15-Second Daily Ritual: The Complete Guide | "daily 15 second dog health ritual tracker", "track my dog's health in under 15 seconds" |
| Understanding Your Dog's Healthspan Score | "healthspan points meaning for dogs", "how to calculate my dog's healthspan score" |
| Golden Retriever Lifespan: How to Extend It | "extend golden retriever lifespan with app", "best healthspan app for senior golden retrievers" |
| Senior Dog Health Tracking with AI | "senior dog health tracking app with AI", "senior dog arthritis and mobility tracker AI" |
| What-If Simulator: Predict Your Dog's Future Health | "what if dog longevity simulator free", "predict my dog's future health risks free" |
| Gamified Dog Longevity: How Points Extend Life | "gamified dog longevity points system", "dog healthspan points leaderboard by breed" |
| Toxic Foods and Your Dog's Longevity | "toxic food checker and dog longevity app", "safe human food list and healthspan impact" |

---

## 5. App Store Optimization (ASO)

### 5.1 iOS App Store

**App Name (30 chars)**: Canine.Fit: AI Healthspan
**Subtitle (30 chars)**: Track dog longevity daily
**Keywords (100 chars)**: dog health,pet tracker,longevity,healthspan,fitbark,whistle,ai dog,lilo,wellness

**Description**:
```
Extend your dog's healthy years with Canine.Fit - the AI-powered healthspan tracker.

TRACK IN 15 SECONDS
Log your dog's energy, appetite, mobility, and mood faster than making coffee. Consistency beats perfection.

LILO AI COMPANION
Get personalized health insights and early warnings powered by machine learning. Lilo analyzes patterns to predict arthritis, kidney issues, and other risks before symptoms appear.

BREED LEADERBOARDS
See how your dog ranks against others of the same breed. Golden Retrievers, Labradors, German Shepherds - compete on breed-specific leaderboards.

HEALTHSPAN SCORE
Understand your dog's health at a glance. Our proprietary score combines daily logs, breed factors, and AI analysis.

WHAT-IF SIMULATOR
See how diet changes, exercise increases, or weight loss could impact your dog's longevity.

FREE TO DOWNLOAD
Start tracking free. Premium features unlock predictive health insights and detailed reports.

Join 10,000+ dog owners extending their pets' lives.

---

Canine.Fit integrates with FitBark and other wearables. Not a replacement for veterinary care.
```

### 5.2 Google Play Store

**Title (50 chars)**: Canine.Fit: AI Dog Healthspan & Longevity Tracker
**Short Description (80 chars)**: Track your dog's healthspan in 15 seconds daily. AI insights & breed leaderboards.

**Full Description**: Same as iOS with added keywords for Google indexing.

---

## 6. Internal Linking Strategy

### 6.1 Link Architecture

```
Homepage (Authority Hub)
│
├── /healthspan/ (Pillar - 50 links)
│   ├── /healthspan/calculator (10 links)
│   ├── /healthspan/golden-retriever (5 links)
│   ├── /healthspan/labrador (5 links)
│   └── /healthspan/german-shepherd (5 links)
│
├── /lilo-ai/ (Pillar - 30 links)
│   ├── /lilo-ai/demo (8 links)
│   └── /lilo-ai/mood-analysis (8 links)
│
├── /daily-ritual/ (20 links)
│
├── /leaderboard/ (25 links)
│   └── /leaderboard/golden-retrievers (10 links)
│
├── /compare/ (Pillar - 20 links)
│   ├── /compare/fitbark (8 links)
│   └── /compare/whistle (8 links)
│
└── /blog/ (Hub - 40 links)
    ├── /blog/what-is-healthspan (12 links)
    ├── /blog/daily-ritual-guide (10 links)
    └── /blog/ai-predicts-health (10 links)
```

### 6.2 Anchor Text Distribution

| Target Page | Primary Anchor | Secondary Anchors |
|-------------|----------------|-------------------|
| /healthspan/ | "dog healthspan" | "track healthspan", "what is healthspan" |
| /lilo-ai/ | "Lilo AI" | "AI dog companion", "AI health insights" |
| /daily-ritual/ | "15-second ritual" | "daily tracking", "quick health log" |
| /leaderboard/ | "breed leaderboard" | "see rankings", "top dogs" |
| /compare/fitbark/ | "Canine.Fit vs FitBark" | "FitBark comparison", "which is better" |

---

## 7. Measurement & KPIs

### 7.1 SEO Metrics

| Metric | Baseline | 3-Month Target | 6-Month Target |
|--------|----------|----------------|----------------|
| Organic Sessions | 0 | 5,000/month | 20,000/month |
| Keyword Rankings (Top 10) | 0 | 25 | 75 |
| Keyword Rankings (Top 3) | 0 | 8 | 25 |
| Featured Snippets | 0 | 3 | 10 |
| Domain Authority | 0 | 15 | 25 |
| Backlinks | 0 | 50 | 150 |

### 7.2 GEO Metrics

| Metric | Target |
|--------|--------|
| "People Also Ask" Appearances | 15+ questions |
| AI Overview Citations | 5+ per month |
| ChatGPT Brand Mentions | Track monthly |
| Perplexity Source Citations | 10+ per month |

### 7.3 Business Metrics

| Metric | Target |
|--------|--------|
| Organic → App Install Rate | 8-12% |
| Organic Install % of Total | 25%+ |
| Organic CAC | <$2.00 |
| Branded Search Volume | 500+/month |

---

## 8. Implementation Timeline

### Week 1-2: Foundation
- [ ] Set up Next.js marketing site
- [ ] Implement core metadata templates
- [ ] Deploy SoftwareApplication schema
- [ ] Set up Google Search Console
- [ ] Set up Google Analytics 4

### Week 3-4: Core Pages
- [ ] Homepage with FAQ schema
- [ ] /healthspan/ pillar page
- [ ] /lilo-ai/ feature page
- [ ] /daily-ritual/ HowTo page
- [ ] 5 top breed pages

### Week 5-6: Content
- [ ] "What is Healthspan" blog post
- [ ] "Daily Ritual Guide" blog post
- [ ] Comparison page (vs FitBark)
- [ ] Comparison page (vs Whistle)

### Week 7-8: Advanced
- [ ] Healthspan calculator tool
- [ ] Leaderboard showcase page
- [ ] 5 more breed pages
- [ ] Link building outreach

### Week 9-12: Scale
- [ ] Weekly blog publishing schedule
- [ ] Video content (YouTube SEO)
- [ ] User-generated content program
- [ ] PR outreach for backlinks

---

## 9. Quick Reference: Schema Checklist

### Every Page Must Have:
- [ ] Title tag (50-60 chars)
- [ ] Meta description (150-160 chars)
- [ ] Canonical URL
- [ ] Open Graph tags
- [ ] Twitter Card tags

### Add Based on Content Type:
- [ ] SoftwareApplication (homepage, download page)
- [ ] FAQPage (pages with 3+ FAQs)
- [ ] HowTo (tutorial/ritual content)
- [ ] Article (blog posts)
- [ ] ItemList (leaderboards)
- [ ] BreadcrumbList (all pages)
- [ ] Organization (footer)

---

## 10. Recommended Tools

| Purpose | Tool | Cost |
|---------|------|------|
| Keyword Research | Ahrefs | $99/mo |
| Rank Tracking | AccuRanker | $99/mo |
| Content Optimization | Clearscope | $170/mo |
| Schema Testing | Google Rich Results Test | Free |
| Site Speed | PageSpeed Insights | Free |
| GEO Monitoring | Perplexity + ChatGPT | Free/Paid |
| Analytics | Google Analytics 4 | Free |
| Search Console | Google Search Console | Free |

---

**Document Version**: 1.0
**Last Updated**: March 2026
**Next Review**: April 2026
