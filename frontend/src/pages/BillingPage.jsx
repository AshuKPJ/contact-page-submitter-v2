import React, { useState } from 'react';
import { 
  CreditCard, DollarSign, TrendingUp, Download, Plus, Check, X,
  Calendar, Clock, AlertCircle, Info, ChevronRight, ChevronDown,
  Shield, Zap, Users, Package, Server, Database, Mail,
  FileText, BarChart3, Settings, RefreshCw, Edit2, Trash2,
  Lock, Star, Award, Gift, Percent, Receipt, Building,
  ArrowUpRight, ArrowDownRight, CheckCircle, XCircle
} from 'lucide-react';

const BillingPage = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedPlan, setSelectedPlan] = useState('pro');
  const [billingPeriod, setBillingPeriod] = useState('monthly');
  const [showAddCard, setShowAddCard] = useState(false);

  const currentPlan = {
    name: 'Professional',
    price: 149,
    billing: 'monthly',
    nextBilling: '2025-10-12',
    usage: {
      campaigns: { used: 45, limit: 100 },
      submissions: { used: 12847, limit: 50000 },
      users: { used: 3, limit: 5 },
      storage: { used: 2.3, limit: 10 }
    }
  };

  const plans = [
    {
      id: 'starter',
      name: 'Starter',
      price: { monthly: 49, yearly: 490 },
      popular: false,
      features: [
        '10 Campaigns/month',
        '5,000 Submissions',
        '1 User',
        'Email Support',
        'Basic Analytics',
        '1GB Storage'
      ],
      limits: {
        campaigns: 10,
        submissions: 5000,
        users: 1,
        storage: 1
      }
    },
    {
      id: 'pro',
      name: 'Professional',
      price: { monthly: 149, yearly: 1490 },
      popular: true,
      features: [
        '100 Campaigns/month',
        '50,000 Submissions',
        '5 Users',
        'Priority Support',
        'Advanced Analytics',
        '10GB Storage',
        'API Access',
        'Custom Integrations'
      ],
      limits: {
        campaigns: 100,
        submissions: 50000,
        users: 5,
        storage: 10
      }
    },
    {
      id: 'business',
      name: 'Business',
      price: { monthly: 299, yearly: 2990 },
      popular: false,
      features: [
        'Unlimited Campaigns',
        '200,000 Submissions',
        '20 Users',
        '24/7 Phone Support',
        'Custom Analytics',
        '100GB Storage',
        'Advanced API Access',
        'Webhook Support',
        'SSO Authentication'
      ],
      limits: {
        campaigns: -1,
        submissions: 200000,
        users: 20,
        storage: 100
      }
    }
  ];

  const paymentMethods = [
    {
      id: 1,
      type: 'card',
      brand: 'Visa',
      last4: '4242',
      expiry: '12/25',
      isDefault: true
    },
    {
      id: 2,
      type: 'card',
      brand: 'Mastercard',
      last4: '8888',
      expiry: '06/24',
      isDefault: false
    }
  ];

  const invoices = [
    {
      id: 'INV-2025-009',
      date: '2025-09-01',
      amount: 149,
      status: 'paid',
      description: 'Professional Plan - Monthly'
    },
    {
      id: 'INV-2025-008',
      date: '2025-08-01',
      amount: 149,
      status: 'paid',
      description: 'Professional Plan - Monthly'
    },
    {
      id: 'INV-2025-007',
      date: '2025-07-01',
      amount: 149,
      status: 'paid',
      description: 'Professional Plan - Monthly'
    },
    {
      id: 'INV-2025-006',
      date: '2025-06-01',
      amount: 149,
      status: 'paid',
      description: 'Professional Plan - Monthly'
    }
  ];

  const usageData = [
    { month: 'May', campaigns: 38, submissions: 9823 },
    { month: 'Jun', campaigns: 42, submissions: 10456 },
    { month: 'Jul', campaigns: 45, submissions: 11234 },
    { month: 'Aug', campaigns: 41, submissions: 10987 },
    { month: 'Sep', campaigns: 45, submissions: 12847 }
  ];

  const calculateSavings = (plan) => {
    if (billingPeriod === 'yearly') {
      const monthlyCost = plan.price.monthly * 12;
      const yearlyCost = plan.price.yearly;
      return Math.round(((monthlyCost - yearlyCost) / monthlyCost) * 100);
    }
    return 0;
  };

  const getCardIcon = (brand) => {
    return brand === 'Visa' ? '💳' : '💳';
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
                  <CreditCard className="w-6 h-6 text-white" />
                </div>
                Billing & Subscription
              </h1>
              <p className="text-gray-600 mt-1">Manage your plan, payment methods, and invoices</p>
            </div>
            <button className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2">
              <ArrowUpRight className="w-4 h-4" />
              Upgrade Plan
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-6 pt-8">
        <div className="flex gap-2 mb-8">
          {['overview', 'plans', 'payment', 'invoices'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 rounded-xl font-medium capitalize transition-all ${
                activeTab === tab
                  ? 'bg-purple-600 text-white shadow-md'
                  : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div>
            {/* Current Plan Card */}
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl p-6 text-white mb-8">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Award className="w-5 h-5" />
                    <span className="text-purple-100">Current Plan</span>
                  </div>
                  <h2 className="text-3xl font-bold mb-1">{currentPlan.name}</h2>
                  <p className="text-purple-100">
                    ${currentPlan.price}/month • Next billing on {currentPlan.nextBilling}
                  </p>
                </div>
                <button className="px-4 py-2 bg-white/20 backdrop-blur-sm rounded-lg hover:bg-white/30 transition-colors">
                  Change Plan
                </button>
              </div>
            </div>

            {/* Usage Stats */}
            <div className="grid grid-cols-4 gap-4 mb-8">
              {Object.entries(currentPlan.usage).map(([key, value]) => (
                <div key={key} className="bg-white rounded-xl border border-gray-200 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium text-gray-700 capitalize">{key}</span>
                    <span className="text-xs text-gray-500">
                      {value.limit === -1 ? 'Unlimited' : `of ${value.limit}`}
                    </span>
                  </div>
                  <div className="text-2xl font-bold text-gray-900 mb-2">
                    {key === 'storage' ? `${value.used} GB` : value.used.toLocaleString()}
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all ${
                        (value.used / value.limit) > 0.8 ? 'bg-red-500' : 'bg-purple-600'
                      }`}
                      style={{ width: `${Math.min((value.used / value.limit) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Usage Chart */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Usage Trends</h3>
              <div className="h-64 flex items-end justify-between gap-4">
                {usageData.map((data, idx) => (
                  <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                    <div className="w-full flex flex-col gap-2" style={{ height: '200px' }}>
                      <div className="relative flex-1 flex items-end">
                        <div 
                          className="w-full bg-purple-600 rounded-t-lg hover:bg-purple-700 transition-colors cursor-pointer"
                          style={{ height: `${(data.campaigns / 50) * 100}%` }}
                        >
                          <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs font-semibold text-gray-700">
                            {data.campaigns}
                          </div>
                        </div>
                      </div>
                    </div>
                    <span className="text-sm text-gray-600">{data.month}</span>
                  </div>
                ))}
              </div>
              <div className="flex items-center justify-center gap-6 mt-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-purple-600 rounded"></div>
                  <span className="text-sm text-gray-600">Campaigns</span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-3 gap-4">
              <button className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-lg transition-all text-left">
                <Download className="w-5 h-5 text-purple-600 mb-2" />
                <h4 className="font-semibold text-gray-900">Download Invoice</h4>
                <p className="text-sm text-gray-600">Get your latest invoice</p>
              </button>
              <button className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-lg transition-all text-left">
                <CreditCard className="w-5 h-5 text-purple-600 mb-2" />
                <h4 className="font-semibold text-gray-900">Update Payment</h4>
                <p className="text-sm text-gray-600">Change payment method</p>
              </button>
              <button className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-lg transition-all text-left">
                <Gift className="w-5 h-5 text-purple-600 mb-2" />
                <h4 className="font-semibold text-gray-900">Redeem Code</h4>
                <p className="text-sm text-gray-600">Apply promo code</p>
              </button>
            </div>
          </div>
        )}

        {/* Plans Tab */}
        {activeTab === 'plans' && (
          <div>
            {/* Billing Period Toggle */}
            <div className="flex justify-center mb-8">
              <div className="bg-white rounded-xl p-1 border border-gray-200 inline-flex">
                <button
                  onClick={() => setBillingPeriod('monthly')}
                  className={`px-6 py-2 rounded-lg transition-all ${
                    billingPeriod === 'monthly'
                      ? 'bg-purple-600 text-white'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Monthly
                </button>
                <button
                  onClick={() => setBillingPeriod('yearly')}
                  className={`px-6 py-2 rounded-lg transition-all ${
                    billingPeriod === 'yearly'
                      ? 'bg-purple-600 text-white'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Yearly
                  <span className="ml-2 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                    Save 20%
                  </span>
                </button>
              </div>
            </div>

            {/* Plans Grid */}
            <div className="grid grid-cols-3 gap-6">
              {plans.map((plan) => (
                <div
                  key={plan.id}
                  className={`bg-white rounded-2xl border-2 ${
                    plan.popular ? 'border-purple-600 shadow-xl' : 'border-gray-200'
                  } p-6 relative`}
                >
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <span className="bg-purple-600 text-white text-xs px-3 py-1 rounded-full font-semibold">
                        Most Popular
                      </span>
                    </div>
                  )}
                  
                  <div className="text-center mb-6">
                    <h3 className="text-xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                    <div className="flex items-baseline justify-center gap-1">
                      <span className="text-4xl font-bold text-gray-900">
                        ${billingPeriod === 'monthly' ? plan.price.monthly : Math.round(plan.price.yearly / 12)}
                      </span>
                      <span className="text-gray-600">/month</span>
                    </div>
                    {billingPeriod === 'yearly' && (
                      <p className="text-sm text-green-600 mt-1">
                        Save {calculateSavings(plan)}% with yearly billing
                      </p>
                    )}
                  </div>

                  <ul className="space-y-3 mb-6">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                        <span className="text-sm text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <button
                    className={`w-full py-3 rounded-xl font-semibold transition-all ${
                      plan.id === 'pro'
                        ? 'bg-purple-600 text-white hover:bg-purple-700'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {plan.id === 'pro' ? 'Current Plan' : 'Select Plan'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Payment Methods Tab */}
        {activeTab === 'payment' && (
          <div>
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900">Payment Methods</h3>
                <button 
                  onClick={() => setShowAddCard(!showAddCard)}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Add Card
                </button>
              </div>

              <div className="space-y-3">
                {paymentMethods.map((method) => (
                  <div key={method.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-purple-300 transition-colors">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-8 bg-gradient-to-r from-gray-700 to-gray-900 rounded flex items-center justify-center text-white text-xs font-bold">
                        {method.brand}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">
                          •••• {method.last4}
                        </p>
                        <p className="text-sm text-gray-600">Expires {method.expiry}</p>
                      </div>
                      {method.isDefault && (
                        <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full font-medium">
                          Default
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                        <Edit2 className="w-4 h-4 text-gray-600" />
                      </button>
                      <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                        <Trash2 className="w-4 h-4 text-gray-600" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Billing Information */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Billing Information</h3>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Company Name</label>
                  <input
                    type="text"
                    defaultValue="Acme Corp"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tax ID</label>
                  <input
                    type="text"
                    defaultValue="US123456789"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Billing Address</label>
                  <input
                    type="text"
                    defaultValue="123 Main St, Suite 100, New York, NY 10001"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>
              <button className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
                Save Changes
              </button>
            </div>
          </div>
        )}

        {/* Invoices Tab */}
        {activeTab === 'invoices' && (
          <div>
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Invoice History</h3>
                  <button className="text-sm text-purple-600 hover:text-purple-700 font-medium">
                    Download All
                  </button>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr className="border-b border-gray-200">
                      <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">Invoice</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">Date</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">Description</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">Amount</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">Status</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {invoices.map((invoice) => (
                      <tr key={invoice.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 text-sm font-medium text-gray-900">{invoice.id}</td>
                        <td className="px-6 py-4 text-sm text-gray-600">{invoice.date}</td>
                        <td className="px-6 py-4 text-sm text-gray-600">{invoice.description}</td>
                        <td className="px-6 py-4 text-sm font-semibold text-gray-900">${invoice.amount}</td>
                        <td className="px-6 py-4">
                          <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-medium">
                            {invoice.status}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <button className="text-purple-600 hover:text-purple-700 text-sm font-medium flex items-center gap-1">
                            <Download className="w-4 h-4" />
                            Download
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BillingPage;