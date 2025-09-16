-- Migration: 00005_storage_bucket_setup.sql
-- Description: Create storage buckets and policies for document management

-- Create the documents bucket
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'documents',
  'documents',
  false,  -- private bucket
  10485760, -- 10MB file size limit
  ARRAY[
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'application/rtf'
  ]
) ON CONFLICT (id) DO NOTHING;

-- Create archives bucket for thread archives
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'archives',
  'archives',
  false,
  10485760, -- 10MB limit
  ARRAY['text/plain', 'application/json']
) ON CONFLICT (id) DO NOTHING;

-- Create temp bucket for temporary processing files
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'temp',
  'temp',
  false,
  52428800, -- 50MB limit for temp files
  ARRAY['text/plain', 'application/json', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
) ON CONFLICT (id) DO NOTHING;

-- Create simplified policies for documents bucket
-- Policy 1: Allow authenticated users to upload to documents bucket
CREATE POLICY "Allow authenticated uploads to documents" ON storage.objects
  FOR INSERT TO authenticated
  WITH CHECK (bucket_id = 'documents');

-- Policy 2: Allow authenticated users to view documents
CREATE POLICY "Allow authenticated view documents" ON storage.objects
  FOR SELECT TO authenticated
  USING (bucket_id = 'documents');

-- Policy 3: Allow authenticated users to update documents
CREATE POLICY "Allow authenticated update documents" ON storage.objects
  FOR UPDATE TO authenticated
  USING (bucket_id = 'documents');

-- Policy 4: Allow authenticated users to delete documents
CREATE POLICY "Allow authenticated delete documents" ON storage.objects
  FOR DELETE TO authenticated
  USING (bucket_id = 'documents');

-- Create policies for archives bucket
CREATE POLICY "Allow authenticated access archives" ON storage.objects
  FOR ALL TO authenticated
  USING (bucket_id = 'archives');

-- Create policies for temp bucket
CREATE POLICY "Allow authenticated access temp" ON storage.objects
  FOR ALL TO authenticated
  USING (bucket_id = 'temp');
