import React, { createContext, useContext, useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { apiService } from '../lib/api';

interface EmailItem {
  id: string;
  senderName: string;
  senderEmail: string;
  avatarUrl?: string;
  subject: string;
  category: string;
  priority: 'High' | 'Medium' | 'Low';
  status: 'Draft Ready' | 'No Reply' | 'Filtered' | 'Approved & Sent' | 'Rejected';
  date: string;
  body: string;
  receivedAtRaw?: string;
  attachmentName?: string;
  attachmentSize?: string;
  draftReply?: {
    id: string;
    text: string;
    tone: 'Formal' | 'Friendly' | 'Brief';
    status: 'pending' | 'approved' | 'sent' | 'rejected';
  };
}

interface CandidateItem {
  id: string;
  name: string;
  role: string;
  email: string;
  phone: string;
  experienceYears: number;
  skills: string[];
  appliedDate: string;
  status: 'Interviewing' | 'Reviewing' | 'Hired' | 'Rejected';
  resumeUrl: string;
  resumeFileName: string;
  summary: string;
  emailId?: string;
  avatarUrl: string;
}

interface CorrectionLogItem {
  id: string;
  date: string;
  original: string;
  corrected: string;
  correctedBy: string;
  type: 'Draft Edit' | 'Category Fix';
  emailSubject: string;
}

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
  gmailAddress: string | null;
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
  approveDraft: (emailId: string) => Promise<void>;
  discardDraft: (emailId: string) => void;
  updateDraftText: (emailId: string, text: string) => Promise<void>;
  updateEmailCategory: (emailId: string, newCategory: string) => void;
  regenerateDraftText: (emailId: string) => Promise<void>;
  generateDraft: (emailId: string) => Promise<void>;
  resumeModalUrl: string | null;
  setResumeModalUrl: (url: string | null) => void;
  activeResumeName: string | null;
  setActiveResumeName: (name: string | null) => void;
  toastMessage: string | null;
  showToast: (msg: string) => void;
}

const AppStateContext = createContext<AppStateContextType | undefined>(undefined);

const DEFAULT_CATEGORIES = [
  'New Applicant',
  'Candidate Follow-up',
  'Interview Scheduling',
  'Interview Reschedule',
  'Documents Submitted',
  'Offer Acceptance',
  'Offer Rejection',
  'General Inquiry',
  'Referral',
  'Candidate Withdrawal',
];

const DEFAULT_ROLES = [
  'AI Engineer',
  'Backend Developer',
  'Frontend Engineer',
  'UX/UI Designer',
  'Product Manager',
  'DevOps Specialist',
];

const mapBackendEmails = (emails: any[]): EmailItem[] =>
  emails.map((email) => ({
    id: email.id,
    senderName: email.sender_name || email.sender_email || 'Unknown Applicant',
    senderEmail: email.sender_email || '',
    avatarUrl: undefined,
    subject: email.subject || 'No subject',
    category: email.category || 'General Inquiry',
    priority: email.priority || 'Medium',
    status: 'No Reply',
    date: email.received_at
      ? new Date(email.received_at).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        })
      : '',
    receivedAtRaw: email.received_at,
    body: email.body_text || '',
  }));

export const AppStateProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isGmailConnected, setGmailConnected] = useState<boolean>(false);
  const [gmailAddress, setGmailAddress] = useState<string | null>(null);
  const [categories, setCategories] = useState<string[]>(DEFAULT_CATEGORIES);
  const [jobRoles, setJobRoles] = useState<string[]>(DEFAULT_ROLES);
  const [emails, setEmails] = useState<EmailItem[]>([]);
  const [candidates, setCandidates] = useState<CandidateItem[]>([]);
  const [corrections, setCorrections] = useState<CorrectionLogItem[]>([]);
  const [onboarding, setOnboarding] = useState<OnboardingState>({
    completed: false,
    categories: DEFAULT_CATEGORIES,
    roles: DEFAULT_ROLES,
    jobDescriptions: {
      'AI Engineer': 'Seeking AI Engineer with PyTorch, RAG, and LLM fine-tuning experience.',
      'Backend Developer': 'Senior Golang / Node.js developer needed for high scale APIs.',
    },
    replyTone: 'Friendly',
  });

  const [resumeModalUrl, setResumeModalUrl] = useState<string | null>(null);
  const [activeResumeName, setActiveResumeName] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

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

  const approveDraft = async (emailId: string) => {
    const email = emails.find((e) => e.id === emailId);
    if (!email?.draftReply?.id) {
      showToast('No draft available to approve.');
      return;
    }

    try {
      await apiService.approveAndSendDraft(email.draftReply.id);
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
      showToast(`✅ Draft approved & sent to ${email.senderEmail || 'candidate'}!`);
    } catch (err) {
      console.error('Approve draft failed', err);
      showToast('Failed to approve draft.');
    }
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
    showToast('Draft discarded.');
  };

  const updateDraftText = async (emailId: string, text: string) => {
    const email = emails.find((e) => e.id === emailId);
    if (!email?.draftReply?.id) {
      showToast('No draft available to update.');
      return;
    }

    try {
      await apiService.updateDraft(email.draftReply.id, text);
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

      if (email) {
        setCorrections((prev) => [
          {
            id: `corr-${Date.now()}`,
            date: new Date().toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
            }),
            original: email.draftReply?.text.slice(0, 40) + '...',
            corrected: text.slice(0, 40) + '...',
            correctedBy: 'HR User',
            type: 'Draft Edit',
            emailSubject: email.subject,
          },
          ...prev,
        ]);
      }
      showToast('Draft edits saved!');
    } catch (err) {
      console.error('Update draft failed', err);
      showToast('Failed to save draft edits.');
    }
  };

const updateEmailCategory = async (emailId: string, newCategory: string) => {
  const email = emails.find((e) => e.id === emailId);
  if (!email) return;
  const oldCategory = email.category;

  setEmails((prev) => prev.map((e) => (e.id === emailId ? { ...e, category: newCategory } : e)));

  try {
    await apiService.updateEmailCategory(emailId, newCategory);
  } catch (err) {
    setEmails((prev) => prev.map((e) => (e.id === emailId ? { ...e, category: oldCategory } : e)));
    showToast('Failed to update category — please try again');
    return;
  }

  setCorrections((prev) => [/* ...unchanged... */]);
  showToast(`Category updated to "${newCategory}"`);
};

  const regenerateDraftText = async (emailId: string) => {
    const email = emails.find((e) => e.id === emailId);
    if (!email?.draftReply?.id) {
      showToast('No draft available to regenerate.');
      return;
    }

    try {
      const result = await apiService.regenerateDraft(email.draftReply.id);
      const nextText = result?.text ?? email.draftReply.text;
      setEmails((prev) =>
        prev.map((e) => {
          if (e.id === emailId && e.draftReply) {
            return { ...e, draftReply: { ...e.draftReply, text: nextText } };
          }
          return e;
        })
      );
      showToast('✨ Draft regenerated successfully.');
    } catch (err) {
      console.error('Regenerate draft failed', err);
      showToast('Unable to regenerate draft from backend.');
    }
  };

  const generateDraft = async (emailId: string) => {
  try {
    const draft = await apiService.generateDraftForEmail(emailId);
    if (draft?.id) {
      setEmails((prev) =>
        prev.map((e) => {
          if (e.id === emailId) {
            return {
              ...e,
              status: 'Draft Ready',
              draftReply: {
                id: draft.id,
                text: draft.draft_body || '',
                tone: 'Friendly',
                status: 'pending',
              },
            };
          }
          return e;
        })
      );
      showToast('✨ Draft generated successfully.');
      return;
    }
  } catch (err) {
    console.error('Generate draft failed', err);
    showToast('Failed to generate draft.');
    return;
  }

  showToast('No draft available for this email yet.');
  };

  useEffect(() => {
    let mounted = true;
    const loadAppState = async () => {
      try {
        const {
          data: { session },
        } = await supabase.auth.getSession();

        if (!mounted) return;
        if (!session) {
          setIsLoading(false);
          return;
        }

        const [emailsData, gmailStatus] = await Promise.all([
          apiService.getEmails(),
          apiService.getGmailStatus(),
        ]);

        if (!mounted) return;

        setEmails(mapBackendEmails(Array.isArray(emailsData) ? emailsData : []));
        setGmailConnected(Array.isArray(gmailStatus) && gmailStatus.length > 0);

        const activeConnection = Array.isArray(gmailStatus)
          ? [...gmailStatus]
              .filter((c: any) => c.is_active)
              .sort((a: any, b: any) => new Date(b.connected_at).getTime() - new Date(a.connected_at).getTime())[0]
          : null;
          setGmailAddress(activeConnection?.gmail_address || null);
      } catch (err) {
        console.error('Failed to load app state', err);
        showToast('Unable to load backend email state.');
      } finally {
        if (mounted) setIsLoading(false);
      }
    };

    loadAppState();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!mounted) return;
      if (!session) {
        setEmails([]);
        setGmailConnected(false);
      } else {
        loadAppState();
      }
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  return (
   <AppStateContext.Provider
      value={{
        isGmailConnected,
        setGmailConnected,
        gmailAddress,
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

