import { createClient, type SupabaseClient } from '@supabase/supabase-js'

// The web bundle only ever holds the anon key: it reads the public `v_*` views
// and nothing else. A missing configuration is a state, not a crash: without
// these variables every hook renders its "sin datos" state.

const supabaseUrl: string | null = import.meta.env.VITE_SUPABASE_URL ?? null
const supabaseAnonKey: string | null = import.meta.env.VITE_SUPABASE_ANON_KEY ?? null

export const isConfigured: boolean = supabaseUrl !== null && supabaseAnonKey !== null

export const supabase: SupabaseClient | null =
  isConfigured && supabaseUrl !== null && supabaseAnonKey !== null
    ? createClient(supabaseUrl, supabaseAnonKey)
    : null
