import type { Metadata } from 'next';
import React from 'react';
import './globals.css';
import { SoftwareAppSchema } from '@/components/schema/SoftwareAppSchema';
import { OrganizationSchema } from '@/components/schema/OrganizationSchema';

export const metadata: Metadata = {
  metadataBase: new URL('https://canine.fit'),
  title: {
    default: 'Canine.Fit | AI Dog Healthspan Tracker - Extend Your Dog\'s Life',
    template: '%s | Canine.Fit',
  },
  description: 'Track your dog\'s healthspan in 15 seconds daily. AI-powered insights, breed leaderboards & personalized longevity scores. Join 10,000+ dog owners extending their pets\' lives.',
  keywords: [
    'dog healthspan',
    'dog longevity',
    'pet health tracker',
    'AI dog companion',
    'Lilo AI',
    'dog wellness app',
    'daily dog health ritual',
    'breed leaderboard',
    'predictive dog health',
    'extend dog lifespan',
  ],
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
  alternates: {
    canonical: 'https://canine.fit',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <SoftwareAppSchema />
        <OrganizationSchema />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
