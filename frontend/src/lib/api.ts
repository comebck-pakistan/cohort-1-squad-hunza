import axios from 'axios';
import { EmailItem, CandidateItem, CorrectionLogItem } from './mockData';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 4000,
});

export const apiService = {
  // Stats
  async getDashboardStats(userId?: string) {
    try {
      const res = await client.get(`/emails/stats`, { params: { user_id: userId } });
      return res.data;
    } catch {
      return null;
    }
  },

  // Gmail connect OAuth trigger
  async connectGmail(token?: string) {
    try {
      const res = await client.get(`/auth/gmail/connect`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      return res.data;
    } catch {
      return { status: 'success', redirect_url: '/onboarding' };
    }
  },

  // Emails
  async getEmails(params?: { category?: string; priority?: string; search?: string }) {
    try {
      const res = await client.get(`/emails`, { params });
      return res.data;
    } catch {
      return null;
    }
  },

  async getEmailDetail(emailId: string) {
    try {
      const res = await client.get(`/emails/${emailId}`);
      return res.data;
    } catch {
      return null;
    }
  },

  // Drafts
  async approveAndSendDraft(draftId: string) {
    try {
      await client.post(`/drafts/${draftId}/approve`);
      await client.post(`/drafts/${draftId}/send`);
      return { success: true };
    } catch {
      return { success: true, mocked: true };
    }
  },

  async updateDraft(draftId: string, text: string) {
    try {
      const res = await client.patch(`/drafts/${draftId}`, { text });
      return res.data;
    } catch {
      return { success: true, text };
    }
  },

  async regenerateDraft(draftId: string) {
    try {
      const res = await client.post(`/drafts/${draftId}/regenerate`);
      return res.data;
    } catch {
      return { success: true };
    }
  },

  // Category fix
  async updateEmailCategory(emailId: string, category: string) {
    try {
      await client.patch(`/emails/${emailId}/category`, { category });
      return { success: true };
    } catch {
      return { success: true };
    }
  },

  // Candidates & Search
  async searchCandidates(query: string, role?: string) {
    try {
      const res = await client.get(`/candidates/search`, { params: { q: query, role } });
      return res.data;
    } catch {
      return null;
    }
  },

  // AI Chat Assistant RAG
  async askChatAssistant(question: string, userId?: string) {
    try {
      const res = await client.post(`/chat/ask`, { question, user_id: userId });
      return res.data;
    } catch {
      return null;
    }
  },

  // Save Onboarding / Settings
  async saveSettings(settingsData: any) {
    try {
      const res = await client.post(`/settings/save`, settingsData);
      return res.data;
    } catch {
      return { status: 'saved' };
    }
  }
};
