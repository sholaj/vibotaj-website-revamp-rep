-- PRD-005: Supabase Storage Buckets + RLS
-- Creates 3 private storage buckets for document management
-- and RLS policies for organization-level access control.

-- ============================================================
-- 1. Create storage buckets (private — access via signed URLs)
-- ============================================================

INSERT INTO storage.buckets (id, name, public, file_size_limit)
VALUES
  ('documents', 'documents', false, 52428800),       -- 50 MB
  ('audit-packs', 'audit-packs', false, 52428800),   -- 50 MB
  ('exports', 'exports', false, 52428800)             -- 50 MB
ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- 2. RLS policies for storage.objects
-- ============================================================
-- Path convention: {bucket}/{org_id}/{document_id}/{filename}
-- The first folder in the path = organization ID.
-- RLS reads app.current_org_id (set by RLSContextMiddleware).

-- Upload: authenticated users can upload to their org's folder
CREATE POLICY "org_upload" ON storage.objects FOR INSERT
  TO authenticated
  WITH CHECK (
    bucket_id IN ('documents', 'audit-packs', 'exports')
    AND (storage.foldername(name))[1] = current_setting('app.current_org_id', true)
  );

-- Read: authenticated users can read their org's files
CREATE POLICY "org_read" ON storage.objects FOR SELECT
  TO authenticated
  USING (
    bucket_id IN ('documents', 'audit-packs', 'exports')
    AND (
      (storage.foldername(name))[1] = current_setting('app.current_org_id', true)
      OR current_setting('app.is_system_admin', true)::boolean = true
    )
  );

-- Update: authenticated users can update their org's files (e.g., rename)
CREATE POLICY "org_update" ON storage.objects FOR UPDATE
  TO authenticated
  USING (
    bucket_id IN ('documents', 'audit-packs', 'exports')
    AND (storage.foldername(name))[1] = current_setting('app.current_org_id', true)
  );

-- Delete: only system admins can delete files
CREATE POLICY "admin_delete" ON storage.objects FOR DELETE
  TO authenticated
  USING (
    bucket_id IN ('documents', 'audit-packs', 'exports')
    AND current_setting('app.is_system_admin', true)::boolean = true
  );
