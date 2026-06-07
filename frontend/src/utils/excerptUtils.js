/**
 * Generate a 4-character hash for an excerpt based on document ID and chunk IDs
 * This should match the Python implementation in the backend
 */
export async function generateExcerptHash(documentId, chunkIds) {
  // Sort chunk IDs for consistency
  const sortedChunkIds = [...chunkIds].sort((a, b) => a - b);
  const hashInput = `${documentId}:${sortedChunkIds.join(',')}`;
  
  // Create SHA-256 hash
  const encoder = new TextEncoder();
  const data = encoder.encode(hashInput);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  
  // Convert to hex string and take first 4 characters
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  
  return hashHex.substring(0, 4);
} 