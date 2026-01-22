-- DIRECT SQL CLEANUP FOR DUPLICATE TWGs
-- Run this in PostgreSQL to clean up duplicates

-- Step 1: First, let's see what we have
SELECT pillar, name, id, COUNT(*) OVER (PARTITION BY pillar) as duplicate_count
FROM twgs
ORDER BY pillar, id;

-- Step 2: Delete all related data for test/debug TWGs first
-- This uses CASCADE behavior
BEGIN;

-- Delete test TWG data
DELETE FROM action_items WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG'));
DELETE FROM documents WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG'));
DELETE FROM projects WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG'));
DELETE FROM meetings WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG'));

-- Now delete the test TWGs themselves
DELETE FROM twgs WHERE name IN ('Test TWG', 'Debug TWG');

COMMIT;

-- Step 3: For Energy Infrastructure duplicates, keep the first one and reassign everything else
BEGIN;

-- Get the ID of the FIRST energy TWG (the one to keep)
WITH first_energy AS (
    SELECT id FROM twgs 
    WHERE pillar = 'TWGPillar.energy_infrastructure'
    ORDER BY id
    LIMIT 1
),
duplicate_energy AS (
    SELECT id FROM twgs 
    WHERE pillar = 'TWGPillar.energy_infrastructure'
    AND id NOT IN (SELECT id FROM first_energy)
)
-- Reassign all related records to the first energy TWG
UPDATE action_items SET twg_id = (SELECT id FROM first_energy) 
WHERE twg_id IN (SELECT id FROM duplicate_energy);

UPDATE documents SET twg_id = (SELECT id FROM first_energy) 
WHERE twg_id IN (SELECT id FROM duplicate_energy);

UPDATE projects SET twg_id = (SELECT id FROM first_energy) 
WHERE twg_id IN (SELECT id FROM duplicate_energy);

UPDATE meetings SET twg_id = (SELECT id FROM first_energy) 
WHERE twg_id IN (SELECT id FROM duplicate_energy);

-- Now delete the duplicate energy TWGs
DELETE FROM twgs 
WHERE pillar = 'TWGPillar.energy_infrastructure'
AND id NOT IN (SELECT id FROM first_energy);

COMMIT;

-- Step 4: Verify cleanup
SELECT pillar, name, id 
FROM twgs
ORDER BY pillar;
