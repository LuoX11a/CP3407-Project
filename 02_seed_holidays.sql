-- ============================================================
-- ParkGuideSG - Singapore Public Holidays Seed Data
-- 2026 dates (update yearly from mom.gov.sg)
-- ============================================================

INSERT INTO public_holidays (date, name) VALUES
    ('2026-01-01', 'New Year''s Day'),
    ('2026-02-17', 'Chinese New Year'),
    ('2026-02-18', 'Chinese New Year Holiday'),
    ('2026-03-21', 'Hari Raya Puasa'),
    ('2026-04-03', 'Good Friday'),
    ('2026-05-01', 'Labour Day'),
    ('2026-05-20', 'Vesak Day'),
    ('2026-05-28', 'Hari Raya Haji'),
    ('2026-08-09', 'National Day'),
    ('2026-10-18', 'Deepavali'),
    ('2026-12-25', 'Christmas Day')
ON CONFLICT (date) DO NOTHING;
