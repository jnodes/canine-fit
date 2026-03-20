import React from 'react';

export function OrganizationSchema() {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'Canine.Fit',
    url: 'https://canine.fit',
    logo: 'https://canine.fit/logo.png',
    sameAs: [
      'https://twitter.com/caninefit',
      'https://facebook.com/caninefit',
      'https://instagram.com/caninefit',
    ],
    description: 'AI-powered dog healthspan tracking app helping owners extend their pets\' healthy years.',
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}
