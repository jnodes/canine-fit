# Canine.Fit - Supabase Setup Script
# Run this from the project root directory

# ============================================
# STEP 1: Install Supabase CLI
# ============================================
# Windows (with scoop):
scoop install supabase

# Windows (with npm):
npm install -g supabase

# macOS:
brew install supabase/tap/supabase

# Linux:
npm install -g supabase

# ============================================
# STEP 2: Login to Supabase
# ============================================
supabase login
# Opens browser for authentication

# ============================================
# STEP 3: Link to your Supabase project
# ============================================
# Get your project ref from: https://supabase.com/dashboard → Settings → General
cd supabase
supabase link --project-ref YOUR_PROJECT_REF

# ============================================
# STEP 4: Push migrations to remote database
# ============================================
supabase db push

# This will:
# - Connect to your remote Supabase database
# - Run all migrations in supabase/migrations/
# - Apply the schema with RLS policies

# ============================================
# STEP 5: Generate types (optional but recommended)
# ============================================
supabase gen types typescript --project-id YOUR_PROJECT_REF > frontend/src/types/supabase.ts

# ============================================
# VERIFY: Check database status
# ============================================
supabase db status

# ============================================
# OTHER USEFUL COMMANDS
# ============================================

# Reset database (careful - deletes all data!)
supabase db reset

# Start local development environment
supabase start

# Stop local environment
supabase stop

# Inspect database tables
supabase db dump -f backup.sql

# Run migration status
supabase migration list
