import React, { useState, useRef, useEffect } from "react";
import { 
  User, Mail, Phone, Globe, Building, MapPin, MessageSquare, 
  ChevronRight, Save, CheckCircle, AlertCircle, Briefcase, 
  Hash, FileText, Info, Target, Zap, Shield, 
  Key, Lock, Camera, X, Eye, EyeOff,
  ArrowRight, Loader, Sparkles, Settings, Bell
} from 'lucide-react';
// Single correct import
import apiService from '../services/api';

// Enhanced toast notification system
const useToast = () => {
  const [toasts, setToasts] = useState([]);
  
  const showToast = (message, type = 'success') => {
    const id = Date.now() + Math.random();
    const toast = { id, message, type };
    
    setToasts(prev => [...prev, toast]);
    
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, type === 'success' ? 4000 : 6000);
  };
  
  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };
  
  return {
    toasts,
    success: (message) => showToast(message, 'success'),
    error: (message) => showToast(message, 'error'),
    removeToast
  };
};

// Toast notification component
const ToastContainer = ({ toasts, onRemove }) => {
  if (toasts.length === 0) return null;
  
  return (
    <div className="fixed top-6 right-6 z-50 space-y-3">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`p-4 rounded-2xl shadow-2xl backdrop-blur-sm max-w-md transform transition-all duration-300 ${
            toast.type === 'success' 
              ? 'bg-gradient-to-r from-emerald-50 to-green-50 border border-emerald-200 text-emerald-800'
              : 'bg-gradient-to-r from-red-50 to-rose-50 border border-red-200 text-red-800'
          }`}
        >
          <div className="flex items-start space-x-3">
            <div className={`flex-shrink-0 p-2 rounded-xl ${
              toast.type === 'success' ? 'bg-emerald-100' : 'bg-red-100'
            }`}>
              {toast.type === 'success' ? (
                <CheckCircle className="w-5 h-5 text-emerald-600" />
              ) : (
                <AlertCircle className="w-5 h-5 text-red-600" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold">{toast.message}</p>
            </div>
            <button 
              onClick={() => onRemove(toast.id)}
              className="flex-shrink-0 p-1 rounded-lg hover:bg-black/5 transition-colors"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

const ContactInformationForm = () => {
  const [activeSection, setActiveSection] = useState("profile");
  const [loading, setLoading] = useState(true);
  const [saveLoading, setSaveLoading] = useState(false);
  const [profileImagePreview, setProfileImagePreview] = useState(null);
  const toast = useToast();
  const [formData, setFormData] = useState({
    first_name: "", 
    last_name: "", 
    email: "", 
    phone_number: "",
    company_name: "", 
    job_title: "", 
    website_url: "", 
    industry: "",
    subject: "", 
    message: "", 
    city: "", 
    state: "", 
    zip_code: "", 
    country: "", 
    dbc_username: "", 
    dbc_password: "",
    linkedin_url: "",
    timezone: "",
    region: "",
    preferred_language: "",
    language: "",
    preferred_contact: "",
    best_time_to_contact: "",
    product_interest: "",
    budget_range: "",
    referral_source: "",
    contact_source: "",
    is_existing_customer: false,
    notes: "",
    form_custom_field_1: "",
    form_custom_field_2: "",
    form_custom_field_3: ""
  });
  
  const [saveStatus, setSaveStatus] = useState("");
  const [dbcBalance, setDbcBalance] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [hasDbcPassword, setHasDbcPassword] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchProfileData();
  }, []);

  const fetchProfileData = async () => {
    try {
      setLoading(true);
      console.log("[PROFILE] Fetching profile data from database...");
      
      const response = await apiService.getUserProfile();
      console.log("[PROFILE] Profile data received:", response);
      
      if (response) {
        const { user, profile } = response;
        
        // Combine user and profile data
        const userData = {
          // User fields
          first_name: user?.first_name || profile?.first_name || "",
          last_name: user?.last_name || profile?.last_name || "",
          email: user?.email || "",
          
          // Profile fields
          phone_number: profile?.phone_number || "",
          company_name: profile?.company_name || "",
          job_title: profile?.job_title || "",
          website_url: profile?.website_url || "",
          linkedin_url: profile?.linkedin_url || "",
          industry: profile?.industry || "",
          subject: profile?.subject || "",
          message: profile?.message || "",
          city: profile?.city || "",
          state: profile?.state || "",
          zip_code: profile?.zip_code || "",
          country: profile?.country || "",
          timezone: profile?.timezone || "",
          region: profile?.region || "",
          preferred_language: profile?.preferred_language || "",
          language: profile?.language || "",
          preferred_contact: profile?.preferred_contact || "",
          best_time_to_contact: profile?.best_time_to_contact || "",
          product_interest: profile?.product_interest || "",
          budget_range: profile?.budget_range || "",
          referral_source: profile?.referral_source || "",
          contact_source: profile?.contact_source || "",
          is_existing_customer: profile?.is_existing_customer || false,
          notes: profile?.notes || "",
          form_custom_field_1: profile?.form_custom_field_1 || "",
          form_custom_field_2: profile?.form_custom_field_2 || "",
          form_custom_field_3: profile?.form_custom_field_3 || "",
          
          // DBC credentials
          dbc_username: profile?.dbc_username || "",
          dbc_password: profile?.dbc_password_masked || ""
        };

        setFormData(userData);
        
        // Set profile image if available
        if (user?.profile_image_url) {
          setProfileImagePreview(user.profile_image_url);
        }

        // Check if user has DBC credentials
        if (profile?.has_dbc_credentials) {
          setDbcBalance("Active");
          setHasDbcPassword(true);
        }

        // Check profile completeness
        if (profile?.captcha_enabled) {
          console.log("[PROFILE] CAPTCHA is enabled for this user");
        }

        toast.success("Profile loaded successfully");
      }
    } catch (error) {
      console.error("[PROFILE] Error fetching profile:", error);
      
      let errorMessage = "Failed to load profile data";
      
      if (error.response?.status === 401) {
        errorMessage = "Session expired. Please login again.";
        // Redirect to login if unauthorized
        setTimeout(() => {
          window.location.href = '/';
        }, 2000);
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const calculateSectionCompletion = (sectionId) => {
    const sectionFields = {
      profile: ["first_name", "last_name", "email", "phone_number"],
      business: ["company_name", "job_title", "website_url", "industry"],
      automation: ["subject", "message"],
      security: ["dbc_username", "dbc_password"],
      location: ["city", "state", "zip_code", "country"]
    };
    
    const fields = sectionFields[sectionId] || [];
    const filledFields = fields.filter(field => {
      // Special handling for masked password
      if (field === 'dbc_password' && hasDbcPassword) return true;
      return formData[field] && formData[field].toString().length > 0;
    });
    return Math.round((filledFields.length / fields.length) * 100);
  };

  const sections = [
    {
      id: "profile", title: "Personal Profile", icon: User,
      description: "Basic personal information", color: "blue",
      completion: calculateSectionCompletion("profile"),
      fields: ["first_name", "last_name", "email", "phone_number"]
    },
    {
      id: "business", title: "Business Info", icon: Building,
      description: "Professional details", color: "purple",
      completion: calculateSectionCompletion("business"),
      fields: ["company_name", "job_title", "website_url", "industry", "linkedin_url"]
    },
    {
      id: "automation", title: "Message Templates", icon: MessageSquare,
      description: "Default messages", color: "emerald",
      completion: calculateSectionCompletion("automation"),
      fields: ["subject", "message"]
    },
    {
      id: "security", title: "Security Services", icon: Shield,
      description: "CAPTCHA integration", color: "amber",
      completion: calculateSectionCompletion("security"),
      fields: ["dbc_username", "dbc_password"]
    },
    {
      id: "location", title: "Location", icon: MapPin,
      description: "Geographic details", color: "rose",
      completion: calculateSectionCompletion("location"),
      fields: ["city", "state", "zip_code", "country", "timezone"]
    }
  ];

  const colorThemes = {
    blue: { 
      gradient: 'from-blue-500 to-indigo-600', bg: 'bg-blue-50', 
      text: 'text-blue-700', ring: 'ring-blue-200', progress: 'bg-blue-500' 
    },
    purple: { 
      gradient: 'from-purple-500 to-violet-600', bg: 'bg-purple-50', 
      text: 'text-purple-700', ring: 'ring-purple-200', progress: 'bg-purple-500' 
    },
    emerald: { 
      gradient: 'from-emerald-500 to-green-600', bg: 'bg-emerald-50', 
      text: 'text-emerald-700', ring: 'ring-emerald-200', progress: 'bg-emerald-500' 
    },
    amber: { 
      gradient: 'from-amber-500 to-orange-600', bg: 'bg-amber-50', 
      text: 'text-amber-700', ring: 'ring-amber-200', progress: 'bg-amber-500' 
    },
    rose: { 
      gradient: 'from-rose-500 to-pink-600', bg: 'bg-rose-50', 
      text: 'text-rose-700', ring: 'ring-rose-200', progress: 'bg-rose-500' 
    }
  };

  const handleChange = (e) => {
    const { id, value, type, checked } = e.target;
    setFormData(prev => ({ 
      ...prev, 
      [id]: type === 'checkbox' ? checked : value 
    }));
  };

  const handleSave = async () => {
    try {
      setSaveLoading(true);
      setSaveStatus("saving");
      console.log("[PROFILE] Saving profile data...");

      // Prepare data for API (exclude empty strings and masked passwords)
      const updateData = {};
      Object.keys(formData).forEach(key => {
        const value = formData[key];
        
        // Skip email as it's not editable
        if (key === 'email') return;
        
        // Skip masked password unless it's been changed
        if (key === 'dbc_password' && (value === '********' || value === '')) {
          return;
        }
        
        // Include non-empty values
        if (value !== "" && value !== null && value !== undefined) {
          updateData[key] = value;
        }
      });

      console.log("[PROFILE] Sending update data:", updateData);

      const response = await apiService.updateUserProfile(updateData);
      console.log("[PROFILE] Profile updated:", response);

      setSaveStatus("saved");
      toast.success("Profile updated successfully!");
      
      // Refresh profile data to get latest from server
      setTimeout(() => {
        fetchProfileData();
      }, 500);
      
      setTimeout(() => setSaveStatus(""), 3000);
    } catch (error) {
      console.error("[PROFILE] Error saving profile:", error);
      setSaveStatus("error");
      
      let errorMessage = "Failed to update profile";
      
      if (error.response?.status === 401) {
        errorMessage = "Session expired. Please login again.";
        setTimeout(() => {
          window.location.href = '/';
        }, 2000);
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast.error(errorMessage);
      
      setTimeout(() => setSaveStatus(""), 5000);
    } finally {
      setSaveLoading(false);
    }
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file
    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      toast.error('File size must be less than 5MB');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Fixed: Using apiService.makeRequest instead of api.post
      const response = await apiService.makeRequest('post', '/api/users/upload-avatar', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response?.profile_image_url) {
        setProfileImagePreview(response.profile_image_url);
        toast.success('Profile image updated!');
      }
    } catch (error) {
      console.error('Error uploading image:', error);
      toast.error('Failed to upload image');
    }
  };

  const calculateProfileStrength = () => {
    const requiredFields = ['first_name', 'last_name', 'email'];
    const importantFields = ['phone_number', 'company_name', 'job_title'];
    const optionalFields = ['website_url', 'industry', 'linkedin_url', 'subject', 
                            'message', 'city', 'state', 'country'];
    
    let totalWeight = 0;
    let completedWeight = 0;
    
    // Required fields worth 3 points each
    requiredFields.forEach(field => {
      totalWeight += 3;
      if (formData[field] && formData[field].length > 0) completedWeight += 3;
    });
    
    // Important fields worth 2 points each
    importantFields.forEach(field => {
      totalWeight += 2;
      if (formData[field] && formData[field].length > 0) completedWeight += 2;
    });
    
    // Optional fields worth 1 point each
    optionalFields.forEach(field => {
      totalWeight += 1;
      if (formData[field] && formData[field].length > 0) completedWeight += 1;
    });
    
    return Math.round((completedWeight / totalWeight) * 100);
  };

  const profileStrength = calculateProfileStrength();
  const currentSection = sections.find(s => s.id === activeSection);
  const currentTheme = colorThemes[currentSection?.color || 'blue'];

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50 flex items-center justify-center">
        <div className="text-center space-y-6">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-slate-200 border-t-indigo-600 rounded-full animate-spin mx-auto"></div>
            <div className="absolute inset-0 w-16 h-16 border-4 border-transparent border-r-purple-600 rounded-full animate-spin mx-auto" style={{animationDelay: '0.3s'}}></div>
          </div>
          <div className="space-y-2">
            <p className="text-xl font-semibold text-slate-700">Loading Your Profile</p>
            <p className="text-sm text-slate-500">Fetching your information from database...</p>
          </div>
        </div>
      </div>
    );
  }

  const renderField = (field) => {
    const fieldConfig = {
      first_name: { label: "First Name", type: "text", icon: User, required: true },
      last_name: { label: "Last Name", type: "text", icon: User, required: true },
      email: { label: "Email Address", type: "email", icon: Mail, required: true, disabled: true },
      phone_number: { label: "Phone Number", type: "tel", icon: Phone },
      company_name: { label: "Company Name", type: "text", icon: Building },
      job_title: { label: "Job Title", type: "text", icon: Briefcase },
      website_url: { label: "Website URL", type: "url", icon: Globe },
      linkedin_url: { label: "LinkedIn URL", type: "url", icon: Globe },
      industry: { 
        label: "Industry", type: "select", icon: Hash,
        options: ["Technology & Software", "Healthcare & Medical", "Financial Services", "Manufacturing", "Retail", "Education", "Other"]
      },
      subject: { label: "Default Subject", type: "text", icon: FileText },
      message: { label: "Message Template", type: "textarea", icon: MessageSquare, rows: 4 },
      city: { label: "City", type: "text", icon: MapPin },
      state: { label: "State", type: "text", icon: MapPin },
      zip_code: { label: "ZIP Code", type: "text", icon: Hash },
      country: { 
        label: "Country", type: "select", icon: Globe,
        options: ["United States", "Canada", "United Kingdom", "Australia", "Germany", "France", "Other"]
      },
      timezone: {
        label: "Timezone", type: "select", icon: Globe,
        options: ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", "Europe/London", "Europe/Paris", "Asia/Tokyo", "Australia/Sydney"]
      },
      dbc_username: { label: "DBC Username", type: "text", icon: User },
      dbc_password: { label: "DBC Password", type: "password", icon: Lock, placeholder: hasDbcPassword ? "Enter new password to change" : "Enter your password" }
    };

    const config = fieldConfig[field];
    if (!config) return null;

    const FieldIcon = config.icon;
    const isDisabled = config.disabled;
    const hasValue = formData[field] && formData[field].length > 0 && formData[field] !== '********';

    return (
      <div key={field} className={config.type === 'textarea' ? 'col-span-full' : 'col-span-full sm:col-span-1'}>
        <label className="flex items-center gap-2 text-sm font-medium text-slate-700 mb-3">
          <FieldIcon className="w-4 h-4 text-slate-500" />
          {config.label}
          {config.required && <span className="text-rose-500">*</span>}
          {isDisabled && (
            <span className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-amber-100 text-amber-700 rounded-full">
              <Lock className="w-3 h-3" />
              Protected
            </span>
          )}
        </label>
        
        <div className="relative group">
          {config.type === 'textarea' ? (
            <textarea
              id={field}
              rows={config.rows}
              value={formData[field] || ''}
              onChange={handleChange}
              disabled={isDisabled}
              className={`w-full px-4 py-3 border rounded-xl text-sm transition-all duration-200 resize-none
                ${hasValue ? 'border-emerald-300 bg-emerald-50/50' : 'border-slate-300 bg-white'} 
                ${isDisabled ? 'bg-slate-50 cursor-not-allowed' : 'hover:border-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200'}
              `}
              placeholder={config.placeholder || `Enter your ${config.label.toLowerCase()}`}
            />
          ) : config.type === 'select' ? (
            <select
              id={field}
              value={formData[field] || ''}
              onChange={handleChange}
              disabled={isDisabled}
              className={`w-full px-4 py-3 border rounded-xl text-sm transition-all duration-200
                ${hasValue ? 'border-emerald-300 bg-emerald-50/50' : 'border-slate-300 bg-white'} 
                ${isDisabled ? 'bg-slate-50 cursor-not-allowed' : 'hover:border-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200'}
              `}
            >
              <option value="">Select {config.label}</option>
              {config.options?.map(opt => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          ) : (
            <div className="relative">
              <input
                type={config.type === 'password' && showPassword ? 'text' : config.type}
                id={field}
                value={formData[field] || ''}
                onChange={handleChange}
                disabled={isDisabled}
                className={`w-full px-4 py-3 border rounded-xl text-sm transition-all duration-200
                  ${hasValue ? 'border-emerald-300 bg-emerald-50/50' : 'border-slate-300 bg-white'} 
                  ${config.type === 'password' ? 'pr-12' : ''}
                  ${isDisabled ? 'bg-slate-50 cursor-not-allowed' : 'hover:border-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200'}
                `}
                placeholder={config.placeholder || `Enter your ${config.label.toLowerCase()}`}
              />
              
              {config.type === 'password' && (
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              )}
            </div>
          )}
          
          {hasValue && !isDisabled && (
            <div className="absolute -right-2 -top-2 p-1.5 bg-emerald-500 rounded-full">
              <CheckCircle className="w-3 h-3 text-white" />
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50">
      {/* Modern Header */}
      <div className="bg-white/80 backdrop-blur-md shadow-sm border-b border-slate-200/60 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">
            {/* Profile Section */}
            <div className="flex items-center gap-6">
              {/* Enhanced Avatar */}
              <div className="relative group">
                <div className="w-20 h-20 rounded-2xl overflow-hidden bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 shadow-xl ring-4 ring-white">
                  {profileImagePreview ? (
                    <img src={profileImagePreview} alt="Profile" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-white font-bold text-xl">
                      {formData.first_name?.[0] || 'U'}{formData.last_name?.[0] || 'N'}
                    </div>
                  )}
                </div>
                
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                />
                
                <button 
                  onClick={() => fileInputRef.current?.click()}
                  className="absolute -bottom-1 -right-1 p-2 bg-white rounded-xl shadow-lg hover:shadow-xl transition-all hover:scale-110 border border-slate-200"
                >
                  <Camera className="w-3.5 h-3.5 text-slate-600" />
                </button>
              </div>
              
              <div className="space-y-2">
                <h1 className="text-2xl lg:text-3xl font-bold text-slate-900">
                  Profile Settings
                </h1>
                <p className="text-slate-600">Manage your information and preferences</p>
                <div className="flex flex-wrap items-center gap-3">
                  <span className="inline-flex items-center px-3 py-1.5 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 text-white text-sm font-medium">
                    {formData.first_name || 'Unknown'} {formData.last_name || 'User'}
                  </span>
                  {formData.company_name && (
                    <span className="text-sm text-slate-500">at {formData.company_name}</span>
                  )}
                </div>
              </div>
            </div>
            
            {/* Stats */}
            <div className="flex items-center gap-8">
              <div className="text-center">
                <div className="relative w-16 h-16 mb-2">
                  <svg className="w-16 h-16 transform -rotate-90">
                    <circle cx="32" cy="32" r="28" stroke="#e2e8f0" strokeWidth="4" fill="none" />
                    <circle
                      cx="32" cy="32" r="28" strokeWidth="4" fill="none" strokeLinecap="round"
                      stroke="url(#profileGradient)"
                      strokeDasharray={`${2 * Math.PI * 28}`}
                      strokeDashoffset={`${2 * Math.PI * 28 * (1 - profileStrength / 100)}`}
                    />
                    <defs>
                      <linearGradient id="profileGradient">
                        <stop offset="0%" stopColor="#6366f1" />
                        <stop offset="100%" stopColor="#a855f7" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-lg font-bold text-slate-900">{profileStrength}%</span>
                  </div>
                </div>
                <p className="text-xs text-slate-500 font-medium">Complete</p>
              </div>
              
              <div className="w-px h-12 bg-slate-200"></div>
              
              <div className="text-center space-y-1">
                <div className={`inline-flex items-center gap-2 ${dbcBalance ? 'text-emerald-600' : 'text-slate-400'}`}>
                  <Shield className="w-4 h-4" />
                </div>
                <div className="text-sm font-bold text-slate-900">
                  {dbcBalance ? 'Active' : 'Inactive'}
                </div>
                <p className="text-xs text-slate-500">CAPTCHA</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-3xl shadow-xl border border-slate-200/60 overflow-hidden sticky top-32">
              <div className="p-6 bg-gradient-to-br from-slate-50 to-white border-b border-slate-200/60">
                <h3 className="font-bold text-slate-900 text-lg mb-1">Settings</h3>
                <p className="text-slate-500 text-sm">Configure your profile</p>
              </div>
              
              <nav className="p-4 space-y-2">
                {sections.map((section) => {
                  const Icon = section.icon;
                  const isActive = activeSection === section.id;
                  const theme = colorThemes[section.color];
                  
                  return (
                    <button
                      key={section.id}
                      onClick={() => setActiveSection(section.id)}
                      className={`w-full p-4 rounded-2xl text-left transition-all duration-300 group ${
                        isActive 
                          ? `${theme.bg} ring-2 ${theme.ring} shadow-md transform scale-[1.02]` 
                          : 'hover:bg-slate-50 hover:shadow-sm'
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        <div className={`p-2.5 rounded-xl transition-all ${
                          isActive 
                            ? `bg-gradient-to-br ${theme.gradient} text-white shadow-lg` 
                            : 'bg-slate-100 text-slate-500 group-hover:bg-slate-200'
                        }`}>
                          <Icon className="w-4 h-4" />
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className={`font-semibold text-sm ${isActive ? theme.text : 'text-slate-700'}`}>
                            {section.title}
                          </div>
                          <div className={`text-xs mt-0.5 ${isActive ? 'text-slate-600' : 'text-slate-500'}`}>
                            {section.description}
                          </div>
                          
                          <div className="flex items-center gap-2 mt-2">
                            <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                              <div 
                                className={`h-full transition-all duration-500 ${theme.progress}`}
                                style={{ width: `${section.completion}%` }}
                              />
                            </div>
                            <span className="text-xs font-medium text-slate-500">
                              {section.completion}%
                            </span>
                          </div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-3xl shadow-xl border border-slate-200/60 overflow-hidden">
              {/* Section Header */}
              <div className={`px-8 py-8 ${currentTheme.bg} border-b border-slate-200/60`}>
                <div className="flex items-center gap-4">
                  <div className={`p-4 bg-gradient-to-br ${currentTheme.gradient} rounded-2xl shadow-lg`}>
                    <currentSection.icon className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-slate-900 mb-1">
                      {currentSection?.title}
                    </h2>
                    <p className="text-slate-600">{currentSection?.description}</p>
                  </div>
                </div>
              </div>

              {/* Form Content */}
              <div className="p-8">
                {activeSection === 'security' && (
                  <div className="mb-8 p-6 bg-gradient-to-r from-amber-50 to-orange-50 rounded-2xl border border-amber-200/60">
                    <div className="flex gap-4">
                      <div className="p-3 bg-amber-100 rounded-xl">
                        <Info className="w-5 h-5 text-amber-600" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-amber-900 mb-2">
                          CAPTCHA Service Integration
                        </h4>
                        <p className="text-amber-800 text-sm leading-relaxed mb-4">
                          Connect your Death By Captcha account to automatically solve CAPTCHAs 
                          and improve form submission success rates.
                        </p>
                        <a 
                          href="https://deathbycaptcha.com" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 px-4 py-2 bg-white rounded-xl text-amber-700 hover:text-amber-800 font-medium text-sm shadow-sm hover:shadow-md transition-all"
                        >
                          <span>Create Account</span>
                          <ArrowRight className="w-4 h-4" />
                        </a>
                      </div>
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  {currentSection?.fields.map(field => renderField(field))}
                </div>
              </div>

              {/* Footer */}
              <div className="px-8 py-6 bg-gradient-to-r from-slate-50 to-white border-t border-slate-200/60">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    {saveStatus === 'saved' && (
                      <div className="flex items-center gap-3 text-emerald-700 bg-emerald-50 px-4 py-2 rounded-xl">
                        <CheckCircle className="w-4 h-4" />
                        <span className="font-medium text-sm">Saved successfully!</span>
                      </div>
                    )}
                    {saveStatus === 'error' && (
                      <div className="flex items-center gap-3 text-red-700 bg-red-50 px-4 py-2 rounded-xl">
                        <AlertCircle className="w-4 h-4" />
                        <span className="font-medium text-sm">Save failed</span>
                      </div>
                    )}
                  </div>
                  
                  <button
                    onClick={handleSave}
                    disabled={saveLoading}
                    className={`px-8 py-3 rounded-xl font-semibold text-sm transition-all duration-200 flex items-center gap-3 ${
                      saveLoading
                        ? 'bg-slate-400 text-white cursor-not-allowed'
                        : 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transform hover:scale-[1.02]'
                    }`}
                  >
                    {saveLoading ? <Loader className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    <span>{saveLoading ? 'Saving...' : 'Save Changes'}</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
              {[
                { label: "Processing", value: "120/hr", icon: Zap, color: "from-blue-500 to-indigo-500" },
                { label: "Success Rate", value: "94%", icon: Target, color: "from-emerald-500 to-green-500" },
                { label: "Email Backup", value: "8%", icon: Mail, color: "from-purple-500 to-violet-500" },
                { label: "Active", value: "3", icon: Bell, color: "from-rose-500 to-pink-500" }
              ].map((stat, idx) => {
                const Icon = stat.icon;
                return (
                  <div key={idx} className="bg-white rounded-2xl shadow-lg border border-slate-200/60 p-6 hover:shadow-xl transition-all duration-300 hover:scale-[1.02]">
                    <div className="flex items-center justify-between mb-4">
                      <div className={`p-3 rounded-xl bg-gradient-to-br ${stat.color} shadow-md`}>
                        <Icon className="w-4 h-4 text-white" />
                      </div>
                      <Sparkles className="w-3 h-3 text-slate-300" />
                    </div>
                    <div className="text-2xl font-bold text-slate-900 mb-1">{stat.value}</div>
                    <div className="text-sm text-slate-500">{stat.label}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
      
      {/* Toast Notifications */}
      <ToastContainer toasts={toast.toasts} onRemove={toast.removeToast} />
    </div>
  );
};

export default ContactInformationForm;