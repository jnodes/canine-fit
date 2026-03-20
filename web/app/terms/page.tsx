import React from 'react';
import { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Terms of Service',
  description: 'Canine.Fit terms of service - Usage agreement and policies.',
};

export default function TermsPage() {
  return (
    <main className="min-h-screen bg-background py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl sm:text-4xl font-bold text-white mb-8">Terms of Service</h1>
        <p className="text-text-secondary mb-8">Last updated: March 2026</p>
        
        <div className="space-y-8 text-text-secondary">
          <section>
            <h2 className="text-xl font-semibold text-white mb-4">1. Acceptance of Terms</h2>
            <p>By downloading, accessing, or using Canine.Fit ("the Service"), you agree to be bound by these Terms of Service. If you do not agree to these terms, do not use the Service.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">2. Description of Service</h2>
            <p className="mb-4">Canine.Fit is a dog healthspan tracking application that provides:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Daily health tracking for dogs</li>
              <li>AI-powered health insights and predictions via Lilo AI</li>
              <li>Breed-specific leaderboards and health comparisons</li>
              <li>Healthspan scoring and trend analysis</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">3. Medical Disclaimer</h2>
            <div className="bg-warning/10 border border-warning/30 rounded-xl p-4 mb-4">
              <p className="text-warning font-medium mb-2">⚠️ Important Notice</p>
              <p>Canine.Fit and Lilo AI provide health insights for informational purposes only. The Service is NOT a substitute for professional veterinary advice, diagnosis, or treatment. Always consult a qualified veterinarian for any health concerns regarding your dog.</p>
            </div>
            <p>Healthspan scores and AI predictions are estimates based on the data you provide and should not be used as the sole basis for medical decisions.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">4. User Accounts</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>You must provide accurate and complete information when creating an account</li>
              <li>You are responsible for maintaining the security of your account credentials</li>
              <li>You must be at least 13 years old to use the Service</li>
              <li>You may create multiple dog profiles under a single account</li>
              <li>Free accounts are limited to 2 dog profiles; premium accounts have unlimited profiles</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">5. Subscription and Payments</h2>
            <p className="mb-4">Canine.Fit offers both free and premium subscription tiers:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Free Tier:</strong> Basic health tracking, limited AI insights, 2 dog profiles</li>
              <li><strong>Premium Tier:</strong> Full AI insights, unlimited dogs, advanced predictions, detailed reports</li>
            </ul>
            <p className="mt-4">Subscriptions are billed monthly or annually through Stripe. You may cancel at any time; premium features remain active until the end of your billing period.</p>
            <p className="mt-2">Refunds are available within 7 days of purchase for annual plans, or within 48 hours for monthly plans. Contact support@canine.fit for refund requests.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">6. Acceptable Use</h2>
            <p className="mb-4">You agree NOT to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Use the Service for any illegal purpose</li>
              <li>Upload malicious content or attempt to compromise our systems</li>
              <li>Create fake dog profiles to manipulate leaderboards</li>
              <li>Share your account credentials with others</li>
              <li>Use the Service to generate AI content for non-dog-related purposes</li>
              <li>Attempt to reverse engineer or extract our AI models</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">7. Intellectual Property</h2>
            <p className="mb-4">Canine.Fit and its associated logos, designs, and software are the property of Canine.Fit, Inc. The "Lilo AI" brand and character are trademarks of Canine.Fit, Inc.</p>
            <p>You retain ownership of the data you input (dog profiles, health logs, photos). By using the Service, you grant us a license to process this data to provide the Service.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">8. Limitation of Liability</h2>
            <p className="mb-4">TO THE MAXIMUM EXTENT PERMITTED BY LAW:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Canine.Fit is provided "as is" without warranties of any kind</li>
              <li>We are not liable for any decisions made based on AI insights or healthspan scores</li>
              <li>We are not liable for any veterinary outcomes or health issues with your dog</li>
              <li>Our total liability shall not exceed the amount you paid in the past 12 months</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">9. Termination</h2>
            <p>You may delete your account at any time through the app or by contacting us. Upon termination:</p>
            <ul className="list-disc pl-6 mt-2 space-y-2">
              <li>All your data will be permanently deleted within 30 days</li>
              <li>Any active subscription will be cancelled</li>
              <li>No refunds are provided for partial subscription periods (unless within refund window)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">10. Changes to Terms</h2>
            <p>We may update these Terms from time to time. Significant changes will be notified via email or in-app notification. Continued use after changes constitutes acceptance of the new terms.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">11. Governing Law</h2>
            <p>These Terms are governed by the laws of the United States. Any disputes shall be resolved through binding arbitration in accordance with the Federal Arbitration Act.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">12. Contact Us</h2>
            <p>For questions about these Terms:</p>
            <ul className="list-none mt-2 space-y-1">
              <li>Email: legal@canine.fit</li>
              <li>Support: support@canine.fit</li>
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
