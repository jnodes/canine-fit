import React from 'react';
import { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Privacy Policy',
  description: 'Canine.Fit privacy policy - How we collect, use, and protect your data.',
};

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-background py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl sm:text-4xl font-bold text-white mb-8">Privacy Policy</h1>
        <p className="text-text-secondary mb-8">Last updated: March 2026</p>
        
        <div className="space-y-8 text-text-secondary">
          <section>
            <h2 className="text-xl font-semibold text-white mb-4">1. Information We Collect</h2>
            <p className="mb-4">Canine.Fit collects the following information to provide our dog healthspan tracking services:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Account Information:</strong> Name, email address, and password (hashed via Supabase Auth)</li>
              <li><strong>Dog Profiles:</strong> Name, breed, date of birth, weight, sex, and activity level</li>
              <li><strong>Health Data:</strong> Daily mood, exercise level, nutrition quality, and notes you log</li>
              <li><strong>Photos:</strong> Optional dog photos for mood analysis (processed by AI, not stored permanently)</li>
              <li><strong>Payment Information:</strong> Processed securely via Stripe - we never store card numbers</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">2. How We Use Your Information</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>Provide personalized healthspan tracking and AI insights for your dog</li>
              <li>Generate breed-specific leaderboards and comparisons</li>
              <li>Process subscription payments and manage your account</li>
              <li>Send important updates about your account and our services</li>
              <li>Improve our AI models and service quality (anonymized data)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">3. AI Processing Disclosure</h2>
            <p className="mb-4">Canine.Fit uses artificial intelligence (OpenAI and Google Gemini) to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Analyze your dog's health patterns and generate insights</li>
              <li>Provide predictive health risk assessments</li>
              <li>Analyze photos for mood detection</li>
            </ul>
            <p className="mt-4">Your dog's health data is sent to these third-party AI services for processing. We do not store the AI responses permanently. AI insights are for informational purposes only and are not veterinary advice.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">4. Data Storage and Security</h2>
            <p className="mb-4">Your data is stored securely using:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Supabase:</strong> Primary database with Row Level Security (RLS) ensuring you can only access your own data</li>
              <li><strong>Encryption:</strong> All data transmitted via HTTPS/TLS 1.3</li>
              <li><strong>Authentication:</strong> Secure authentication via Supabase Auth with JWT tokens</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">5. Your Rights (GDPR)</h2>
            <p className="mb-4">Under the General Data Protection Regulation, you have the right to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Access (Article 15):</strong> Request a copy of your personal data via the app or API</li>
              <li><strong>Rectification (Article 16):</strong> Update or correct your data through the app</li>
              <li><strong>Erasure (Article 17):</strong> Delete your account and all associated data</li>
              <li><strong>Data Portability (Article 20):</strong> Export your data in JSON format</li>
              <li><strong>Object (Article 21):</strong> Object to AI processing of your data</li>
            </ul>
            <p className="mt-4">To exercise these rights, use the in-app settings or contact us at privacy@canine.fit</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">6. Third-Party Services</h2>
            <p className="mb-4">We use the following third-party services:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Supabase:</strong> Database and authentication (supabase.com/privacy)</li>
              <li><strong>Stripe:</strong> Payment processing (stripe.com/privacy)</li>
              <li><strong>OpenAI:</strong> AI insights generation (openai.com/privacy)</li>
              <li><strong>Google (Gemini):</strong> AI photo analysis (policies.google.com/privacy)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">7. Data Retention</h2>
            <p>We retain your data only as long as your account is active. Upon account deletion, all personal data is permanently removed within 30 days, including all dog profiles, health logs, and AI-generated reports.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">8. Children's Privacy</h2>
            <p>Canine.Fit is not intended for children under 13. We do not knowingly collect personal information from children under 13. If you believe we have collected information from a child under 13, contact us immediately.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">9. Contact Us</h2>
            <p>For privacy-related questions or to exercise your rights:</p>
            <ul className="list-none mt-2 space-y-1">
              <li>Email: privacy@canine.fit</li>
              <li>Address: Canine.Fit, Inc.</li>
            </ul>
          </section>

          <div className="pt-8 border-t border-border">
            <Link href="/" className="text-primary hover:text-primary-light transition-colors">
              ← Back to Home
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
