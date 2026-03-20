'use client';

import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';

interface FAQItemProps {
  question: string;
  answer: string;
}

export function FAQItem({ question, answer }: FAQItemProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="bg-card rounded-2xl border border-border/50 overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-5 text-left hover:bg-card-light/50 transition-colors"
      >
        <h3 className="text-white font-semibold text-base pr-4">{question}</h3>
        <ChevronDown 
          size={24} 
          className={`text-text-secondary flex-shrink-0 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>
      <div 
        className={`overflow-hidden transition-all duration-300 ${isOpen ? 'max-h-96' : 'max-h-0'}`}
      >
        <p className="text-text-secondary text-sm leading-relaxed px-5 pb-5">
          {answer}
        </p>
      </div>
    </div>
  );
}
