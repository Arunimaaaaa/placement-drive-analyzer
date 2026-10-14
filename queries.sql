-- Placement Drive Analyzer: analysis queries on placements.db
-- Each query has a numbered header comment; run_queries.py runs them all.

-- Q1. What is actually in a "placement" group? Count of announcements by type
SELECT type, COUNT(*) AS posts,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM announcements WHERE type != 'duplicate'), 1) AS pct
FROM announcements
WHERE type != 'duplicate'
GROUP BY type
ORDER BY posts DESC;

-- Q2. Highest-paying opportunities (by top of the CTC range)
SELECT company, type, ctc_lpa_min, ctc_lpa_max, fixed_ctc_lpa, bond_years
FROM announcements
WHERE type IN ('job', 'internship_ppo') AND ctc_lpa_max IS NOT NULL
ORDER BY ctc_lpa_max DESC
LIMIT 10;

-- Q3. Direct job vs internship + PPO: how many, typical pay, how often pay is disclosed
SELECT type,
       COUNT(*) AS drives,
       SUM(CASE WHEN ctc_lpa_max IS NOT NULL THEN 1 ELSE 0 END) AS ctc_disclosed,
       ROUND(AVG(ctc_lpa_max), 2) AS avg_ctc_max,
       ROUND(AVG(stipend_per_month)) AS avg_stipend
FROM announcements
WHERE type IN ('job', 'internship_ppo', 'internship')
GROUP BY type;

-- Q4. Bonds: which drives have one, and how does pay compare?
SELECT CASE
         WHEN bond_years > 0 THEN 'Bond'
         WHEN bond_years = 0 THEN 'No bond (stated)'
         ELSE 'Not mentioned'
       END AS bond_status,
       COUNT(*) AS drives,
       ROUND(AVG(ctc_lpa_max), 2) AS avg_ctc_max,
       GROUP_CONCAT(company, ', ') AS companies
FROM announcements
WHERE type IN ('job', 'internship_ppo')
GROUP BY bond_status;

-- Q5. Headline CTC vs guaranteed fixed pay (where the message splits them)
SELECT company, ctc_lpa_max AS headline_ctc, fixed_ctc_lpa AS fixed_ctc,
       ROUND(ctc_lpa_max - fixed_ctc_lpa, 2) AS variable_part,
       ROUND(100.0 * fixed_ctc_lpa / ctc_lpa_max) AS pct_fixed
FROM announcements
WHERE fixed_ctc_lpa IS NOT NULL AND fixed_ctc_lpa < ctc_lpa_max;

-- Q6. When do opportunities arrive? Drives per month
SELECT strftime('%Y-%m', date) AS month, COUNT(*) AS drives
FROM announcements
WHERE type IN ('job', 'internship_ppo', 'internship')
GROUP BY month
ORDER BY month;

-- Q7. Follow-up load per drive (JOIN): how many group posts each hiring company generated
SELECT a.company, a.type, a.ctc_lpa_max, c.total_posts,
       CAST(julianday(c.last_post) - julianday(c.first_post) AS INTEGER) AS days_active
FROM announcements a
JOIN companies c ON a.company = c.company
WHERE a.type IN ('job', 'internship_ppo', 'internship')
ORDER BY c.total_posts DESC
LIMIT 10;

-- Q8. Internship + PPO: stipend during internship vs CTC after conversion
SELECT company, stipend_per_month, ctc_lpa_max,
       ROUND(stipend_per_month * 12 / 100000.0, 2) AS stipend_as_lpa
FROM announcements
WHERE type = 'internship_ppo' AND stipend_per_month IS NOT NULL AND ctc_lpa_max IS NOT NULL
ORDER BY ctc_lpa_max DESC;
