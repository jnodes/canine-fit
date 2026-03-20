import React from 'react';

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
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}
