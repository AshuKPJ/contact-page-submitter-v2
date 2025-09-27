import React, { useState } from 'react';
import {
  HelpCircle, Search, BookOpen, MessageCircle, Mail, Phone,
  ChevronRight, ChevronDown, PlayCircle, FileText, Star,
  Clock, CheckCircle, ArrowRight, ExternalLink, Video,
  Download, Users, Zap, Shield, Target, Globe, Settings,
  AlertCircle, Info, Lightbulb, Heart, Award, TrendingUp
} from 'lucide-react';

const HelpSupportPage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [expandedFaq, setExpandedFaq] = useState(null);

  const quickActions = [
    {
      title: 'Getting Started',
      description: 'Learn the basics of Contact Page Submitter',
      icon: PlayCircle,
      color: 'bg-green-100 text-green-600',
      action: () => {}
    },
    {
      title: 'Create Your First Campaign',
      description: 'Step-by-step guide to launch your outreach',
      icon: Zap,
      color: 'bg-blue-100 text-blue-600',
      action: () => {}
    },
    {
      title: 'Contact Support',
      description: 'Get help from our expert team',
      icon: MessageCircle,
      color: 'bg-purple-100 text-purple-600',
      action: () => {}
    },
    {
      title: 'API Documentation',
      description: 'Technical guides for developers',
      icon: FileText,
      color: 'bg-orange-100 text-orange-600',
      action: () => {}
    }
  ];

  const categories = [
    { id: 'all', name: 'All Topics', count: 47 },
    { id: 'getting-started', name: 'Getting Started', count: 12 },
    { id: 'campaigns', name: 'Campaigns', count: 15 },
    { id: 'billing', name: 'Billing & Plans', count: 8 },
    { id: 'technical', name: 'Technical Issues', count: 7 },
    { id: 'api', name: 'API & Integration', count: 5 }
  ];

  const faqs = [
    {
      category: 'getting-started',
      question: 'How do I get started with Contact Page Submitter?',
      answer: 'Getting started is easy! First, create your account and complete your profile setup. Then, prepare a CSV file with your target websites, create your first campaign with a personalized message, and launch it. Our system will automatically find contact forms and submit your messages.'
    },
    {
      category: 'campaigns',
      question: 'What file format should I use for uploading websites?',
      answer: 'We accept CSV files with columns for URL, company name, and any custom fields you want to use. The URL column is required. You can download our CSV template from the campaign creation page for the proper format.'
    },
    {
      category: 'campaigns',
      question: 'How many websites can I process in one campaign?',
      answer: 'The number depends on your plan. Starter plans allow up to 1,000 URLs per campaign, Professional plans up to 10,000, and Enterprise plans have no limits. You can always split large lists into multiple campaigns.'
    },
    {
      category: 'technical',
      question: 'What happens if a website doesn\'t have a contact form?',
      answer: 'Our intelligent fallback system automatically searches for email addresses on the page, including mailto links and contact information. If found, your message is sent directly to that email address instead.'
    },
    {
      category: 'campaigns',
      question: 'How does CAPTCHA solving work?',
      answer: 'We integrate with Death By Captcha, a professional CAPTCHA-solving service. When our system encounters a CAPTCHA, it\'s automatically solved using AI and human workers. This significantly improves success rates on protected websites.'
    },
    {
      category: 'billing',
      question: 'Can I change or cancel my subscription anytime?',
      answer: 'Yes! You can upgrade, downgrade, or cancel your subscription at any time from your account settings. Changes take effect immediately, and we provide prorated billing for upgrades and credits for downgrades.'
    },
    {
      category: 'technical',
      question: 'Why are some of my submissions failing?',
      answer: 'Common reasons include offline websites, broken contact forms, or extremely strict security measures. Our system automatically retries failed submissions and provides detailed error logs to help you understand issues.'
    },
    {
      category: 'api',
      question: 'Do you offer an API for developers?',
      answer: 'Yes! Our REST API allows you to programmatically create campaigns, upload URLs, check status, and retrieve results. Full documentation is available in your account dashboard under the API section.'
    },
    {
      category: 'billing',
      question: 'What payment methods do you accept?',
      answer: 'We accept all major credit cards (Visa, MasterCard, American Express, Discover) and PayPal. All payments are processed securely through Stripe with bank-level encryption.'
    },
    {
      category: 'campaigns',
      question: 'Can I track the success rate of my campaigns?',
      answer: 'Absolutely! Your dashboard provides real-time analytics including success rates, failure reasons, processing speed, and detailed logs. You can also export comprehensive reports for analysis.'
    }
  ];

  const tutorials = [
    {
      title: 'Setting Up Your First Campaign',
      duration: '5 min',
      type: 'video',
      description: 'Learn how to create and launch your first outreach campaign',
      thumbnail: '/api/placeholder/200/120',
      popular: true
    },
    {
      title: 'Writing Effective Outreach Messages',
      duration: '3 min',
      type: 'article',
      description: 'Best practices for crafting messages that get responses',
      thumbnail: '/api/placeholder/200/120',
      popular: true
    },
    {
      title: 'Understanding Success Rates and Analytics',
      duration: '4 min',
      type: 'video',
      description: 'How to interpret your campaign results and optimize performance',
      thumbnail: '/api/placeholder/200/120'
    },
    {
      title: 'Advanced CSV Formatting',
      duration: '6 min',
      type: 'article',
      description: 'Tips for preparing your contact lists for maximum success',
      thumbnail: '/api/placeholder/200/120'
    },
    {
      title: 'CAPTCHA Configuration and Troubleshooting',
      duration: '8 min',
      type: 'video',
      description: 'Setup and optimize CAPTCHA solving for better results',
      thumbnail: '/api/placeholder/200/120'
    },
    {
      title: 'API Integration Guide',
      duration: '12 min',
      type: 'article',
      description: 'Complete guide to integrating with our REST API',
      thumbnail: '/api/placeholder/200/120'
    }
  ];

  const filteredFaqs = faqs.filter(faq => {
    const matchesCategory = selectedCategory === 'all' || faq.category === selectedCategory;
    const matchesSearch = faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         faq.answer.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const supportOptions = [
    {
      title: 'Live Chat',
      description: 'Chat with our support team',
      availability: 'Available now',
      icon: MessageCircle,
      color: 'bg-green-100 text-green-600',
      available: true
    },
    {
      title: 'Email Support',
      description: 'Get detailed help via email',
      availability: 'Response within 2 hours',
      icon: Mail,
      color: 'bg-blue-100 text-blue-600',
      available: true
    },
    {
      title: 'Phone Support',
      description: 'Talk to an expert directly',
      availability: 'Business hours only',
      icon: Phone,
      color: 'bg-purple-100 text-purple-600',
      available: false
    },
    {
      title: 'Screen Sharing',
      description: 'Get personalized assistance',
      availability: 'Schedule a session',
      icon: Users,
      color: 'bg-orange-100 text-orange-600',
      available: true
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
        <div className="max-w-7xl mx-auto px-6 py-16 text-center">
          <h1 className="text-4xl font-bold mb-4">How can we help you?</h1>
          <p className="text-xl text-indigo-100 mb-8 max-w-2xl mx-auto">
            Find answers, get support, and learn how to make the most of Contact Page Submitter
          </p>
          
          {/* Search Bar */}
          <div className="max-w-2xl mx-auto relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search for help articles, guides, and answers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-6 py-4 text-gray-900 bg-white rounded-2xl shadow-lg focus:ring-4 focus:ring-indigo-300 focus:outline-none text-lg"
            />
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 -mt-8 mb-12">
          {quickActions.map((action, index) => {
            const Icon = action.icon;
            return (
              <div
                key={index}
                className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer hover:scale-105 border border-gray-100"
                onClick={action.action}
              >
                <div className={`inline-flex p-3 rounded-xl ${action.color} mb-4`}>
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{action.title}</h3>
                <p className="text-gray-600 text-sm mb-4">{action.description}</p>
                <div className="flex items-center text-indigo-600 text-sm font-medium">
                  Learn more <ArrowRight className="w-4 h-4 ml-1" />
                </div>
              </div>
            );
          })}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          {/* FAQ Section */}
          <div className="lg:col-span-2">
            <div className="mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">Frequently Asked Questions</h2>
              <p className="text-gray-600 mb-6">Find quick answers to common questions about using Contact Page Submitter</p>
              
              {/* Category Filter */}
              <div className="flex flex-wrap gap-2 mb-6">
                {categories.map(category => (
                  <button
                    key={category.id}
                    onClick={() => setSelectedCategory(category.id)}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                      selectedCategory === category.id
                        ? 'bg-indigo-100 text-indigo-700 border-2 border-indigo-200'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200 border-2 border-transparent'
                    }`}
                  >
                    {category.name} ({category.count})
                  </button>
                ))}
              </div>
            </div>

            {/* FAQ List */}
            <div className="space-y-4">
              {filteredFaqs.length === 0 ? (
                <div className="text-center py-12">
                  <HelpCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No FAQs found</h3>
                  <p className="text-gray-500">Try adjusting your search or category filter</p>
                </div>
              ) : (
                filteredFaqs.map((faq, index) => (
                  <div key={index} className="bg-white border border-gray-200 rounded-xl overflow-hidden hover:shadow-lg transition-shadow">
                    <button
                      onClick={() => setExpandedFaq(expandedFaq === index ? null : index)}
                      className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-gray-50 transition-colors"
                    >
                      <h3 className="text-lg font-medium text-gray-900 pr-4">{faq.question}</h3>
                      <div className="flex-shrink-0">
                        {expandedFaq === index ? (
                          <ChevronDown className="w-5 h-5 text-gray-500" />
                        ) : (
                          <ChevronRight className="w-5 h-5 text-gray-500" />
                        )}
                      </div>
                    </button>
                    {expandedFaq === index && (
                      <div className="px-6 pb-4 border-t bg-gray-50">
                        <p className="text-gray-700 leading-relaxed pt-4">{faq.answer}</p>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            {/* Contact Support */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-8 hover:shadow-lg transition-shadow">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Need More Help?</h3>
              <p className="text-gray-600 mb-6">Our support team is here to help you succeed</p>
              
              <div className="space-y-4">
                {supportOptions.map((option, index) => {
                  const Icon = option.icon;
                  return (
                    <div key={index} className={`p-4 rounded-xl border-2 ${option.available ? 'cursor-pointer hover:shadow-md' : 'opacity-60'} transition-all`}>
                      <div className="flex items-center gap-3 mb-2">
                        <div className={`p-2 rounded-lg ${option.color}`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-900">{option.title}</h4>
                          <p className="text-sm text-gray-500">{option.availability}</p>
                        </div>
                        {option.available && (
                          <ArrowRight className="w-4 h-4 text-gray-400" />
                        )}
                      </div>
                      <p className="text-sm text-gray-600">{option.description}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Popular Tutorials */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Popular Tutorials</h3>
              <div className="space-y-4">
                {tutorials.slice(0, 4).map((tutorial, index) => (
                  <div key={index} className="flex gap-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                    <div className="relative">
                      <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                        {tutorial.type === 'video' ? (
                          <Video className="w-6 h-6 text-white" />
                        ) : (
                          <FileText className="w-6 h-6 text-white" />
                        )}
                      </div>
                      {tutorial.popular && (
                        <div className="absolute -top-1 -right-1 w-4 h-4 bg-orange-500 rounded-full flex items-center justify-center">
                          <Star className="w-2 h-2 text-white fill-current" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-gray-900 text-sm leading-tight mb-1">
                        {tutorial.title}
                      </h4>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <Clock className="w-3 h-3" />
                        <span>{tutorial.duration}</span>
                        <span>•</span>
                        <span className="capitalize">{tutorial.type}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <button className="w-full mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center justify-center gap-2">
                <BookOpen className="w-4 h-4" />
                View All Tutorials
              </button>
            </div>
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl text-white p-8 text-center">
          <h2 className="text-2xl font-bold mb-4">Still need help?</h2>
          <p className="text-indigo-100 mb-6 max-w-2xl mx-auto">
            Our expert support team is standing by to help you get the most out of Contact Page Submitter
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="px-6 py-3 bg-white text-indigo-600 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
              Start Live Chat
            </button>
            <button className="px-6 py-3 bg-indigo-700 text-white rounded-lg font-semibold hover:bg-indigo-800 transition-colors">
              Send us an Email
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HelpSupportPage;