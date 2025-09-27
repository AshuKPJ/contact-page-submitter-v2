import React, { useState } from 'react';
import { 
  Code, Terminal, Book, Key, Globe, Database, Server, Shield,
  Copy, Check, ChevronRight, ChevronDown, ExternalLink, Search,
  Zap, Lock, Clock, AlertCircle, Info, CheckCircle,
  Package, Cpu, Activity, BarChart3, Settings, Download,
  Play, Pause, RefreshCw, Link2, Hash, FileJson,
  Layers, GitBranch, Command, Braces, Send
} from 'lucide-react';

const APIDocumentationPage = () => {
  const [activeSection, setActiveSection] = useState('getting-started');
  const [selectedLanguage, setSelectedLanguage] = useState('javascript');
  const [copiedCode, setCopiedCode] = useState(null);
  const [expandedEndpoint, setExpandedEndpoint] = useState(null);

  const apiKey = 'sk_live_51234567890abcdef';

  const languages = [
    { id: 'javascript', label: 'JavaScript' },
    { id: 'python', label: 'Python' },
    { id: 'php', label: 'PHP' },
    { id: 'ruby', label: 'Ruby' },
    { id: 'curl', label: 'cURL' }
  ];

  const sections = [
    { id: 'getting-started', label: 'Getting Started', icon: Zap },
    { id: 'authentication', label: 'Authentication', icon: Key },
    { id: 'endpoints', label: 'API Endpoints', icon: Globe },
    { id: 'webhooks', label: 'Webhooks', icon: Link2 },
    { id: 'rate-limits', label: 'Rate Limits', icon: Clock },
    { id: 'errors', label: 'Error Handling', icon: AlertCircle },
    { id: 'sdks', label: 'SDKs & Libraries', icon: Package }
  ];

  const endpoints = [
    {
      method: 'GET',
      path: '/api/campaigns',
      description: 'List all campaigns',
      category: 'Campaigns',
      params: ['limit', 'offset', 'status'],
      response: '{ "campaigns": [...], "total": 100 }'
    },
    {
      method: 'POST',
      path: '/api/campaigns',
      description: 'Create a new campaign',
      category: 'Campaigns',
      params: ['name', 'urls', 'message'],
      response: '{ "id": "camp_123", "status": "created" }'
    },
    {
      method: 'GET',
      path: '/api/campaigns/{id}',
      description: 'Get campaign details',
      category: 'Campaigns',
      params: ['id'],
      response: '{ "id": "camp_123", "name": "...", ... }'
    },
    {
      method: 'POST',
      path: '/api/submissions',
      description: 'Submit to forms',
      category: 'Submissions',
      params: ['campaign_id', 'url', 'data'],
      response: '{ "success": true, "submission_id": "sub_456" }'
    },
    {
      method: 'GET',
      path: '/api/analytics',
      description: 'Get analytics data',
      category: 'Analytics',
      params: ['start_date', 'end_date', 'metrics'],
      response: '{ "total_submissions": 1000, ... }'
    }
  ];

  const codeExamples = {
    javascript: `const response = await fetch('https://api.example.com/campaigns', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer ${apiKey}',
    'Content-Type': 'application/json'
  }
});

const campaigns = await response.json();
console.log(campaigns);`,
    python: `import requests

response = requests.get(
    'https://api.example.com/campaigns',
    headers={
        'Authorization': f'Bearer ${apiKey}',
        'Content-Type': 'application/json'
    }
)

campaigns = response.json()
print(campaigns)`,
    curl: `curl -X GET https://api.example.com/campaigns \\
  -H "Authorization: Bearer ${apiKey}" \\
  -H "Content-Type: application/json"`
  };

  const handleCopyCode = (code, id) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const getMethodColor = (method) => {
    const colors = {
      GET: 'bg-green-100 text-green-700',
      POST: 'bg-blue-100 text-blue-700',
      PUT: 'bg-yellow-100 text-yellow-700',
      DELETE: 'bg-red-100 text-red-700'
    };
    return colors[method] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl">
                  <Code className="w-6 h-6 text-white" />
                </div>
                API Documentation
              </h1>
              <p className="text-gray-600 mt-1">Complete developer guide and API reference</p>
            </div>
            <div className="flex items-center gap-3">
              <button className="px-4 py-2 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors flex items-center gap-2">
                <Download className="w-4 h-4" />
                Export Docs
              </button>
              <button className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2">
                <Terminal className="w-4 h-4" />
                API Playground
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-4 gap-6">
          {/* Sidebar Navigation */}
          <div className="col-span-1">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm sticky top-24">
              <div className="p-4 border-b border-gray-200">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search docs..."
                    className="w-full pl-9 pr-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>
              <nav className="p-2">
                {sections.map(section => {
                  const Icon = section.icon;
                  return (
                    <button
                      key={section.id}
                      onClick={() => setActiveSection(section.id)}
                      className={`w-full px-3 py-2 rounded-lg text-left flex items-center gap-3 transition-colors ${
                        activeSection === section.id
                          ? 'bg-purple-50 text-purple-700'
                          : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      <span className="text-sm font-medium">{section.label}</span>
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="col-span-3">
            {/* Getting Started Section */}
            {activeSection === 'getting-started' && (
              <div>
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Getting Started</h2>
                  <p className="text-gray-600 mb-6">
                    Welcome to our API documentation. Follow these steps to get started with integrating our services.
                  </p>

                  {/* Quick Start Steps */}
                  <div className="space-y-4 mb-8">
                    {[
                      { step: 1, title: 'Get your API key', desc: 'Sign up and generate your API key from the dashboard' },
                      { step: 2, title: 'Install SDK', desc: 'Choose your preferred language and install our SDK' },
                      { step: 3, title: 'Make your first request', desc: 'Test the API with a simple GET request' },
                      { step: 4, title: 'Explore endpoints', desc: 'Browse available endpoints and build your integration' }
                    ].map(item => (
                      <div key={item.step} className="flex gap-4 p-4 bg-gray-50 rounded-lg">
                        <div className="w-8 h-8 bg-purple-600 text-white rounded-lg flex items-center justify-center font-semibold">
                          {item.step}
                        </div>
                        <div>
                          <h4 className="font-semibold text-gray-900">{item.title}</h4>
                          <p className="text-sm text-gray-600">{item.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Base URL */}
                  <div className="bg-gray-900 rounded-lg p-4 mb-6">
                    <p className="text-gray-400 text-sm mb-2">Base URL</p>
                    <code className="text-green-400 font-mono">https://api.example.com/v1</code>
                  </div>

                  {/* Language Selector & Code Example */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-900">Quick Example</h3>
                      <div className="flex gap-2">
                        {languages.slice(0, 3).map(lang => (
                          <button
                            key={lang.id}
                            onClick={() => setSelectedLanguage(lang.id)}
                            className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                              selectedLanguage === lang.id
                                ? 'bg-purple-100 text-purple-700'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                          >
                            {lang.label}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="relative">
                      <pre className="bg-gray-900 text-gray-300 p-4 rounded-lg overflow-x-auto">
                        <code className="font-mono text-sm">{codeExamples[selectedLanguage]}</code>
                      </pre>
                      <button
                        onClick={() => handleCopyCode(codeExamples[selectedLanguage], 'example')}
                        className="absolute top-3 right-3 p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                      >
                        {copiedCode === 'example' ? (
                          <Check className="w-4 h-4 text-green-400" />
                        ) : (
                          <Copy className="w-4 h-4 text-gray-400" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                {/* API Stats */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-white rounded-xl border border-gray-200 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <Activity className="w-5 h-5 text-green-600" />
                      <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">Operational</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">99.9%</p>
                    <p className="text-sm text-gray-600">Uptime</p>
                  </div>
                  <div className="bg-white rounded-xl border border-gray-200 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <Zap className="w-5 h-5 text-purple-600" />
                      <span className="text-xs text-gray-500">Average</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">45ms</p>
                    <p className="text-sm text-gray-600">Response Time</p>
                  </div>
                  <div className="bg-white rounded-xl border border-gray-200 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <Shield className="w-5 h-5 text-blue-600" />
                      <span className="text-xs text-gray-500">Latest</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">v1.2.0</p>
                    <p className="text-sm text-gray-600">API Version</p>
                  </div>
                </div>
              </div>
            )}

            {/* API Endpoints Section */}
            {activeSection === 'endpoints' && (
              <div>
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">API Endpoints</h2>
                  <p className="text-gray-600 mb-6">
                    Explore all available endpoints and their parameters.
                  </p>

                  {/* Endpoints List */}
                  <div className="space-y-3">
                    {endpoints.map((endpoint, idx) => (
                      <div key={idx} className="border border-gray-200 rounded-lg overflow-hidden">
                        <button
                          onClick={() => setExpandedEndpoint(expandedEndpoint === idx ? null : idx)}
                          className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between"
                        >
                          <div className="flex items-center gap-3">
                            <span className={`px-2 py-1 rounded text-xs font-semibold ${getMethodColor(endpoint.method)}`}>
                              {endpoint.method}
                            </span>
                            <code className="font-mono text-sm text-gray-700">{endpoint.path}</code>
                            <span className="text-sm text-gray-600">{endpoint.description}</span>
                          </div>
                          <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${
                            expandedEndpoint === idx ? 'rotate-180' : ''
                          }`} />
                        </button>
                        
                        {expandedEndpoint === idx && (
                          <div className="p-4 bg-white border-t border-gray-200">
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <h4 className="text-sm font-semibold text-gray-700 mb-2">Parameters</h4>
                                <div className="space-y-2">
                                  {endpoint.params.map(param => (
                                    <div key={param} className="flex items-center gap-2">
                                      <code className="px-2 py-1 bg-gray-100 rounded text-xs font-mono">{param}</code>
                                      <span className="text-xs text-gray-500">string</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                              <div>
                                <h4 className="text-sm font-semibold text-gray-700 mb-2">Response</h4>
                                <pre className="bg-gray-900 text-green-400 p-3 rounded text-xs font-mono">
                                  {endpoint.response}
                                </pre>
                              </div>
                            </div>
                            <div className="mt-4 flex gap-2">
                              <button className="px-3 py-1 bg-purple-100 text-purple-700 rounded-lg text-sm font-medium hover:bg-purple-200 transition-colors">
                                Try it out
                              </button>
                              <button className="px-3 py-1 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors">
                                View docs
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Authentication Section */}
            {activeSection === 'authentication' && (
              <div>
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Authentication</h2>
                  <p className="text-gray-600 mb-6">
                    Our API uses Bearer token authentication. Include your API key in the Authorization header of each request.
                  </p>

                  {/* API Key Display */}
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-semibold text-purple-900">Your API Key</span>
                      <button
                        onClick={() => handleCopyCode(apiKey, 'apikey')}
                        className="flex items-center gap-2 px-3 py-1 bg-white rounded-lg text-sm font-medium text-purple-700 hover:bg-purple-100 transition-colors"
                      >
                        {copiedCode === 'apikey' ? (
                          <>
                            <Check className="w-3 h-3" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" />
                            Copy
                          </>
                        )}
                      </button>
                    </div>
                    <code className="font-mono text-sm text-purple-800">{apiKey}</code>
                  </div>

                  {/* Security Best Practices */}
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <div className="flex gap-3">
                      <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <h4 className="font-semibold text-yellow-900 mb-1">Security Best Practices</h4>
                        <ul className="text-sm text-yellow-800 space-y-1">
                          <li>• Never expose your API key in client-side code</li>
                          <li>• Use environment variables to store sensitive keys</li>
                          <li>• Rotate your API keys regularly</li>
                          <li>• Use IP whitelisting for production environments</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Rate Limits Section */}
            {activeSection === 'rate-limits' && (
              <div>
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Rate Limits</h2>
                  <p className="text-gray-600 mb-6">
                    API rate limits help ensure fair usage and platform stability.
                  </p>

                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr className="border-b border-gray-200">
                          <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Plan</th>
                          <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Requests/Hour</th>
                          <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Requests/Day</th>
                          <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Burst Rate</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        <tr>
                          <td className="px-4 py-3 text-sm text-gray-900">Free</td>
                          <td className="px-4 py-3 text-sm text-gray-600">100</td>
                          <td className="px-4 py-3 text-sm text-gray-600">1,000</td>
                          <td className="px-4 py-3 text-sm text-gray-600">10/sec</td>
                        </tr>
                        <tr>
                          <td className="px-4 py-3 text-sm text-gray-900">Pro</td>
                          <td className="px-4 py-3 text-sm text-gray-600">1,000</td>
                          <td className="px-4 py-3 text-sm text-gray-600">10,000</td>
                          <td className="px-4 py-3 text-sm text-gray-600">50/sec</td>
                        </tr>
                        <tr>
                          <td className="px-4 py-3 text-sm text-gray-900">Enterprise</td>
                          <td className="px-4 py-3 text-sm text-gray-600">Unlimited</td>
                          <td className="px-4 py-3 text-sm text-gray-600">Unlimited</td>
                          <td className="px-4 py-3 text-sm text-gray-600">Custom</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default APIDocumentationPage;