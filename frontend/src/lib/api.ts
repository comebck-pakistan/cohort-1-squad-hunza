import axios from 'axios';
import { supabase } from './supabase';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000, 
});

client.interceptors.request.use(async (config) => {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }

  return config;
});

export const apiService = {
  // Stats
  async getDashboardStats(userId?: string) {
    const res = await client.get(`/emails/stats`, { params: { user_id: userId } });
    return res.data;
  },

  // Gmail connect OAuth trigger
  async connectGmail(token?: string) {
    const res = await client.get(`/gmail/connect`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return res.data;
  },

  async getGmailStatus() {
    const res = await client.get(`/gmail/status`);
    return res.data;
  },

  // Emails
  async getEmails(params?: { category?: string; priority?: string; search?: string }) {
    const res = await client.get(`/emails`, { params });
    return res.data;
  },

  async getEmailDetail(emailId: string) {
    const res = await client.get(`/emails/${emailId}`);
    return res.data;
  },

  // Drafts
  async getDraftForEmail(emailId: string) {
    const res = await client.get(`/drafts/by-email/${emailId}`);
    return res.data;
  },

  async approveAndSendDraft(draftId: string) {
    const res = await client.post(`/drafts/${draftId}/approve`);
    return res.data;
  },

  async updateDraft(draftId: string, text: string) {
    const res = await client.patch(`/drafts/${draftId}`, { draft_body: text });
    return res.data;
  },

  async regenerateDraft(draftId: string) {
    const res = await client.post(`/drafts/${draftId}/regenerate`);
    return res.data;
  },

  // Category fix
  async updateEmailCategory(emailId: string, category: string) {
    const res = await client.patch(`/emails/${emailId}/category`, { category });
    return res.data;
  },

  // Candidates & Search
  async searchCandidates(query: string, role?: string) {
    const res = await client.get(`/candidates/search`, { params: { q: query, role } });
    return res.data;
  },

  // AI Chat Assistant RAG
  async askChatAssistant(question: string, userId?: string) {
    const res = await client.post(`/chat/ask`, { question, user_id: userId });
    return res.data;
  },

  // Save Onboarding / Settings
  async saveSettings(settingsData: any) {
    const res = await client.post(`/settings/save`, settingsData);
    return res.data;
  },
};

