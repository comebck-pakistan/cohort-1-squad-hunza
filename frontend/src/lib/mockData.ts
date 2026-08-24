export interface EmailItem {
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
  attachmentName?: string;
  attachmentSize?: string;
  draftReply?: {
    id: string;
    text: string;
    tone: 'Formal' | 'Friendly' | 'Brief';
    status: 'pending' | 'approved' | 'sent' | 'rejected';
  };
}

export interface CandidateItem {
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
  educationDegree: string | null;
  educationInstitution: string | null;
  educationGpa: string | null;
  portfolioUrl: string | null;
}

export interface CorrectionLogItem {
  id: string;
  date: string;
  original: string;
  corrected: string;
  correctedBy: string;
  type: 'Draft Edit' | 'Category Fix';
  emailSubject: string;
}

export const INITIAL_CATEGORIES = [
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

export const INITIAL_ROLES = [
  'AI Engineer',
  'Backend Developer',
  'Frontend Engineer',
  'UX/UI Designer',
  'Product Manager',
  'DevOps Specialist',
];

export const INITIAL_EMAILS: EmailItem[] = [
  {
    id: 'em-101',
    senderName: 'John Smith',
    senderEmail: 'john.smith@gmail.com',
    avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
    subject: 'Applying for AI Engineer Position - John Smith',
    category: 'New Applicant',
    priority: 'Medium',
    status: 'Draft Ready',
    date: 'Jul 28, 2026',
    body: `Hi HR Team,\n\nI am writing to express my strong interest in the AI Engineer position at your company. With over 4 years of hands-on experience building LLM pipelines, fine-tuning PyTorch models, and deploying RAG architectures on AWS, I am confident I can make an immediate impact on your team.\n\nI have attached my resume for your review. Please let me know if you would be available for a brief introductory call.\n\nBest regards,\nJohn Smith\n+1 (555) 234-5678`,
    attachmentName: 'Resume_John_Smith_AI_Engineer.pdf',
    attachmentSize: '1.4 MB',
    draftReply: {
      id: 'df-101',
      text: `Dear John,\n\nThank you for reaching out and applying for the AI Engineer role at our company. We were impressed by your background in LLM architectures and PyTorch fine-tuning.\n\nOur recruiting team would love to invite you to a 30-minute initial screening call next week. Please let us know your availability for Tuesday or Wednesday afternoon.\n\nWarm regards,\nHR Recruiting Team`,
      tone: 'Friendly',
      status: 'pending',
    },
  },
  {
    id: 'em-102',
    senderName: 'Jane Doe',
    senderEmail: 'jane.doe@techconsulting.io',
    avatarUrl: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80',
    subject: 'Question regarding salary range & remote policy for Backend Developer',
    category: 'General Inquiry',
    priority: 'High',
    status: 'No Reply',
    date: 'Jul 28, 2026',
    body: `Hello,\n\nI am currently evaluating senior backend roles and noticed your job posting for Senior Backend Developer. Could you kindly provide details regarding the compensation band for this role and whether hybrid/remote work is supported?\n\nThank you,\nJane Doe`,
    attachmentName: undefined,
    draftReply: {
      id: 'df-102',
      text: `Dear Jane,\n\nThank you for your inquiry regarding our Senior Backend Developer position. The compensation range for this level is $140,000 - $175,000 base salary, depending on candidate experience and technical depth.\n\nWe operate on a flexible hybrid work model with 2 days in-office per week or full remote options for US-based staff. We'd love to review your application!\n\nBest regards,\nHR Team`,
      tone: 'Formal',
      status: 'pending',
    },
  },
  {
    id: 'em-103',
    senderName: 'Spam Bot Network',
    senderEmail: 'offers@promo-growth-boost.net',
    subject: 'Buy cheap watches & candidate leads 90% discount',
    category: 'Spam',
    priority: 'Low',
    status: 'Filtered',
    date: 'Jul 27, 2026',
    body: `Special offer! Increase your candidate response rate by 500% with our automated spam blasting tool. Click here to claim your $50 credit today!`,
  },
  {
    id: 'em-104',
    senderName: 'Marcus Vance',
    senderEmail: 'marcus.vance@devmail.org',
    avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80',
    subject: 'Accepted: Offer Letter - Lead UX/UI Designer',
    category: 'Offer Acceptance',
    priority: 'High',
    status: 'Draft Ready',
    date: 'Jul 27, 2026',
    body: `Hi Sarah,\n\nI am delighted to accept the offer for the Lead UX/UI Designer position! I have signed and attached the executed offer letter. I look forward to starting on August 15th as discussed.\n\nThank you again for this wonderful opportunity.\n\nBest,\nMarcus Vance`,
    attachmentName: 'Signed_Offer_Letter_MarcusVance.pdf',
    attachmentSize: '480 KB',
    draftReply: {
      id: 'df-104',
      text: `Hi Marcus,\n\nWonderful news! We are thrilled to welcome you to the team as our Lead UX/UI Designer. We have received your signed offer letter.\n\nOur People Ops team will send over your onboarding packet and hardware preference form later this week. See you on August 15th!\n\nWarmly,\nSarah & HR Team`,
      tone: 'Friendly',
      status: 'pending',
    },
  },
  {
    id: 'em-105',
    senderName: 'Elena Rostova',
    senderEmail: 'elena.rostova@cloudtech.com',
    avatarUrl: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150&auto=format&fit=crop&q=80',
    subject: 'Reschedule request for Tech Interview round 2',
    category: 'Interview Reschedule',
    priority: 'High',
    status: 'Draft Ready',
    date: 'Jul 26, 2026',
    body: `Hi HR Team,\n\nUnfortunately, I have an unexpected scheduling conflict for our scheduled technical round tomorrow at 2:00 PM EST. Would it be possible to reschedule to Thursday or Friday at any time after 11:00 AM?\n\nApologies for the inconvenience.\n\nBest,\nElena`,
    attachmentName: undefined,
    draftReply: {
      id: 'df-105',
      text: `Dear Elena,\n\nNo problem at all! We completely understand. We have rescheduled your Technical Interview Round 2 to Thursday, July 30th at 1:00 PM EST.\n\nA updated calendar invitation with Google Meet details has been sent to your email.\n\nBest of luck,\nHR Scheduling Team`,
      tone: 'Brief',
      status: 'pending',
    },
  },
  {
    id: 'em-106',
    senderName: 'David Kim',
    senderEmail: 'david.kim@fullstackdev.co',
    avatarUrl: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80',
    subject: 'Submitted: Code Challenge & Portfolio links',
    category: 'Documents Submitted',
    priority: 'Medium',
    status: 'Draft Ready',
    date: 'Jul 26, 2026',
    body: `Hello Team,\n\nI have finished the frontend coding assessment for the Senior Frontend Engineer position. You can inspect the live demo at https://david-kim-demo.vercel.app and the GitHub repo attached.\n\nLooking forward to your feedback!\n\nBest,\nDavid Kim`,
    attachmentName: 'Coding_Challenge_David_Kim.zip',
    attachmentSize: '3.1 MB',
    draftReply: {
      id: 'df-106',
      text: `Hi David,\n\nThank you for submitting your coding assessment! We've forwarded your repository and live demo to our engineering leads for evaluation.\n\nWe aim to get back to you with next steps within 48 hours.\n\nBest regards,\nHR Recruiting`,
      tone: 'Formal',
      status: 'pending',
    },
  },
];

export const INITIAL_CANDIDATES: CandidateItem[] = [
  {
    id: 'cand-1',
    name: 'John Smith',
    role: 'AI Engineer',
    email: 'john.smith@gmail.com',
    phone: '+1 (555) 234-5678',
    experienceYears: 4,
    skills: ['Python', 'PyTorch', 'RAG Architecture', 'LangChain', 'AWS Bedrock', 'FastAPI'],
    appliedDate: 'Jul 28, 2026',
    status: 'Reviewing',
    resumeUrl: 'https://wanvhvtdpynebwlvorpw.supabase.co/storage/v1/object/public/resumes/john_smith_resume.pdf',
    resumeFileName: 'Resume_John_Smith_AI_Engineer.pdf',
    summary: '4+ years of experience constructing production LLM inference pipelines, fine-tuning Llama-3 models, and deploying vector indexes with Pinecone.',
    emailId: 'em-101',
    avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
    educationDegree: 'B.S. Computer Science',
    educationInstitution: 'University of Washington',
    educationGpa: '3.8',
    portfolioUrl: null,
  },
  {
    id: 'cand-2',
    name: 'Jane Doe',
    role: 'Backend Developer',
    email: 'jane.doe@techconsulting.io',
    phone: '+1 (555) 876-5432',
    experienceYears: 6,
    skills: ['Node.js', 'Go', 'PostgreSQL', 'Docker', 'Kubernetes', 'Microservices'],
    appliedDate: 'Jul 28, 2026',
    status: 'Interviewing',
    resumeUrl: 'https://wanvhvtdpynebwlvorpw.supabase.co/storage/v1/object/public/resumes/jane_doe_resume.pdf',
    resumeFileName: 'Resume_Jane_Doe_Backend.pdf',
    summary: 'Senior Backend Specialist with expertise in distributed microservice architectures, high-throughput gRPC pipelines, and cloud native Kubernetes.',
    emailId: 'em-102',
    avatarUrl: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80',
    educationDegree: 'M.S. Software Engineering',
    educationInstitution: 'Georgia Tech',
    educationGpa: '3.9',
    portfolioUrl: null,
  },
  {
    id: 'cand-3',
    name: 'Marcus Vance',
    role: 'UX/UI Designer',
    email: 'marcus.vance@devmail.org',
    phone: '+1 (555) 432-1098',
    experienceYears: 5,
    skills: ['Figma', 'Design Systems', 'User Research', 'Prototyping', 'Tailwind CSS'],
    appliedDate: 'Jul 27, 2026',
    status: 'Hired',
    resumeUrl: 'https://wanvhvtdpynebwlvorpw.supabase.co/storage/v1/object/public/resumes/marcus_vance_resume.pdf',
    resumeFileName: 'Portfolio_Marcus_Vance.pdf',
    summary: 'Lead UX/UI Designer who built scalable design systems for enterprise SaaS applications used by over 500k monthly active users.',
    emailId: 'em-104',
    avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80',
    educationDegree: 'B.A. Interaction Design',
    educationInstitution: 'School of Visual Arts',
    educationGpa: '3.7',
    portfolioUrl: null,
  },
  {
    id: 'cand-4',
    name: 'Elena Rostova',
    role: 'AI Engineer',
    email: 'elena.rostova@cloudtech.com',
    phone: '+1 (555) 901-2345',
    experienceYears: 3,
    skills: ['Python', 'TensorFlow', 'Computer Vision', 'OpenCV', 'FastAPI'],
    appliedDate: 'Jul 26, 2026',
    status: 'Interviewing',
    resumeUrl: 'https://wanvhvtdpynebwlvorpw.supabase.co/storage/v1/object/public/resumes/elena_rostova.pdf',
    resumeFileName: 'Resume_Elena_Rostova.pdf',
    summary: 'Applied Machine Learning researcher with emphasis on multimodal embeddings and real-time computer vision inference.',
    emailId: 'em-105',
    avatarUrl: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150&auto=format&fit=crop&q=80',
    educationDegree: 'M.S. Computer Vision',
    educationInstitution: 'University of Michigan',
    educationGpa: '3.9',
    portfolioUrl: null,
  },
];

export const INITIAL_CORRECTIONS: CorrectionLogItem[] = [
  {
    id: 'corr-1',
    date: 'Jul 27, 2026',
    original: 'Dear Applicant, thank you for your submission...',
    corrected: 'Personalized candidate name and added specific interview date slot options.',
    correctedBy: 'Sarah (HR Manager)',
    type: 'Draft Edit',
    emailSubject: 'Applying for AI Engineer Position',
  },
  {
    id: 'corr-2',
    date: 'Jul 26, 2026',
    original: 'Spam',
    corrected: 'General Inquiry',
    correctedBy: 'Sarah (HR Manager)',
    type: 'Category Fix',
    emailSubject: 'Inquiry regarding healthcare benefits package',
  },
];

export const CHART_VOLUME_DATA = [
  { day: 'Mon', Applicants: 12, Interviews: 5, Inquiries: 4, Spam: 2 },
  { day: 'Tue', Applicants: 18, Interviews: 8, Inquiries: 6, Spam: 3 },
  { day: 'Wed', Applicants: 15, Interviews: 10, Inquiries: 5, Spam: 1 },
  { day: 'Thu', Applicants: 22, Interviews: 12, Inquiries: 8, Spam: 4 },
  { day: 'Fri', Applicants: 24, Interviews: 14, Inquiries: 6, Spam: 3 },
  { day: 'Sat', Applicants: 8, Interviews: 3, Inquiries: 2, Spam: 1 },
  { day: 'Sun', Applicants: 6, Interviews: 2, Inquiries: 1, Spam: 1 },
];

export const CHART_30DAY_VOLUME_DATA = [
  { day: 'Week 1', Applicants: 68, Interviews: 24, Inquiries: 19, Spam: 9 },
  { day: 'Week 2', Applicants: 84, Interviews: 32, Inquiries: 25, Spam: 12 },
  { day: 'Week 3', Applicants: 105, Interviews: 41, Inquiries: 30, Spam: 14 },
  { day: 'Week 4', Applicants: 122, Interviews: 53, Inquiries: 38, Spam: 15 },
];

