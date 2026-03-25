import { serve } from "std/http/server"
import { createClient } from '@supabase/supabase-js'

// Constants
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

// Initialize clients
const supabaseUrl = Deno.env.get('SUPABASE_URL')!
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

const supabase = createClient(supabaseUrl, supabaseServiceKey)

// Text extraction functions
async function extractTextFromPDF(arrayBuffer: ArrayBuffer): Promise<string> {
  const { default: pdfParse } = await import('npm:pdf-parse');
  const data = await pdfParse(new Uint8Array(arrayBuffer));
  return data.text;
}

async function extractTextFromDOCX(arrayBuffer: ArrayBuffer): Promise<string> {
  const { default: mammoth } = await import('npm:mammoth');
  const result = await mammoth.extractRawText({ arrayBuffer });
  return result.value;
}

async function extractTextFromFile(file: File): Promise<string> {
  const arrayBuffer = await file.arrayBuffer();
  
  if (file.size > MAX_FILE_SIZE) {
    throw new Error(`File size exceeds limit of ${MAX_FILE_SIZE} bytes`);
  }

  const fileType = file.type.toLowerCase();
  switch (fileType) {
    case 'application/pdf':
      return await extractTextFromPDF(arrayBuffer);
    case 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
      return await extractTextFromDOCX(arrayBuffer);
    case 'text/plain':
    case 'application/rtf':
      return await file.text();
    default:
      throw new Error(`Unsupported file type: ${fileType}`);
  }
}

/**
 * Main Edge Function handler
 */
serve(async (req) => {
  const requestStartTime = Date.now()
  console.log(`[EXTRACT TEXT] 🚀 Text extraction request received: ${req.method} ${req.url}`)
  
  // Handle CORS preflight request
  if (req.method === 'OPTIONS') {
    console.log(`[EXTRACT TEXT] Handling CORS preflight request`)
    return new Response('ok', {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
        'Access-Control-Max-Age': '86400',
      }
    })
  }

  try {
    // Parse request body
    console.log(`[EXTRACT TEXT] Parsing request body...`)
    const { documentId, userId, filePath } = await req.json()
    
    if (!documentId || !userId || !filePath) {
      console.error(`[EXTRACT TEXT] ❌ Missing required fields:`, { documentId, userId, filePath })
      return new Response(
        JSON.stringify({ error: 'Missing required fields: documentId, userId, filePath' }),
        { 
          status: 400, 
          headers: { 
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          } 
        }
      )
    }

    console.log(`[EXTRACT TEXT] Processing document ${documentId} for user ${userId}`)

    // Get document details
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('*')
      .eq('id', documentId)
      .eq('user_id', userId)
      .single()

    if (docError || !document) {
      console.error(`[EXTRACT TEXT] Document fetch failed:`, docError?.message)
      return new Response(
        JSON.stringify({ error: 'Document not found or access denied' }),
        { 
          status: 404, 
          headers: { 
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          } 
        }
      )
    }

    console.log(`[EXTRACT TEXT] Document found: "${document.title}" (${document.file_type})`)

    // Download file from storage
    console.log(`[EXTRACT TEXT] Downloading file from storage: ${filePath}`)
    const { data: fileData, error: downloadError } = await supabase.storage
      .from('documents')
      .download(filePath)

    if (downloadError) {
      console.error(`[EXTRACT TEXT] File download failed:`, downloadError.message)
      return new Response(
        JSON.stringify({ error: `File download failed: ${downloadError.message}` }),
        { 
          status: 500, 
          headers: { 
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          } 
        }
      )
    }

    // Extract text from file
    console.log(`[EXTRACT TEXT] Extracting text from file...`)
    const extractedText = await extractTextFromFile(fileData)

    if (!extractedText || extractedText.trim().length === 0) {
      console.warn(`[EXTRACT TEXT] No text content extracted from file`)
      return new Response(
        JSON.stringify({ error: 'No text content could be extracted from the file' }),
        { 
          status: 400, 
          headers: { 
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          } 
        }
      )
    }

    console.log(`[EXTRACT TEXT] Extracted ${extractedText.length} characters of text`)

    // Update document with extracted text
    console.log(`[EXTRACT TEXT] Updating document with extracted text...`)
    const { error: updateError } = await supabase
      .from('documents')
      .update({
        content: extractedText,
        status: 'completed',
        updated_at: new Date().toISOString()
      })
      .eq('id', documentId)

    if (updateError) {
      console.error(`[EXTRACT TEXT] Document update failed:`, updateError.message)
      return new Response(
        JSON.stringify({ error: `Document update failed: ${updateError.message}` }),
        { 
          status: 500, 
          headers: { 
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          } 
        }
      )
    }

    const requestEndTime = Date.now()
    const totalRequestTime = requestEndTime - requestStartTime
    
    console.log(`[EXTRACT TEXT] ✅ Text extraction completed successfully in ${totalRequestTime}ms`)
    console.log(`[EXTRACT TEXT] 📊 Summary:`, {
      documentId,
      userId,
      totalTime: `${totalRequestTime}ms`,
      textLength: extractedText.length,
      fileType: document.file_type
    })

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Text extraction completed successfully',
        textLength: extractedText.length,
        documentId
      }),
      { 
        status: 200,
        headers: { 
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      }
    )

  } catch (error) {
    const requestEndTime = Date.now()
    const totalRequestTime = requestEndTime - requestStartTime
    
    console.error(`[EXTRACT TEXT] ❌ Text extraction failed after ${totalRequestTime}ms:`, error)
    return new Response(
      JSON.stringify({ 
        success: false,
        message: 'Text extraction failed',
        error: error.message 
      }),
      { 
        status: 500,
        headers: { 
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      }
    )
  }
})
