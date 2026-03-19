-- Canine.Fit Database Schema for Supabase
-- Run this in the Supabase SQL Editor to create the database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USER PROFILES
-- ============================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    is_premium BOOLEAN DEFAULT FALSE,
    subscription_status TEXT,
    subscription_plan TEXT,
    subscription_expires TIMESTAMPTZ,
    stripe_customer_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- DOGS
-- ============================================
CREATE TABLE IF NOT EXISTS dogs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    breed TEXT NOT NULL,
    breed_api_id TEXT,
    date_of_birth DATE,
    weight_lbs DECIMAL(5,2),
    sex TEXT CHECK (sex IN ('male', 'female')),
    activity_level TEXT CHECK (activity_level IN ('low', 'moderate', 'high', 'very_high')),
    avatar_url TEXT,
    healthspan_score DECIMAL(5,2) DEFAULT 85.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_dogs_owner ON dogs(owner_id);
CREATE INDEX idx_dogs_breed ON dogs(breed);

-- ============================================
-- DAILY LOGS
-- ============================================
CREATE TABLE IF NOT EXISTS daily_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dog_id UUID NOT NULL REFERENCES dogs(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    mood TEXT CHECK (mood IN ('Excellent', 'Good', 'Fair', 'Low')),
    energy_level INTEGER CHECK (energy_level BETWEEN 1 AND 10),
    appetite INTEGER CHECK (appetite BETWEEN 1 AND 10),
    sleep_quality INTEGER CHECK (sleep_quality BETWEEN 1 AND 10),
    exercise_level INTEGER CHECK (exercise_level BETWEEN 1 AND 10),
    nutrition_quality INTEGER CHECK (nutrition_quality BETWEEN 1 AND 10),
    water_intake INTEGER CHECK (water_intake BETWEEN 1 AND 10),
    notes TEXT,
    logged_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(dog_id, date)
);

CREATE INDEX idx_daily_logs_dog ON daily_logs(dog_id);
CREATE INDEX idx_daily_logs_date ON daily_logs(date);

-- ============================================
-- HEALTHSPAN STATS
-- ============================================
CREATE TABLE IF NOT EXISTS healthspan_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dog_id UUID NOT NULL REFERENCES dogs(id) ON DELETE CASCADE UNIQUE,
    current_score DECIMAL(5,2) DEFAULT 85.00,
    total_points INTEGER DEFAULT 0,
    streak INTEGER DEFAULT 0,
    last_activity_date DATE,
    calculated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_healthspan_dog ON healthspan_stats(dog_id);

-- ============================================
-- LILO AI REPORTS
-- ============================================
CREATE TABLE IF NOT EXISTS lilo_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dog_id UUID NOT NULL REFERENCES dogs(id) ON DELETE CASCADE,
    mood TEXT,
    summary TEXT,
    insights JSONB,
    recommendation TEXT,
    healthspan_delta DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_lilo_reports_dog ON lilo_reports(dog_id);

-- ============================================
-- FOOD SAFETY CHECKS
-- ============================================
CREATE TABLE IF NOT EXISTS food_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dog_id UUID NOT NULL REFERENCES dogs(id) ON DELETE CASCADE,
    food_name TEXT NOT NULL,
    usda_fdc_id TEXT,
    verdict TEXT CHECK (verdict IN ('SAFE', 'CAUTION', 'TOXIC')),
    warnings TEXT[],
    nutrients JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_food_checks_dog ON food_checks(dog_id);

-- ============================================
-- SUBSCRIPTION TRANSACTIONS
-- ============================================
CREATE TABLE IF NOT EXISTS payment_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    stripe_session_id TEXT,
    stripe_subscription_id TEXT,
    amount_cents INTEGER,
    currency TEXT DEFAULT 'usd',
    status TEXT,
    plan_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_payment_user ON payment_transactions(user_id);

-- ============================================
-- LEADERBOARD DATA
-- ============================================
CREATE TABLE IF NOT EXISTS leaderboard_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dog_id UUID NOT NULL REFERENCES dogs(id) ON DELETE CASCADE,
    breed TEXT NOT NULL,
    total_points INTEGER DEFAULT 0,
    current_score DECIMAL(5,2),
    streak INTEGER DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(dog_id)
);

CREATE INDEX idx_leaderboard_breed ON leaderboard_entries(breed);
CREATE INDEX idx_leaderboard_points ON leaderboard_entries(total_points DESC);

-- ============================================
-- ROW LEVEL SECURITY POLICIES
-- ============================================

-- Enable RLS on all tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE dogs ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE healthspan_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE lilo_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE food_checks ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE leaderboard_entries ENABLE ROW LEVEL SECURITY;

-- User profiles: Users can only see/update their own profile
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

-- Dogs: Users can only access their own dogs
CREATE POLICY "Users can view own dogs" ON dogs
    FOR SELECT USING (auth.uid() = owner_id);

CREATE POLICY "Users can insert own dogs" ON dogs
    FOR INSERT WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update own dogs" ON dogs
    FOR UPDATE USING (auth.uid() = owner_id);

CREATE POLICY "Users can delete own dogs" ON dogs
    FOR DELETE USING (auth.uid() = owner_id);

-- Daily logs: Access through dog ownership
CREATE POLICY "Users can view own daily logs" ON daily_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM dogs
            WHERE dogs.id = daily_logs.dog_id
            AND dogs.owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own daily logs" ON daily_logs
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM dogs
            WHERE dogs.id = daily_logs.dog_id
            AND dogs.owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own daily logs" ON daily_logs
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM dogs
            WHERE dogs.id = daily_logs.dog_id
            AND dogs.owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own daily logs" ON daily_logs
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM dogs
            WHERE dogs.id = daily_logs.dog_id
            AND dogs.owner_id = auth.uid()
        )
    );

-- Healthspan stats: Access through dog ownership
CREATE POLICY "Users can view own healthspan stats" ON healthspan_stats
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM dogs
            WHERE dogs.id = healthspan_stats.dog_id
            AND dogs.owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own healthspan stats" ON healthspan_stats
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM dogs
            WHERE dogs.id = healthspan_stats.dog_id
            AND dogs.owner_id = auth.uid()
        )
    );

-- Lilo reports: Access through dog ownership
CREATE POLICY "Users can view own lilo reports" ON lilo_reports
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM dogs
            WHERE dogs.id = lilo_reports.dog_id
            AND dogs.owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own lilo reports" ON lilo_reports
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM dogs
            WHERE dogs.id = lilo_reports.dog_id
            AND dogs.owner_id = auth.uid()
        )
    );

-- Food checks: Access through dog ownership
CREATE POLICY "Users can view own food checks" ON food_checks
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM dogs
            WHERE dogs.id = food_checks.dog_id
            AND dogs.owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own food checks" ON food_checks
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM dogs
            WHERE dogs.id = food_checks.dog_id
            AND dogs.owner_id = auth.uid()
        )
    );

-- Payment transactions: Users can only see their own
CREATE POLICY "Users can view own transactions" ON payment_transactions
    FOR SELECT USING (auth.uid() = user_id);

-- Leaderboard: Public read, but updates require ownership
CREATE POLICY "Anyone can view leaderboard" ON leaderboard_entries
    FOR SELECT USING (true);

CREATE POLICY "Users can update own leaderboard entry" ON leaderboard_entries
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM dogs
            WHERE dogs.id = leaderboard_entries.dog_id
            AND dogs.owner_id = auth.uid()
        )
    );

-- ============================================
-- FUNCTIONS
-- ============================================

-- Function to auto-create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, email, name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'name', 'Dog Lover')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to auto-create user profile
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to update healthspan score when daily log changes
CREATE OR REPLACE FUNCTION update_healthspan_on_log()
RETURNS TRIGGER AS $$
DECLARE
    v_dog_id UUID;
    v_new_score DECIMAL(5,2);
BEGIN
    v_dog_id := COALESCE(NEW.dog_id, OLD.dog_id);
    
    -- Calculate new score based on recent logs (last 7 days)
    WITH recent_logs AS (
        SELECT 
            AVG((energy_level + appetite + sleep_quality + exercise_level + nutrition_quality + water_intake) / 6.0) as avg_score
        FROM daily_logs
        WHERE dog_id = v_dog_id
        AND date >= CURRENT_DATE - INTERVAL '7 days'
    )
    SELECT 
        COALESCE(
            (SELECT 70 + (avg_score * 3) FROM recent_logs WHERE avg_score IS NOT NULL),
            85.00
        ) INTO v_new_score;
    
    -- Update or insert healthspan stats
    INSERT INTO healthspan_stats (dog_id, current_score, last_activity_date, calculated_at)
    VALUES (v_dog_id, v_new_score, CURRENT_DATE, NOW())
    ON CONFLICT (dog_id) DO UPDATE SET
        current_score = v_new_score,
        last_activity_date = CURRENT_DATE,
        calculated_at = NOW();
    
    -- Update leaderboard
    INSERT INTO leaderboard_entries (dog_id, breed, total_points, current_score)
    SELECT d.id, d.breed, hs.total_points, hs.current_score
    FROM dogs d
    JOIN healthspan_stats hs ON d.id = hs.dog_id
    WHERE d.id = v_dog_id
    ON CONFLICT (dog_id) DO UPDATE SET
        total_points = EXCLUDED.total_points,
        current_score = EXCLUDED.current_score,
        updated_at = NOW();
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger for daily log changes
DROP TRIGGER IF EXISTS on_daily_log_change ON daily_logs;
CREATE TRIGGER on_daily_log_change
    AFTER INSERT OR UPDATE ON daily_logs
    FOR EACH ROW EXECUTE FUNCTION update_healthspan_on_log();

-- ============================================
-- REALTIME SUBSCRIPTIONS
-- ============================================
ALTER PUBLICATION supabase_realtime ADD TABLE dogs;
ALTER PUBLICATION supabase_realtime ADD TABLE daily_logs;
ALTER PUBLICATION supabase_realtime ADD TABLE healthspan_stats;

-- ============================================
-- SEED DATA (Optional - for testing)
-- ============================================
-- Uncomment to add sample breeds
/*
INSERT INTO breeds (name, api_id, category, avg_weight_lbs, avg_lifespan_years) VALUES
    ('Golden Retriever', '121', 'Sporting', 70, 11),
    ('Labrador Retriever', '123', 'Sporting', 70, 12),
    ('German Shepherd', '115', 'Herding', 75, 11),
    ('French Bulldog', '107', 'Non-Sporting', 28, 11),
    ('Bulldog', '104', 'Non-Sporting', 50, 9),
    ('Poodle', '118', 'Non-Sporting', 45, 13),
    ('Beagle', '102', 'Hound', 25, 13),
    ('Rottweiler', '120', 'Working', 100, 9),
    ('German Shorthaired Pointer', '116', 'Sporting', 60, 12),
    ('Dachshund', '106', 'Hound', 20, 14);
*/
