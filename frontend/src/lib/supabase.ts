import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://wanvhvtdpynebwlvorpw.supabase.co';
const supabasePublishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || 'sb_publishable_Od070Oxf-EJJJg7OmxC3Sg_4Web2XF2';

export const supabase = createClient(supabaseUrl, supabasePublishableKey);
