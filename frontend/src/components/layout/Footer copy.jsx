// src/components/landing/Footer.jsx - Enhanced Modern Version

import React, { useState } from "react";
import { 
  Mail, Phone, MapPin, ArrowUpRight, Send, Heart, 
  Twitter, Linkedin, Facebook, Instagram, Github,
  Zap, Shield, Award, Users, Globe, Sparkles,
  ExternalLink, ChevronRight, Star, MessageCircle
} from "lucide-react";

const Footer = () => {
  const [email, setEmail] = useState("");
  const [subscribed, setSubscribed] = useState(false);

  const handleSubscribe = (e) => {
    e.preventDefault();
    if (email) {
      setSubscribed(true);
      setEmail("");
      setTimeout(() => setSubscribed(false), 3000);
    }
  };

  // Company stats for credibility
  const stats = [
    { label: "Messages Sent", value: "2.5M+", icon: Send },
    { label: "Happy Clients", value: "10K+", icon: Users },
    { label: "Success Rate", value: "88%", icon: Award },
    { label: "Countries", value: "50+", icon: Globe }
  ];

  // Social media links
  const socialLinks = [
    { name: "Twitter", icon: Twitter, href: "#", color: "hover:text-blue-400" },
    { name: "LinkedIn", icon: Linkedin, href: "#", color: "hover:text-blue-600" },
    { name: "Facebook", icon: Facebook, href: "#", color: "hover:text-blue-500" },
    { name: "Instagram", icon: Instagram, href: "#", color: "hover:text-pink-500" },
    { name: "GitHub", icon: Github, href: "#", color: "hover:text-gray-900" }
  ];

  // Navigation sections
  const footerSections = [
    {
      title: "Solutions",
      links: [
        { name: "Campaign Management", href: "#campaigns", description: "Automated outreach tools" },
        { name: "Analytics Dashboard", href: "#analytics", description: "Real-time insights" },
        { name: "Contact Forms", href: "#forms", description: "Smart form detection" },
        { name: "API Integration", href: "#api", description: "Developer resources" }
      ]
    },
    {
      title: "Company",
      links: [
        { name: "About Us", href: "#about", description: "Our story and mission" },
        { name: "Careers", href: "#careers", description: "Join our team" },
        { name: "Press Kit", href: "#press", description: "Media resources" },
        { name: "Contact", href: "#contact", description: "Get in touch" }
      ]
    },
    {
      title: "Support",
      links: [
        { name: "Help Center", href: "#help", description: "Documentation & guides" },
        { name: "API Docs", href: "#docs", description: "Technical documentation" },
        { name: "Status Page", href: "#status", description: "System status" },
        { name: "Community", href: "#community", description: "User community" }
      ]
    },
    {
      title: "Legal",
      links: [
        { name: "Privacy Policy", href: "https://www.databaseemailer.com/tos.php", description: "Data protection" },
        { name: "Terms of Service", href: "https://www.databaseemailer.com/tos.php", description: "Usage terms" },
        { name: "Cookie Policy", href: "#cookies", description: "Cookie usage" },
        { name: "GDPR", href: "#gdpr", description: "Compliance info" }
      ]
    }
  ];

  return (
    <footer className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-gray-300 overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
        }} />
      </div>

      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-indigo-900/20 via-transparent to-transparent" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Top Section with Stats */}
        <div className="pt-16 pb-12 border-b border-gray-700/50">
          <div className="text-center mb-12">
            {/* Logo */}
            <div className="flex items-center justify-center space-x-3 mb-6 group">
              <img
                className="h-12 opacity-90 transition-all duration-300 group-hover:scale-110"
                src="/assets/images/CPS_footer_logo.png"
                alt="Contact Page Submitter"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
              />
              <div className="hidden items-center space-x-3 transition-all duration-300 group-hover:scale-110" style={{ display: 'none' }}>
                <div className="w-12 h-12 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl flex items-center justify-center shadow-2xl">
                  <Zap className="w-7 h-7 text-white" />
                </div>
                <div className="text-left">
                  <h3 className="text-2xl font-bold text-white">Contact Page Submitter</h3>
                </div>
              </div>
            </div>
            
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4 bg-gradient-to-r from-white via-gray-100 to-white bg-clip-text text-transparent">
              AI-Powered Outreach at Scale
            </h2>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
              The most effective, professional, and cost-efficient way to deliver 
              <span className="text-indigo-400 font-semibold"> automated personalized messages</span> — 
              at unprecedented scale!
            </p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
            {stats.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <div key={index} className="text-center group">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl mb-4 shadow-xl group-hover:scale-110 transition-transform duration-300">
                    <Icon className="w-8 h-8 text-white" />
                  </div>
                  <div className="text-3xl font-bold text-white mb-1 group-hover:text-indigo-400 transition-colors">
                    {stat.value}
                  </div>
                  <div className="text-sm text-gray-400 group-hover:text-gray-300 transition-colors">
                    {stat.label}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Newsletter Signup */}
          <div className="max-w-md mx-auto">
            <div className="bg-gradient-to-r from-gray-800/80 to-gray-700/80 backdrop-blur-sm rounded-2xl p-6 border border-gray-600/30 shadow-2xl">
              <div className="text-center mb-4">
                <h3 className="text-lg font-semibold text-white mb-2">Stay Updated</h3>
                <p className="text-sm text-gray-300">Get the latest features and tips delivered to your inbox</p>
              </div>
              
              {!subscribed ? (
                <form onSubmit={handleSubscribe} className="flex space-x-2">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email"
                    className="flex-1 px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                    required
                  />
                  <button
                    type="submit"
                    className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-xl flex items-center space-x-2"
                  >
                    <Send className="w-4 h-4" />
                    <span className="hidden sm:inline">Subscribe</span>
                  </button>
                </form>
              ) : (
                <div className="flex items-center justify-center space-x-2 py-3 text-green-400">
                  <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className="font-medium">Successfully subscribed!</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main Footer Content */}
        <div className="py-12">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {footerSections.map((section, sectionIndex) => (
              <div key={sectionIndex} className="space-y-4">
                <h4 className="text-lg font-semibold text-white mb-6 flex items-center space-x-2">
                  <span>{section.title}</span>
                  <div className="w-8 h-0.5 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-full"></div>
                </h4>
                <ul className="space-y-3">
                  {section.links.map((link, linkIndex) => (
                    <li key={linkIndex}>
                      <a
                        href={link.href}
                        className="group flex items-start space-x-2 text-gray-300 hover:text-white transition-all duration-300 py-2 rounded-lg hover:bg-gray-800/30 px-3 -mx-3"
                        target={link.href.startsWith('http') ? '_blank' : '_self'}
                        rel={link.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                      >
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <span className="font-medium group-hover:text-indigo-400 transition-colors">
                              {link.name}
                            </span>
                            {link.href.startsWith('http') && (
                              <ExternalLink className="w-3 h-3 text-gray-500 group-hover:text-indigo-400 transition-colors" />
                            )}
                          </div>
                          <p className="text-xs text-gray-500 group-hover:text-gray-400 transition-colors mt-0.5">
                            {link.description}
                          </p>
                        </div>
                        <ChevronRight className="w-4 h-4 text-gray-500 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all opacity-0 group-hover:opacity-100" />
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Contact Information */}
        <div className="py-8 border-t border-gray-700/50">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center md:text-left">
            <div className="flex items-center justify-center md:justify-start space-x-3 group">
              <div className="p-3 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl shadow-lg group-hover:scale-110 transition-transform">
                <Mail className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Email Support</p>
                <p className="text-white font-medium group-hover:text-indigo-400 transition-colors">support@cps.com</p>
              </div>
            </div>
            
            <div className="flex items-center justify-center md:justify-start space-x-3 group">
              <div className="p-3 bg-gradient-to-r from-green-600 to-emerald-600 rounded-xl shadow-lg group-hover:scale-110 transition-transform">
                <MessageCircle className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Live Chat</p>
                <p className="text-white font-medium group-hover:text-indigo-400 transition-colors">24/7 Available</p>
              </div>
            </div>
            
            <div className="flex items-center justify-center md:justify-start space-x-3 group">
              <div className="p-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl shadow-lg group-hover:scale-110 transition-transform">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Security</p>
                <p className="text-white font-medium group-hover:text-indigo-400 transition-colors">Enterprise Grade</p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="py-8 border-t border-gray-700/50">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between space-y-6 lg:space-y-0">
            {/* Copyright */}
            <div className="flex items-center space-x-4">
              <p className="text-gray-400 text-sm">
                © {new Date().getFullYear()} Contact Page Submitter. All rights reserved.
              </p>
              <div className="hidden sm:flex items-center space-x-2 text-xs text-gray-500">
                <span>Made with</span>
                <Heart className="w-3 h-3 text-red-500 animate-pulse" />
                <span>for entrepreneurs</span>
              </div>
            </div>

            {/* Social Media */}
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-400 hidden sm:inline">Follow us:</span>
              <div className="flex items-center space-x-3">
                {socialLinks.map((social, index) => {
                  const Icon = social.icon;
                  return (
                    <a
                      key={index}
                      href={social.href}
                      className={`p-2.5 bg-gray-800 rounded-xl text-gray-400 transition-all duration-300 hover:bg-gray-700 hover:scale-110 ${social.color}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      title={social.name}
                    >
                      <Icon className="w-4 h-4" />
                    </a>
                  );
                })}
              </div>
            </div>

            {/* Trust Badges */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-xs text-gray-400">
                <Award className="w-4 h-4 text-yellow-500" />
                <span>SOC 2 Certified</span>
              </div>
              <div className="flex items-center space-x-2 text-xs text-gray-400">
                <Shield className="w-4 h-4 text-green-500" />
                <span>GDPR Compliant</span>
              </div>
            </div>
          </div>
        </div>

        {/* Floating Action Button */}
        <div className="fixed bottom-8 right-8 z-50">
          <button className="group flex items-center space-x-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-4 rounded-2xl shadow-2xl hover:shadow-3xl transition-all duration-300 hover:scale-105">
            <MessageCircle className="w-5 h-5" />
            <span className="font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-300 hidden lg:inline">
              Need Help?
            </span>
          </button>
        </div>
      </div>
    </footer>
  );
};

export default Footer;