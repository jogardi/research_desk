
/**
 * Get the text of an excerpt
 * @param {Array} excerpt - the excerpt [start, end]
 * @param {Array} chunks - the array of chunks
 * @returns {String} - the text of the excerpt
 */
export function getExcerptText(excerpt, chunks) {
    const sentences = chunks.slice(excerpt[0], excerpt[1] + 1) // get the sentences in the excerpt - copy of each chunk in the excerpt range
    return sentences.map(s => s.text).join('');
    // for (let i = 0; i < sentences.length; i++) {
    //     sentences[i].text = sentences[i].text.replace(/(\r\n|\n|\r)/gm, ''); // remove newlines
    // }
    // join sentences with ' ':
        // return  sentences.map(s => s.text).join(' ');
}

/**
 * Get the text of a document
 * @param {Object} doc - the document
 * @returns {String} - the text of the document
 */
export function getDocText(doc) {
    let text = '';
    doc.excerpts.forEach(excerpt => {
        text += getExcerptText(excerpt, doc.chunks) + '\n\n';
    });

    return text;
}

/**
 * Get the text of a list of documents
 * @param {Array} docs - the list of documents
 * @returns {String} - the text of the documents
 */
export function getDocumentsText(docs) {
    let text = '';
    docs.forEach(doc => {
        doc.excerpts.forEach(excerpt => {
            text += getExcerptText(excerpt, doc.chunks) + '\n\n';
        });
    });
    return text;
}

/**
 * Restore the original chunks in an excerpt
 * @param {Array} excerpt - the excerpt [start, end, excerptData]
 * @param {Array} originalChunks - the original chunks
 * @param {Object} doc - the document
 */
export function restoreChunks(excerpt, originalChunks, doc) {
    for (let index = excerpt[0]; index <= excerpt[1]; index++) {
        const originalChunk = originalChunks.find(chunk => chunk.id == doc.chunks[index].id);
        doc.chunks[index] = { ... originalChunk }
    }
    excerpt[2].text = getExcerptText(excerpt, doc.chunks);
}

/**
 * calculate the score of an excerpt as the average score of the chunks in the excerpt
 * @param {Object} doc - the document
 * @param {Array} excerpt - the excerpt
 * @returns {Number} - the score of the excerpt
 * */
export function _calcExcerptScore(doc, excerpt) {
    let scoreTotal = 0;
    let score2Count = 0;
    for (let i = excerpt[0]; i <= excerpt[1]; i++) {
        if (doc.chunks[i].score != 2) {
            scoreTotal += doc.chunks[i].score;
        }
        else {
            score2Count++;
        }
    }

    const score = scoreTotal / (excerpt[1] - excerpt[0] + 1 - score2Count); // average score of the chunks in the excerpt
    return score;
}

/**
 *  Move an excerpt from a source document to a destination document
 * @param {Array} srcExcerpt - the excerpt to be moved [start, end]
 * @param {Object} srcDoc - the source document
 * @param {Array} destDocs - the destination documents
 * @returns {Object} - the destination document
 */
export function moveExcerpt(srcExcerpt, srcDoc, destDocs, checked = false) {
// find the document in destDocs
let destDoc = destDocs.find(doc => doc.documentID === srcDoc.documentID);

// if doc is not in destDocs, add new document to destDocs
if (!destDoc) {
    destDoc = {
        documentID: srcDoc.documentID,
        documentCategory: srcDoc.documentCategory,
        documentName: srcDoc.documentName,
        docType: srcDoc.docType,
        checked: false,
        chunks: [],
        excerpts: null
    };
    destDocs.push(destDoc);
}

let srcSentences = null; // the sentences in the source excerpt
if (checked) {
    srcSentences =  srcDoc.chunks.slice(srcExcerpt[0], srcExcerpt[1] + 1); // copy the sentences in the excerpt
}
else {
    // remove the chunks with index range srcExcerpt[0] to srcExcerpt[1]
    srcSentences =  srcDoc.chunks.splice(srcExcerpt[0], srcExcerpt[1] - srcExcerpt[0] + 1);
}

// insert each sentence in the source excerpt into the destination document chunks array in id order
for (let index = 0; index < srcSentences.length; index++) {
    const srcSentence = srcSentences[index]; // current sentence from source excerpt

    // find the insertion point for the source sentence in the context document chunks array 
    // and insert it if not already present
    let inserted = false;
    for (let i = 0; i < destDoc.chunks.length; i++) {
        if (destDoc.chunks[i].id === srcSentence.id) { // if sentence already in context, do not overwrite it
            inserted = true;  // indicate that the sentence was inserted
            break;
        } 
        else if (srcSentence.id < destDoc.chunks[i].id) { // if found insertion point
            destDoc.chunks.splice(i, 0, { ...srcSentence }); // insert at the current position
            inserted = true; // indicate that the sentence was inserted
            break;
        }
    }

    // if sentence was not inserted (it is the last sentence or it is a new doc with empty chunks array)
    if (!inserted) { 
        destDoc.chunks.push({ ...srcSentence }); // Append at the end if not inserted earlier
    }

}

// reconstruct the excerpts array in the context document
_reconstructExcerpts(destDoc);

// reconstruct the excerpts array in source document
if (!checked && srcDoc.chunks.length > 0) {
    _reconstructExcerpts(srcDoc);
}

return destDoc;
}

/**
 * Remove an excerpt from a document
 * @param {Array} excerpt - the excerpt to be removed [start, end]
 * @param {Object} doc - the document
 */
export function removeExcerpt(excerpt, doc) {
    // remove the chunks referenced by the excerpt from the doc.chunks
    doc.chunks.splice(excerpt[0], excerpt[1] - excerpt[0] + 1);
    // reconstruct the doc.excerpts (effectively removing the excerpt from the document) 
    if (doc.chunks.length > 0) {
        _reconstructExcerpts(doc);
    }
}

/**
 * Remove checked excerpts 
 * @param {Array} docs - the list of documents
 * @returns {Set} - the set of document IDs to be removed
 */
export function removeCheckedExcerpts(docs) {
    const docRemoveSet = new Set(); 
    const chunkRemoveSet = new Set();

    // Collect document IDs that need to be removed
    docs.forEach(doc => {
        doc.excerpts.forEach(excerpt => {
            if (excerpt[2].checked) {
                // Collect chunk IDs that need to be removed
                for (let i = excerpt[0]; i <= excerpt[1]; i++) {
                    chunkRemoveSet.add(doc.chunks[i].id); 
                }
            }
        });

        if (chunkRemoveSet.size > 0) { // if there are chunks to be removed
            // Remove chunks from the document
            doc.chunks = doc.chunks.filter(chunk => !chunkRemoveSet.has(chunk.id));
            chunkRemoveSet.clear();
            if (doc.chunks.length > 0) {  // if there are chunks left, reconstruct the excerpts
                _reconstructExcerpts(doc);
                doc.title = null; // update the title
            }
            else { // no chunks left, mark for removal
                docRemoveSet.add(doc.documentID);
            }
        }
    });

    // return the set of document IDs to be removed
    return docRemoveSet;  
}

export function moveCheckedExcerpts(srcDocs, destDocs) {
    const destDocsToBeReTitledSet = new Set();
    srcDocs.forEach(doc => {
      doc.excerpts.forEach(excerpt => {
        if (excerpt[2].checked) {
          const destDoc = moveExcerpt(excerpt, doc, destDocs, true); // move excerpt to context
          destDocsToBeReTitledSet.add(destDoc.documentID);
          destDoc.title = null // update the title of the destination doc
        }
      });
    });

    // update the titles of the source docs
    srcDocs.forEach(doc => {
      if (destDocsToBeReTitledSet.has(doc.documentID)) {
        doc.title = null; // update the title
      }
    });

    // removeCheckedItems();
}

function _createExcerpt(doc, firstIndex, lastIndex) {
    const excerpt = [firstIndex, lastIndex];

    // find the a chunk with the excerptData and save it into the new first chunk
    let excerptData = null; // the excerptData to be added to the excerpt
    // for (let index = excerpt[0] + 1; index <= excerpt[1]; index++) {
    for (let index = excerpt[0]; index <= excerpt[1]; index++) {
        const chunk = doc.chunks[index];
        if (chunk.excerptData) { 
            if (excerptData) { // if excerptData already found
                excerptData.stickyNote += '\n' + chunk.excerptData.stickyNote; // combine sticky notes
            }
            else {
                excerptData = { ...chunk.excerptData }; // save the excerptData into the first chunk
            }
            delete chunk.excerptData; // remove the excerptData from the chunk
        };
    }

    // if no previous excerptData found, create it and save it into the first chunk
    if (!excerptData) {
        excerptData = { 
            status: 'O', checked: false, edited: false, documentID: doc.documentID, stickyNote: '', 
            text: getExcerptText(excerpt, doc.chunks), score: _calcExcerptScore(doc, excerpt)
        };
    }  
    // doc.chunks[0].excerptData = excerptData; // save the excerptData into the first chunk
    doc.chunks[excerpt[0]].excerptData = excerptData; // save the excerptData into the first chunk
    // add the excerptData to the excerpt
    excerpt[2] = excerptData;

    return excerpt;
}
    
// Generate a list of excerpts from a list of chunks
function _reconstructExcerpts(doc) {
    const excerpts = [];
    let excerptStartIdx = 0;
    for (let i = 1; i < doc.chunks.length; i++) {
        if (doc.chunks[i].id - doc.chunks[i - 1].id === 1) { // if consecutive sentence IDs
            continue; // skip consecutive
        }
        const excerpt = _createExcerpt(doc, excerptStartIdx, i - 1);
        excerpts.push(excerpt); // add the excerpt
        excerptStartIdx = i; // start a new excerpt
    }
    const excerpt = _createExcerpt(doc, excerptStartIdx, doc.chunks.length - 1);
    excerpts.push(excerpt); // add the last excerpt
    doc.excerpts = excerpts;
}
