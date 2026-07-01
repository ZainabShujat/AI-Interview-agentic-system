import { createClient } from '@supabase/supabase-js';

const supabaseUrl = (import.meta.env.VITE_SUPABASE_URL as string) || 'https://khilvmvhaibhfuthbakl.supabase.co';
const supabaseAnonKey = (import.meta.env.VITE_SUPABASE_ANON_KEY as string) || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtoaWx2bXZoYWliaGZ1dGhiYWtsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIxOTYwNTEsImV4cCI6MjA5Nzc3MjA1MX0.0MT0nFQAYWD9XWjdOd1A1JZopjVkptrM35-ysMge1ww';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
