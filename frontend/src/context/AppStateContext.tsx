import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  EmailItem,
  CandidateItem,
  CorrectionLogItem,
  INITIAL_CATEGORIES,
  INITIAL_ROLES,
  INITIAL_EMAILS,
  INITIAL_CANDIDATES,
  INITIAL_CORRECTIONS,
} from '../lib/mockData';

interface OnboardingState {
  completed: boolean;
  categories: string[];
  roles: string[];
  jobDescriptions: Record<string, string>;
  replyTone: 'Formal' | 'Friendly' | 'Brief';
}

interface AppStateContextType {
  isGmailConnected: boolean;
  setGmailConnected: (val: boolean) => void;
  onboarding: OnboardingState;
  updateOnboarding: (data: Partial<OnboardingState>) => void;
  emails: EmailItem[];
  candidates: CandidateItem[];
  corrections: CorrectionLogItem[];
  categories: string[];
  jobRoles: string[];
  addCategory: (cat: string) => void;
  removeCategory: (cat: string) => void;
  addJobRole: (role: string) => void;
  removeJobRole: (role: string) => void;
  approveDraft: (emailId: string) => void;
  discardDraft: (emailId: string) => void;
  updateDraftText: (emailId: string, text: string) => void;
  updateEmailCategory: (emailId: string, newCategory: string) => void;
  regenerateDraftText: (emailId: string) => void;
  generateDraft: (emailId: string) => Promise<void>;
  resumeModalUrl: string | null;
  setResumeModalUrl: (url: string | null) => void;
  activeResumeName: string | null;
  setActiveResumeName: (name: string | null) => void;
  toastMessage: string | null;
  showToast: (msg: string) => void;
}

const AppStateContext = createContext<AppStateContextType | undefined>(undefined);

export const AppStateProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isGmailConnected, setGmailConnected] = useState<boolean>(true);
  const [categories, setCategories] = useState<string[]>(INITIAL_CATEGORIES);
  const [jobRoles, setJobRoles] = useState<string[]>(INITIAL_ROLES);
  const [emails, setEmails] = useState<EmailItem[]>(INITIAL_EMAILS);
  const [candidates, setCandidates] = useState<CandidateItem[]>(INITIAL_CANDIDATES);
  const [corrections, setCorrections] = useState<CorrectionLogItem[]>(INITIAL_CORRECTIONS);

  const [onboarding, setOnboarding] = useState<OnboardingState>({
    completed: true,
    categories: INITIAL_CATEGORIES,
    roles: INITIAL_ROLES,
    jobDescriptions: {
      'AI Engineer': 'Seeking AI Engineer with PyTorch, RAG, and LLM fine-tuning experience.',
      'Backend Developer': 'Senior Golang / Node.js developer needed for high scale APIs.',
    },
    replyTone: 'Friendly',
  });

  const [resumeModalUrl, setResumeModalUrl] = useState<string | null>(null);
  const [activeResumeName, setActiveResumeName] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const updateOnboarding = (data: Partial<OnboardingState>) => {
    setOnboarding((prev) => ({ ...prev, ...data }));
  };

  const addCategory = (cat: string) => {
    if (!cat || categories.includes(cat)) return;
    setCategories((prev) => [...prev, cat]);
    showToast(`Category "${cat}" added successfully`);
  };

  const removeCategory = (cat: string) => {
    setCategories((prev) => prev.filter((c) => c !== cat));
    showToast(`Category "${cat}" removed`);
  };

  const addJobRole = (role: string) => {
    if (!role || jobRoles.includes(role)) return;
    setJobRoles((prev) => [...prev, role]);
    showToast(`Role "${role}" added`);
  };

  const removeJobRole = (role: string) => {
    setJobRoles((prev) => prev.filter((r) => r !== role));
    showToast(`Role "${role}" removed`);
  };

  const approveDraft = (emailId: string) => {
    setEmails((prev) =>
      prev.map((e) => {
        if (e.id === emailId && e.draftReply) {
          return {
            ...e,
            status: 'Approved & Sent',
            draftReply: { ...e.draftReply, status: 'approved' },
          };
        }
        return e;
      })
    );
    const email = emails.find((e) => e.id === emailId);
    showToast(`✅ Draft approved & sent to ${email?.senderEmail || 'candidate'}!`);
  };

  const discardDraft = (emailId: string) => {
    setEmails((prev) =>
      prev.map((e) => {
        if (e.id === emailId) {
          return { ...e, draftReply: undefined, status: 'No Reply' };
        }
        return e;
      })
    );
    showToast(`Draft discarded.`);
  };

  const updateDraftText = (emailId: string, text: string) => {
    setEmails((prev) =>
      prev.map((e) => {
        if (e.id === emailId && e.draftReply) {
          return {
            ...e,
            draftReply: { ...e.draftReply, text },
          };
        }
        return e;
      })
    );
    // Add audit log
    const email = emails.find((e) => e.id === emailId);
    if (email) {
      setCorrections((prev) => [
        {
          id: `corr-${Date.now()}`,
          date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
          original: email.draftReply?.text.slice(0, 40) + '...',
          corrected: text.slice(0, 40) + '...',
          correctedBy: 'HR User',
          type: 'Draft Edit',
          emailSubject: email.subject,
        },
        ...prev,
      ]);
    }
    showToast(`Draft edits saved!`);
  };

  const updateEmailCategory = (emailId: string, newCategory: string) => {
    const email = emails.find((e) => e.id === emailId);
    if (!email) return;
    const oldCategory = email.category;

    setEmails((prev) =>
      prev.map((e) => (e.id === emailId ? { ...e, category: newCategory } : e))
    );

    setCorrections((prev) => [
      {
        id: `corr-${Date.now()}`,
        date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
        original: oldCategory,
        corrected: newCategory,
        correctedBy: 'HR User',
        type: 'Category Fix',
        emailSubject: email.subject,
      },
      ...prev,
    ]);

    showToast(`Category updated to "${newCategory}"`);
  };

  const regenerateDraftText = (emailId: string) => {
    setEmails((prev) =>
      prev.map((e) => {
        if (e.id === emailId && e.draftReply) {
          const freshText = `Dear ${e.senderName.split(' ')[0]},\n\nThank you for reaching out regarding "${e.subject}". We have reviewed your details and our team is keen to proceed.\n\nCould you confirm your availability for a 15-minute quick call next week?\n\nBest regards,\nHR Talent Team`;
          return {
            ...e,
            draftReply: { ...e.draftReply, text: freshText },
          };
        }
        return e;
      })
    );
    showToast(`✨ AI Draft regenerated with updated tone.`);
  };

  const generateDraft = async (emailId: string) => {
    // Attempt backend API call if token available, or gracefully fallback
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      await fetch(`${apiUrl}/drafts/generate/${emailId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      }).catch(() => {
        // Fallback for offline / mock mode
      });
    } catch (err) {
      console.warn('API call failed, falling back to client draft generation', err);
    }

    const email = emails.find((e) => e.id === emailId);
    const newDraftText = `Dear ${email ? email.senderName.split(' ')[0] : 'Applicant'},\n\nThank you for reaching out to us. We have received your message regarding "${email?.subject || 'your inquiry'}" and are currently reviewing your details.\n\nOur recruiting team will get back to you shortly with next steps.\n\nBest regards,\nHR Team`;

    setEmails((prev) =>
      prev.map((e) => {
        if (e.id === emailId) {
          return {
            ...e,
            status: 'Draft Ready',
            draftReply: {
              id: `draft-${Date.now()}`,
              emailId: emailId,
              text: newDraftText,
              status: 'pending',
              createdAt: new Date().toISOString(),
              tone: 'Friendly',
            },
          };
        }
        return e;
      })
    );
    showToast(`✨ AI Draft Generated Successfully!`);
  };

  return (
    <AppStateContext.Provider
      value={{
        isGmailConnected,
        setGmailConnected,
        onboarding,
        updateOnboarding,
        emails,
        candidates,
        corrections,
        categories,
        jobRoles,
        addCategory,
        removeCategory,
        addJobRole,
        removeJobRole,
        approveDraft,
        discardDraft,
        updateDraftText,
        updateEmailCategory,
        regenerateDraftText,
        generateDraft,
        resumeModalUrl,
        setResumeModalUrl,
        activeResumeName,
        setActiveResumeName,
        toastMessage,
        showToast,
      }}
    >
      {children}
    </AppStateContext.Provider>
  );
};

export const useAppState = () => {
  const context = useContext(AppStateContext);
  if (!context) {
    throw new Error('useAppState must be used within an AppStateProvider');
  }
  return context;
};
