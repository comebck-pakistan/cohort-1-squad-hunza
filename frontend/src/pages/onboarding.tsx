import React, { useState } from 'react';
import { useRouter } from 'next/router';
import {
  Check,
  Plus,
  X,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Briefcase,
  Layers,
  FileText,
  MessageSquare,
} from 'lucide-react';
import { useAppState } from '../context/AppStateContext';

export default function Onboarding() {
  const router = useRouter();
  const { categories, addCategory, jobRoles, addJobRole, removeJobRole, updateOnboarding, showToast } = useAppState();

  const [currentStep, setCurrentStep] = useState<number>(1);
  const [selectedCategories, setSelectedCategories] = useState<string[]>(categories);
  const [customCategoryInput, setCustomCategoryInput] = useState<string>('');
  const [newRoleInput, setNewRoleInput] = useState<string>('');
  const [selectedRoleForDesc, setSelectedRoleForDesc] = useState<string>(jobRoles[0] || 'AI Engineer');
  const [jobDescriptionText, setJobDescriptionText] = useState<string>(
    'Seeking AI Engineer with 3+ years experience building PyTorch models, vector databases, and RAG architectures.'
  );
  const [replyTone, setReplyTone] = useState<'Formal' | 'Friendly' | 'Brief'>('Friendly');

  const toggleCategory = (cat: string) => {
    if (selectedCategories.includes(cat)) {
      setSelectedCategories(selectedCategories.filter((c) => c !== cat));
    } else {
      setSelectedCategories([...selectedCategories, cat]);
    }
  };

  const handleAddCustomCategory = () => {
    if (!customCategoryInput.trim()) return;
    const cat = customCategoryInput.trim();
    addCategory(cat);
    setSelectedCategories((prev) => [...prev, cat]);
    setCustomCategoryInput('');
  };

  const handleAddRole = () => {
    if (!newRoleInput.trim()) return;
    addJobRole(newRoleInput.trim());
    setNewRoleInput('');
  };

  const handleFinishSetup = () => {
    updateOnboarding({
      completed: true,
      categories: selectedCategories,
      roles: jobRoles,
      jobDescriptions: { [selectedRoleForDesc]: jobDescriptionText },
      replyTone,
    });
    showToast('🎉 Onboarding setup complete! Welcome to Crextio.');
    router.push('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-[#EFE9DE]">
      <div className="w-full max-w-2xl bg-[#FBF9F5] border border-[#EAE3D5] rounded-3xl p-8 shadow-nixtio-lg space-y-8 relative">
        {/* Progress Bar Top */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-zinc-600">
            <span className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-500" />
              Onboarding Wizard
            </span>
            <span className="bg-amber-400/20 text-amber-900 border border-amber-300 px-3 py-1 rounded-full">
              Step {currentStep} of 4
            </span>
          </div>
          <div className="w-full bg-[#EFE9DE] h-2.5 rounded-full overflow-hidden">
            <div
              className="bg-zinc-900 h-full transition-all duration-300 rounded-full"
              style={{ width: `${(currentStep / 4) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* STEP 1: Categories */}
        {currentStep === 1 && (
          <div className="space-y-6 animate-fadeIn">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-zinc-900">
                <Layers className="w-5 h-5 text-amber-500" />
                <h2 className="text-xl font-extrabold">What types of emails do you receive?</h2>
              </div>
              <p className="text-xs text-zinc-500 font-medium">
                Toggle categories to enable automatic AI tagging and routing.
              </p>
            </div>

            {/* Chips grid */}
            <div className="flex flex-wrap gap-2.5">
              {categories.map((cat) => {
                const isSelected = selectedCategories.includes(cat);
                return (
                  <button
                    key={cat}
                    onClick={() => toggleCategory(cat)}
                    className={`px-4 py-2 rounded-2xl text-xs font-bold transition-all flex items-center gap-2 ${
                      isSelected
                        ? 'bg-zinc-900 text-white shadow-sm'
                        : 'bg-[#EFE9DE] text-zinc-600 border border-[#E4DCCF] hover:bg-[#E4DCCF]'
                    }`}
                  >
                    {isSelected && <Check className="w-3.5 h-3.5 text-amber-400" />}
                    <span>{cat}</span>
                  </button>
                );
              })}
            </div>

            {/* Custom Category Input */}
            <div className="flex items-center gap-2 pt-2">
              <input
                type="text"
                value={customCategoryInput}
                onChange={(e) => setCustomCategoryInput(e.target.value)}
                placeholder="Add custom category name..."
                className="flex-1 bg-white border border-zinc-300 rounded-xl px-4 py-2 text-xs font-medium text-zinc-900 focus:outline-none focus:ring-2 focus:ring-amber-400"
              />
              <button
                onClick={handleAddCustomCategory}
                className="bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-bold px-4 py-2 rounded-xl flex items-center gap-1 transition-all"
              >
                <Plus className="w-4 h-4 text-amber-400" /> Add
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: Job Roles */}
        {currentStep === 2 && (
          <div className="space-y-6 animate-fadeIn">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-zinc-900">
                <Briefcase className="w-5 h-5 text-amber-500" />
                <h2 className="text-xl font-extrabold">What roles are you currently hiring for?</h2>
              </div>
              <p className="text-xs text-zinc-500 font-medium">
                Add open requisitions to contextualize candidate application parsing.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="text"
                value={newRoleInput}
                onChange={(e) => setNewRoleInput(e.target.value)}
                placeholder="e.g. Senior Frontend Engineer..."
                className="flex-1 bg-white border border-zinc-300 rounded-xl px-4 py-2.5 text-xs font-medium text-zinc-900 focus:outline-none focus:ring-2 focus:ring-amber-400"
              />
              <button
                onClick={handleAddRole}
                className="bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-bold px-5 py-2.5 rounded-xl flex items-center gap-1 transition-all"
              >
                <Plus className="w-4 h-4 text-amber-400" /> Add Role
              </button>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Active Roles</label>
              <div className="flex flex-wrap gap-2">
                {jobRoles.map((role) => (
                  <span
                    key={role}
                    className="bg-[#EFE9DE] border border-[#E2DACB] text-zinc-900 px-3.5 py-1.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-xs"
                  >
                    <span>{role}</span>
                    <button
                      onClick={() => removeJobRole(role)}
                      className="text-zinc-400 hover:text-rose-600 transition-colors"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* STEP 3: Job Description */}
        {currentStep === 3 && (
          <div className="space-y-6 animate-fadeIn">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-zinc-900">
                <FileText className="w-5 h-5 text-amber-500" />
                <h2 className="text-xl font-extrabold">Paste your job description</h2>
              </div>
              <p className="text-xs text-zinc-500 font-medium">
                This helps the AI detect questions already answered in your job posting.
              </p>
            </div>

            <div className="space-y-3">
              <label className="text-xs font-bold text-zinc-700">Select Target Role</label>
              <select
                value={selectedRoleForDesc}
                onChange={(e) => setSelectedRoleForDesc(e.target.value)}
                className="w-full bg-white border border-zinc-300 rounded-xl px-4 py-2.5 text-xs font-bold text-zinc-900 focus:outline-none focus:ring-2 focus:ring-amber-400"
              >
                {jobRoles.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>

              <label className="text-xs font-bold text-zinc-700 block">Job Requirement Details</label>
              <textarea
                rows={5}
                value={jobDescriptionText}
                onChange={(e) => setJobDescriptionText(e.target.value)}
                placeholder="Paste requirements, compensation details, remote policies..."
                className="w-full bg-white border border-zinc-300 rounded-xl p-4 text-xs font-medium text-zinc-900 leading-relaxed focus:outline-none focus:ring-2 focus:ring-amber-400"
              ></textarea>
            </div>
          </div>
        )}

        {/* STEP 4: Reply Settings */}
        {currentStep === 4 && (
          <div className="space-y-6 animate-fadeIn">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-zinc-900">
                <MessageSquare className="w-5 h-5 text-amber-500" />
                <h2 className="text-xl font-extrabold">How should the AI write replies?</h2>
              </div>
              <p className="text-xs text-zinc-500 font-medium">
                Select your default communication style for generated email drafts.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { tone: 'Formal', desc: 'Professional, structured, and polished' },
                { tone: 'Friendly', desc: 'Warm, welcoming, and conversational' },
                { tone: 'Brief', desc: 'Short, concise, and straight to the point' },
              ].map((item) => (
                <div
                  key={item.tone}
                  onClick={() => setReplyTone(item.tone as any)}
                  className={`p-5 rounded-2xl border-2 cursor-pointer transition-all space-y-2 ${
                    replyTone === item.tone
                      ? 'border-zinc-900 bg-zinc-900 text-white shadow-md'
                      : 'border-[#EAE3D5] bg-[#EFE9DE]/60 text-zinc-900 hover:border-zinc-400'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-extrabold text-sm">{item.tone}</span>
                    {replyTone === item.tone && <Check className="w-4 h-4 text-amber-400" />}
                  </div>
                  <p className={`text-xs ${replyTone === item.tone ? 'text-zinc-300' : 'text-zinc-500'}`}>
                    {item.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Navigation Buttons Bottom */}
        <div className="pt-6 border-t border-[#EAE3D5] flex items-center justify-between">
          {currentStep > 1 ? (
            <button
              onClick={() => setCurrentStep((prev) => prev - 1)}
              className="bg-[#EFE9DE] hover:bg-[#E4DCCF] text-zinc-700 font-bold px-5 py-2.5 rounded-xl text-xs flex items-center gap-2 transition-all"
            >
              <ArrowLeft className="w-4 h-4" /> Back
            </button>
          ) : (
            <div></div>
          )}

          {currentStep < 4 ? (
            <button
              onClick={() => setCurrentStep((prev) => prev + 1)}
              className="bg-zinc-900 hover:bg-zinc-800 text-white font-bold px-6 py-2.5 rounded-xl text-xs flex items-center gap-2 shadow-md transition-all"
            >
              Next <ArrowRight className="w-4 h-4 text-amber-400" />
            </button>
          ) : (
            <button
              onClick={handleFinishSetup}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-7 py-3 rounded-xl text-xs flex items-center gap-2 shadow-md transition-all"
            >
              <span>Finish Setup</span>
              <Check className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
