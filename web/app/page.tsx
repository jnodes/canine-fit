'use client';

import React from 'react';
import { 
  Timer, 
  Brain, 
  Trophy, 
  Shield, 
  Flame, 
  Star, 
  CheckCircle,
  TrendingUp,
  Apple,
  Activity,
  PawPrint,
  ChevronRight,
  Download
} from 'lucide-react';
import { GradientButton } from '@/components/ui/GradientButton';
import { FeatureCard } from '@/components/ui/FeatureCard';
import { StatsCard } from '@/components/ui/StatsCard';
import { FAQItem } from '@/components/ui/FAQItem';
import { FAQSchema, healthspanFAQs } from '@/components/schema/FAQSchema';

export default function HomePage() {
  const features = [
    {
      icon: Timer,
      title: '15-Second Daily Ritual',
      description: 'Log your dog\'s health faster than making coffee. Consistency beats perfection.',
      iconColor: '#FF6B00',
    },
    {
      icon: Brain,
      title: 'Lilo AI Companion',
      description: 'Get personalized health insights and early warning alerts powered by AI.',
      iconColor: '#00BFA5',
    },
    {
      icon: Trophy,
      title: 'Breed Leaderboards',
      description: 'See how your dog ranks against others of the same breed. Gamify their health!',
      iconColor: '#F59E0B',
    },
    {
      icon: Shield,
      title: 'Predictive Health',
      description: 'AI predicts arthritis, kidney issues, and other risks before symptoms appear.',
      iconColor: '#10B981',
    },
  ];

  const stats = [
    { icon: Flame, label: 'Active Users', value: '10K+', color: '#FF6B00' },
    { icon: Star, label: 'App Rating', value: '4.8', color: '#00BFA5' },
    { icon: Trophy, label: 'Dogs Tracked', value: '25K+', color: '#F59E0B' },
    { icon: CheckCircle, label: 'Rituals Logged', value: '1M+', color: '#10B981' },
  ];

  const breeds = [
    { name: 'Golden Retriever', score: 78, rank: 1 },
    { name: 'Labrador', score: 77, rank: 2 },
    { name: 'German Shepherd', score: 76, rank: 3 },
    { name: 'Poodle', score: 82, rank: 4 },
  ];

  return (
    <main className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-primary-light flex items-center justify-center">
                <PawPrint className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold text-white">Canine.Fit</span>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-text-secondary hover:text-white transition-colors text-sm">Features</a>
              <a href="#leaderboard" className="text-text-secondary hover:text-white transition-colors text-sm">Leaderboard</a>
              <a href="#faq" className="text-text-secondary hover:text-white transition-colors text-sm">FAQ</a>
              <GradientButton size="sm" href="#download">Download App</GradientButton>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center animate-fade-in">
            <div className="inline-flex items-center gap-2 bg-card px-4 py-2 rounded-full mb-6 border border-border/50">
              <span className="w-2 h-2 bg-success rounded-full animate-pulse"></span>
              <span className="text-text-secondary text-sm">Now tracking 25,000+ dogs worldwide</span>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white mb-6 leading-tight">
              Extend Your Dog's Life with{' '}
              <span className="gradient-text">AI-Powered</span>{' '}
              Healthspan Tracking
            </h1>
            <p className="text-text-secondary text-lg sm:text-xl max-w-2xl mx-auto mb-10">
              Track your dog's health in 15 seconds daily. Join 10,000+ owners using Lilo AI to predict health risks and extend their dog's healthy years.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <GradientButton size="lg" href="#download">
                <Download className="w-5 h-5 mr-2" />
                Download Free
              </GradientButton>
              <GradientButton variant="secondary" size="lg" href="#features">
                Learn More
                <ChevronRight className="w-5 h-5 ml-2" />
              </GradientButton>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-wrap gap-4">
            {stats.map((stat, index) => (
              <StatsCard key={index} {...stat} />
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Why Canine.Fit is the #1 Dog Healthspan App
            </h2>
            <p className="text-text-secondary max-w-2xl mx-auto">
              Unlike activity-only trackers, we focus on what really matters - extending your dog's healthy years.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {features.map((feature, index) => (
              <FeatureCard key={index} {...feature} />
            ))}
          </div>
        </div>
      </section>

      {/* Healthspan Score Card Demo */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-gradient-to-br from-primary to-primary-light rounded-3xl p-8 sm:p-12">
            <div className="flex items-center gap-4 mb-8">
              <div className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center">
                <PawPrint className="w-7 h-7 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white">Max</h3>
                <p className="text-white/80">Golden Retriever • 5 years</p>
              </div>
            </div>
            <div className="bg-white/15 rounded-2xl p-6">
              <div className="mb-4">
                <p className="text-white/80 text-sm mb-1">Healthspan Score</p>
                <div className="flex items-end gap-3">
                  <span className="text-6xl font-extrabold text-white">88</span>
                  <div className="flex items-center gap-1 bg-success/20 px-3 py-1 rounded-full mb-2">
                    <TrendingUp className="w-4 h-4 text-success" />
                    <span className="text-success text-sm font-semibold">+3</span>
                  </div>
                </div>
              </div>
              <div className="h-1.5 bg-white/30 rounded-full mb-4">
                <div className="h-full w-[88%] bg-white rounded-full"></div>
              </div>
              <div className="flex items-center gap-2 pt-4 border-t border-white/20">
                <Trophy className="w-5 h-5 text-yellow-400" />
                <span className="text-white font-semibold">#42 in Golden Retrievers</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Daily Ritual CTA */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-gradient-to-r from-secondary to-secondary-light rounded-3xl p-8 sm:p-12">
            <div className="flex flex-col sm:flex-row items-center gap-6">
              <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
                <CheckCircle className="w-8 h-8 text-white" />
              </div>
              <div className="flex-1 text-center sm:text-left">
                <h3 className="text-2xl font-bold text-white mb-2">Complete Your Daily Ritual</h3>
                <p className="text-white/90">Log your dog's health in under 15 seconds. Consistency is the key to longevity.</p>
              </div>
              <GradientButton variant="primary" className="bg-white text-secondary hover:bg-white/90 flex-shrink-0">
                Start Tracking
              </GradientButton>
            </div>
          </div>
        </div>
      </section>

      {/* Leaderboard Preview */}
      <section id="leaderboard" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Top Breeds on the Healthspan Leaderboard
            </h2>
            <p className="text-text-secondary">
              See how different breeds compare and find your dog's ranking.
            </p>
          </div>
          <div className="bg-card rounded-3xl p-6 border border-border/50">
            {breeds.map((breed, index) => (
              <div 
                key={index}
                className="flex items-center justify-between py-4 border-b border-border/50 last:border-0"
              >
                <div className="flex items-center gap-4">
                  <span className="text-text-secondary font-bold w-6">{breed.rank}</span>
                  <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                    <PawPrint className="w-5 h-5 text-primary" />
                  </div>
                  <span className="text-white font-semibold">{breed.name}</span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className="text-white font-bold text-lg">{breed.score}</span>
                    <p className="text-text-secondary text-xs">avg score</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-text-secondary" />
                </div>
              </div>
            ))}
          </div>
          <div className="text-center mt-8">
            <GradientButton variant="secondary" href="/leaderboard">
              View Full Leaderboard
              <ChevronRight className="w-5 h-5 ml-2" />
            </GradientButton>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              How to Track Your Dog's Healthspan
            </h2>
            <p className="text-text-secondary">
              Four simple steps to start extending your dog's healthy years.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: Download, title: 'Download', desc: 'Get the app free on iOS or Android' },
              { icon: PawPrint, title: 'Add Your Dog', desc: 'Create a profile with breed and age' },
              { icon: Activity, title: 'Daily Log', desc: '15-second ritual every day' },
              { icon: Brain, title: 'Get Insights', desc: 'AI-powered health recommendations' },
            ].map((step, index) => (
              <div key={index} className="text-center">
                <div className="w-16 h-16 rounded-2xl bg-card flex items-center justify-center mx-auto mb-4 border border-border/50">
                  <step.icon className="w-8 h-8 text-primary" />
                </div>
                <h3 className="text-white font-bold mb-2">{step.title}</h3>
                <p className="text-text-secondary text-sm">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Frequently Asked Questions
            </h2>
            <p className="text-text-secondary">
              Everything you need to know about dog healthspan tracking.
            </p>
          </div>
          <div className="space-y-4">
            {healthspanFAQs.map((faq, index) => (
              <FAQItem key={index} question={faq.question} answer={faq.answer} />
            ))}
          </div>
          <FAQSchema items={healthspanFAQs} />
        </div>
      </section>

      {/* Final CTA */}
      <section id="download" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="bg-card rounded-3xl p-8 sm:p-12 border border-border/50">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Start Extending Your Dog's Healthy Years Today
            </h2>
            <p className="text-text-secondary text-lg mb-8">
              Free to download. No credit card required. Join 10,000+ dog owners already tracking their pet's healthspan.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <a 
                href="https://apps.apple.com/app/canine-fit" 
                className="flex items-center gap-3 bg-white text-background px-6 py-3 rounded-xl font-semibold hover:bg-white/90 transition-colors"
              >
                <Apple className="w-6 h-6" />
                <div className="text-left">
                  <p className="text-xs text-gray-600">Download on the</p>
                  <p className="text-sm font-bold">App Store</p>
                </div>
              </a>
              <a 
                href="https://play.google.com/store/apps/details?id=com.caninefit.app" 
                className="flex items-center gap-3 bg-card-light text-white px-6 py-3 rounded-xl font-semibold border border-border hover:bg-card-light/80 transition-colors"
              >
                <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M3 20.5V3.5C3 2.91 3.34 2.39 3.84 2.15L13.69 12L3.84 21.85C3.34 21.6 3 21.09 3 20.5ZM16.81 15.12L6.05 21.34L14.54 12.85L16.81 15.12ZM20.16 10.81C20.5 11.08 20.75 11.5 20.75 12C20.75 12.5 20.53 12.9 20.18 13.18L17.89 14.5L15.39 12L17.89 9.5L20.16 10.81ZM6.05 2.66L16.81 8.88L14.54 11.15L6.05 2.66Z"/>
                </svg>
                <div className="text-left">
                  <p className="text-xs text-text-secondary">Get it on</p>
                  <p className="text-sm font-bold">Google Play</p>
                </div>
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 sm:px-6 lg:px-8 border-t border-border">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-primary-light flex items-center justify-center">
                <PawPrint className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold text-white">Canine.Fit</span>
            </div>
            <div className="flex items-center gap-6">
              <a href="/privacy" className="text-text-secondary hover:text-white transition-colors text-sm">Privacy</a>
              <a href="/terms" className="text-text-secondary hover:text-white transition-colors text-sm">Terms</a>
              <a href="/contact" className="text-text-secondary hover:text-white transition-colors text-sm">Contact</a>
            </div>
            <p className="text-text-secondary text-sm">
              © 2026 Canine.Fit. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
