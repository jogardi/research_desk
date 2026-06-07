// src/utils/api.js
// TODO split api.js by feature
import { Notify } from 'quasar'
import router from 'src/router';
import { Config } from 'src/config.js';
// import * as io from 'https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.5/socket.io.js'
import { io } from 'socket.io-client';

export function notify(options, closeBtn = true) {
  const notifyConfig = {
    message: options.title,
    caption: options.message,
    position: options.position || 'top-right',
    timeout: options.duration,
    icon: options.icon, 
    color: 'grey-10',
    iconColor: options.color, 
    textColor: options.color,
    closeBtn: closeBtn,
  };

  // Only include html property if it's defined
  if (options.html !== undefined) {
    notifyConfig.html = options.html;
  }

  Notify.create(notifyConfig);
}  

function _notifyException(error)  {
  console.log('*** +++ Error:', error);
  notify({
    title: 'Unexpected Server Error',
    message: 'An error occurred while processing your request. <br />Our team has been notified. Please try again later.',
    color: 'negative',
    icon: 'error',
    duration:  5000,
    html: true
  })
}

function _rateLimitExceededNotification(url) {

  let title = 'Rate Limit Exceeded';
  let message = 'Oops! Too many requests. Please wait an hour and try again';

  if (url.endsWith('api/llm/answer')) {
    title = 'AI/LLM submission Rate Limit Exceeded';
    message = 'Oops! Too many requests. Please wait an hour and try again';
  }

  notify({
    title: title,
    message: message,
    color: 'warning',
    icon: 'warning',
    duration:  5000
  })
}

async function fetchAuth(url, options = {}, url_params = {}) {  
  const finalUrl = Object.keys(url_params).length > 0
    ? `${url}${url.includes('?') ? '&' : '?'}${new URLSearchParams(url_params)}`
    : url;
    
  // Get token from local storage
  const token = localStorage.getItem('_id_'); 

  if (!token) {
    // Navigate to the login page
    router.replace('/login');
    return { ok: false }; // return fake response object to indicate non-200 status
  }
  
  // add additianl headers to options.headers
  options.headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`
  };
  
  
  const response = await fetch(finalUrl, options);

  if (response.status === 401) {
    // notify({
    //   title: 'Session Expired!',
    //   message: 'Please login to continue.',
    //   color: 'info',
    //   icon: 'info',
    //   duration:  5000
    // })
    
    // Navigate to the login page
    router.replace('/login');

    return response;
  }

  else if (response.status === 404) {
    notify({
      title: 'Resource not fount - 404',
      message: `The requested resource was not found: <br />${url}`,
      color: 'warning',
      icon: 'warning',
      duration:  5000,
      html: true
    })
    return response;
  }

  else if (response.status === 429) {
    _rateLimitExceededNotification(url);
    return response;
  }

  else if (response.status === 422) {
    const responseBody = await response.json();
    debugger;
    if (responseBody.detail && responseBody.detail.includes('Maximum context window length exceeded')) {
      return response; // let caller handle the error
    }
  }


  // else if (response.status === 422) {
  //   notify({
  //     title: 'LLM Context Window Exceeded',
  //     message: `Too many tokens in the context or search results. <br />Please remove some excerptst or documents from the context or search results.`,
  //     color: 'info',
  //     icon: 'error',
  //     duration:  15000,
  //     html: true
  //   })
  //   return response;
  // }

  else if (!response.ok) {
    notify({
      title: `Unexpected Server Error: ${response.status}`,
      message: 'An error occurred while processing your request. Our team has been notified. Please try again later.',
      color: 'negative',
      icon: 'error',
      duration:  5000
    })
  }

  return response;
} 

/*
* Session API
*/
export async function loadSessionList() {
  let result = []; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/sessions/list`,
      {
        method: 'GET',
        // credentials: 'include'
      }
    );
    if (response.ok) {
      result= await response.json();
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

export async function loadSessionListForKbName(kb_name) {
  let result = []; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/user/session-list/${kb_name}`,
      {
        method: 'GET',
        // credentials: 'include'
      }
    );
    if (response.ok) {
      result= await response.json();
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

export async function loadSession (sessionId) {
  let result = { data: null, isError: true } ; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/sessions/detail/${sessionId}`, {
      method: 'GET',
      // credentials: 'include'
      });

      if (response.ok) {
        const payload = await response.json();
        result = { data: payload, isError: false };
      }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

export async function addSession(session) {
  let result = null; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/sessions`, {
      method: 'POST',
      // credentials: 'include',
      body: JSON.stringify(session),
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      result = await response.json();
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

export async function saveSession(sessionId, session) {
  let result = true; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/sessions/${sessionId}`, {
      method: 'PUT',
      // credentials: 'include',
      body: JSON.stringify(session),
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      result = false; // No error
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

export async function removeSession(sessionId) {
  let result = false; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/sessions/${sessionId}`, {
      method: 'DELETE',
      // credentials: 'include'
    });
    
    if (response.ok) {
      result = true;
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

export async function forkSession(sessionId, session) {
  let result = null; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/sessions/fork/${sessionId}`, {
      method: 'POST',
      // credentials: 'include',
      body: JSON.stringify(session),
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      result = await response.json();
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

/*
* LLM Roles API
*/
export async function loadLlmRoleList() {
  let result = []; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/llm-roles/list`,
      {
        method: 'GET',
        // credentials: 'include'
      }
    );
    if (response.ok) {
      result= await response.json();
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

export async function addLlmRole(llmRole) {
  let result = null; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/llm-roles`, {
      method: 'POST',
      // credentials: 'include',
      body: JSON.stringify(llmRole),
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      result = await response.json();
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

export async function saveLlmRole(llmRole) {
  let result = true; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/llm-roles`, {
      method: 'PUT',
      // credentials: 'include',
      body: JSON.stringify(llmRole),
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      result = false; // No error
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

export async function removeLlmRole(llmRoleId) {
  let result = false; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/llm-roles/${llmRoleId}`, {
      method: 'DELETE',
      // credentials: 'include'
    });
    
    if (response.ok) {
      result = true;
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

/*
* Category API
*/
export async function loadCategories(type) {
  let result = { categories: [], categoryIDs: [] }; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/categories/${type}`, {
      method: 'GET',
      // credentials: 'include'
    });
  
    if (response.ok) {
      result= await response.json();
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

// export async function getCategoryPaths(categoryIDs, type) {
//   try {
//     const response = await fetchAuth(`${Config.API_SERVER}/api/categories/paths?categoryIDs=${categoryIDs}&type=${type}`);
//     if (!response.ok) {
//       window.alert(`Error fetching categories. HTTP Status Code: ${response.status}`);
//       return [];
//     }
//     const payload = await response.json();
//     return payload.paths;
//   }
//   catch (error) {
//     window.alert("Error fetching categories:", error);
//     return [];
//   }
// }

/*
* Semantic Search API (by document)
*/
export async function semanticSearchByDoc(query, selectedCategoryPaths, topK) {
  let result = { data: [], isError: true }; // Default result in case of error
  // encode the query to be used in the URL
  // query = encodeURIComponent(query);
  const categories = selectedCategoryPaths.join(',');
  try {
    // const response = await fetchAuth(`${Config.API_SERVER}/api/search/semantic_by_doc?categories=${categories}&query=${query}&topK=${topK}`, {
    const response = await fetchAuth(`${Config.API_SERVER}/api/search/semantic_by_doc`, {
      method: 'GET',
      // credentials: 'include'
      }, {
        categories: categories,
        query: query,
        topK: topK
      });
    if (response.ok) {
      const docs = await response.json();
      result = { data: docs, isError: false };
    }
  }
  catch (error) {
    _notifyException(error);
  }

  return result;
}

/*
* Semantic Search API
*/
export async function semanticSearch(query, selectedCategoryPaths, topK) {
  let result = { data: [], isError: true }; // Default result in case of error
  const categories = selectedCategoryPaths.join(',');
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/search/semantic`, {
      method: 'GET',
      // credentials: 'include'
      }, {
        categories: categories,
        query: query,
        topK: topK
      });
    if (response.ok) {
      const chunks = await response.json();
      result = { data: chunks, isError: false };
    }
    
  }
  catch (error) {
    _notifyException(error);
  }

  return result;
}

/*
* Text Search API
*/
export async function textSearch(query, selectedCategoryPaths) {
  let result = { data: [], isError: true }; // Default result in case of error
  const categories = selectedCategoryPaths.join(',');
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/search/fts`, {
      method: 'GET',
      // credentials: 'include'
      }, {
        categories: categories,
        query: query
      });
    if (response.ok) {
      const payload = await response.json();
      result = { data: payload.chunks, isError: false };
    }
  }
  catch (error) {
    _notifyException(error);
  }

  return result;
}

/*
* Text Search API (by document)
*/
export async function textSearchByDoc(query, selectedCategoryPaths) {
  let result = { data: [], isError: true }; // Default result in case of error
  const categories = selectedCategoryPaths.join(',');
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/search/fts_by_doc`, {
      method: 'GET',
      // credentials: 'include'
      }, {
        categories: categories,
        query: query
      });
    if (response.ok) {
      const docs = await response.json();
      result = { data: docs, isError: false };
    }
  }
  catch (error) {
    _notifyException(error);
  }

  return result;
}

// export async function generateTitles(docTexts, docs) {
//   try {
//     for (let i=0; i < docs.length; i++) {
//       let response = await fetchAuth(`${Config.API_SERVER}/api/search/title`, {
//         method: 'POST',
//         // credentials: 'include',
//         headers: {
//           'Content-Type': 'application/json',
//         },
//         body: JSON.stringify({content: docTexts[i] })
//         });
      
//       if (response.ok) {
//         const payload = await response.json();
//         docs[i].title = payload.title;
//       }
//     }
//   } 
//   catch (error) {
//     _notifyException(error);
//   }
// }

export async function generateTitle(docText, userQuery) {
  let title = null;
  try {
    console.log("generateTitle", docText, userQuery)
      let response = await fetchAuth(`${Config.API_SERVER}/api/search/title`, {
        method: 'POST',
        // credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({content: docText, user_query: userQuery })
        });
      
      if (response.ok) {
        const payload = await response.json();
        // doc.title = payload.title;
        title =  payload.title;
      }
  } 
  catch (error) {
    _notifyException(error);
  }
  return title;
}

export async function getSuggestedCategories(query) {
  let result = null; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/search/category/for_query`, {
      method: 'GET',
      // credentials: 'include'
      }, {
        query: query
      });
    if (response.ok) {
      const payload = await response.json();
      result = payload.categories;
    }
  }
  catch (error) {
    _notifyException(error);
  }

  return result;
}

/*
* Chat API
*/
export async function chat(chat_request, systemMessage) {
  let result = { data: null, isError: true }; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/llm/chat`, {
      method: 'POST',
      // credentials: 'include',
      body: JSON.stringify({ chat_request: chat_request, system_message: systemMessage }),
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const assistant_message = await response.json();
      result = { data: assistant_message, isError: false };
    }
  }
  catch (error) {
    _notifyException(error);
  }

  return result;
}

let socket = null;

export async function* streamChat(chat_request, systemMessage, useTools, citationMetadata = {}) {
  console.log("streamChat", chat_request, systemMessage);
  const token = localStorage.getItem('_id_');
  if (!token) {
    console.log("*** No token found, redirecting to login");
    router.replace('/login');
    return;
  }
  // Create WebSocket connection (using FastAPI WebSocket endpoint)
  const wsUrl = `${Config.API_SERVER.replace('http', 'ws')}/ws?token=${token}`;
  try {
    socket = new WebSocket(wsUrl);
  } 
  catch (error) {
    console.log("*** Error creating WebSocket connection");
    notify({
      title: 'Error creating chat connection',
      message: JSON.stringify(error),
      color: 'warning',
      icon: 'warning',
      duration:  5000
    })
    return;
  }

  // A queue to store incoming chunks
  const queue = [];

  // Flag to signal the stream is done
  let done = false;

  // A helper promise and its resolver to wait for new entries in the queue.
  let resolveQueue;
  let queuePromise = new Promise((resolve) => {
    resolveQueue = resolve;
  });

  // Handle incoming messages
  socket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    switch (message.type) {
      case 'stream_chat_response':
        queue.push({ type: "chunk", data: message.data });
        resolveQueue();
        break;
      case 'error':
        queue.push({ type: "error", data: message.data });
        console.log("*** received error 111", message.data);
        // _notifyException(new Error(message.data));
        notify({
          title: 'AI Model Error',
          message: message.data,
          color: 'negative',
          icon: 'error',
          duration:  10000
        })
        resolveQueue();
        break;
      case 'auth_error':
        queue.push({ type: "auth_error", data: message.data });
        console.log("*** received auth_error", message.data);
        localStorage.removeItem('_id_');
        notify({
          title: 'Authentication error',
          message: 'Please login to continue',
          color: 'info',
          icon: 'warning',
          duration:  5000
        })
        setTimeout(() => {
          router.replace('/login');
        }, 5000);
        resolveQueue();
        break;
      case 'done':
        console.log(`Stream ended: ${message.data}`);
        done = true;
        resolveQueue();
        break;
      case 'query':
        console.log("received query", message.data);
        queue.push({ type: "query", data: message.data });
        resolveQueue();
        break;
      case 'read_page':
        console.log("received read_page", message.data);
        queue.push({ type: "read_page", data: JSON.parse(message.data) });
        resolveQueue();
        break;
        case 'load_pdf':
        console.log("received load_pdf", message.data);
        queue.push({ type: "load_pdf", data: JSON.parse(message.data) });
        resolveQueue();
        break;
    }
  };

  // Handle connection errors
  socket.onerror = (error) => {
    console.log('*** WebSocket error 222:', error);
    queue.push({ type: "error", data: error });
    _notifyException(error);
    resolveQueue();
  };

  // Handle connection close
  socket.onclose = (event) => {
    console.log('WebSocket connection closed');
    // console.log("*** event", event);
    done = true;
    resolveQueue();
  };

  // Wait for connection to open, then send the initial chat request
  socket.onopen = () => {
    console.log('Connected to WebSocket server');
    const toolsPresent = useTools.searchSemanticByDoc || useTools.readPage || useTools.loadPdf;

    socket.send(JSON.stringify({
      type: 'stream_chat',
      data: { 
        chat_request, 
        system_message: systemMessage,
        use_tools: toolsPresent? useTools : null,
        citation_metadata: citationMetadata 
      }
    }));
  };

  // Continuously yield items as they arrive.
  while (!done || queue.length > 0) {
    // If the queue is empty, wait until new data arrives.
    if (queue.length === 0) {
      await queuePromise;
      // Reset the promise for the next iteration.
      queuePromise = new Promise((resolve) => {
        resolveQueue = resolve;
      });
    }
  
    // Yield all chunks in the queue.
    while (queue.length > 0) {
      yield queue.shift();
    }
  }
  
  // Clean up the WebSocket connection once done.
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.close();
  }
}

export async function stopStream() {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({
      type: 'stop_stream',
      data: {}
    }));
  }
}

export async function* httpStreamChat(chat_request, systemMessage) {
  console.log("passing sytem message ", systemMessage);
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/llm/stream_chat`, {
      method: 'POST',
      // credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ chat_request: chat_request, system_message: systemMessage })
    });

    if (!response.ok) {
      console.log("Error:", response.status);
      return; // Optionally yield an error message or terminate.
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      // Decode the chunk with streaming support.
      const chunk = decoder.decode(value, { stream: true });
      yield chunk;
    }
    
    // Flush any remaining characters
    const remainingChunk = decoder.decode();
    if (remainingChunk) {
      yield remainingChunk;
    }
    
  } catch (error) {
    _notifyException(error);
    // Optionally: yield an error or simply exit
  }
}

export async function loadModels() {
  let result = { data: [], isError: true }; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/llm/models`, {
      method: 'GET',
      // credentials: 'include'
    });

    if (response.ok) {
      const models = await response.json();
      result = { data: models, isError: false };
    }
  }
  catch (error) {
    _notifyException(error);
  }

  return result;
}

/*
* Generate Databases API
*/
export async function generate_databases(categoryIDs) {
  let result = { data: null, isError: true }; // Default result in case of error  
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/generate_databases`, {
      method: 'GET',
      // credentials: 'include'
      }, {
        categoryIDs: categoryIDs
      });
    if (response.ok) {
      const payload = await response.json(); // Should be { 'status': 'success' }
      result = { data: payload, isError: false };
    }
    
  }
  catch (error) {
    _notifyException(error);
  }

  return result;
}

/*
* Document related API
*/
export async function getDocumentInfo(documentID) {
  let result = null; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/doc/${documentID}`, {
      method: 'GET',
      // credentials: 'include'
      });

    if (response.ok) {
      result = await response.json();
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

export async function getDocumentDescription(documentID) {
  let result = null; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/doc/summary/${documentID}`, {
      method: 'GET',
      // credentials: 'include'
      });

    if (response.ok) {
      const payload = await response.json();
      result = payload.summary;
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

export async function getCategoryDescription(categoryPath) {
  let result = null; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/category/description`, {
      method: 'GET',
      // credentials: 'include'
      }, {
        category: categoryPath
      });

    if (response.ok) {
      const payload = await response.json();
      result = payload.description;
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

/**
 * Generate summary API 
 */
export async function generateSummary(text) {
  let result = ''; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/llm/summary`, {
      method: 'POST',
      // credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ text: text })
    });
    if (response.ok) {
      const payload = await response.json();
      result = payload.summary;
    }
    else if (response.status === 422) {
      notify({
        title: 'LLM Context Window Exceeded',
        message: `Too many tokens in the context or search results. <br />Please remove some excerptst or documents from the context or search results.`,
        color: 'info',
        icon: 'error',
        duration:  15000,
        html: true
      })
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

/*  
* Generate answer API 
*/
export async function generateAnswer(user_query, text, excludeLLMKnowledgebase, promptKey, searchQuery) {
  let result = ''; // Default result in case of error
  
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/llm/answer`, {
      method: 'POST',
      // credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ text: text, user_query: user_query, exclude_llm_knowledgebase: excludeLLMKnowledgebase, prompt_key: promptKey, search_query: searchQuery })
    });

    if (response.ok) {
      const payload = await response.json();
      result =  payload.answer;
    }
    else if (response.status === 422) {
      notify({
        title: 'LLM Context Window Exceeded',
        message: `Too many tokens in the context or search results. <br />Please remove some excerptst or documents from the context or search results.`,
        color: 'info',
        icon: 'error',
        duration:  15000,
        html: true
      })
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result
}

/*  
* Generate suggested queries API 
*/
export async function generateSugggestedQueries(text) {
  let result = []; // Default result in case of error

  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/llm/suggest_queries`, {
      method: 'POST',
      // credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ text: text })
    });

    if (response.ok) {
      result = await response.json();
    }
    else if (response.status === 422) {
      notify({
        title: 'LLM Context Window Exceeded',
        message: `Too many tokens in the context or search results. <br />Please remove some excerptst or documents from the context or search results.`,
        color: 'info',
        icon: 'error',
        duration:  15000,
        html: true
      })
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result
}

export async function getExcerptConcise(excerptText) {
  let result = null; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/search/excerpt/concise`, {
      method: 'POST',
      // credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({content: excerptText })
      });

    if (response.ok) {
      const payload = await response.json();
      result = payload.concise;
    }
    
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

export async function get_chunk_text(documentID, chunk_id) {
  let result = null; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/search/chunk/content/${documentID}/${chunk_id}`, {
      method: 'GET',
      // credentials: 'include'
      });

    if (response.ok) {
      const payload = await response.json();
      result = payload.content;
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

export async function getExcerptChunks(documentID, firstChunkId, lastChunkId) {
  let result = null; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/search/excerpt/chunks/${documentID}?&first_chunk_id=${firstChunkId}&last_chunk_id=${lastChunkId}`, {
      method: 'GET',
      // credentials: 'include'
      });

    if (response.ok) {
      const payload = await response.json();
      result = payload.excerpt;
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

/*
* User API
*/
export async function login(form) {
  try {
      // Make the POST request to log in the user
      const response = await fetch(`${Config.API_SERVER}/api/user/login`, {
          method: 'POST',
          // credentials: 'include', // TODO: remove this after completing bearer token authentication everywhere
          headers: {
          'Content-Type': 'application/json'
          },
          body: JSON.stringify(form)
      });
  
      if (response.status == 401) {
          return null;
      }
  
      if (!response.ok) {
          return null; // Handle login failure
      }
      const user_data = await response.json();

      // store token in local storage
      localStorage.setItem('_id_', user_data.access_token);
      localStorage.setItem('user', JSON.stringify(user_data.user));
  
      return user_data; // Return true to indicate successful login
  } 
  catch (error) {
      console.log('Login error:', error);
      return null; // Return false to indicate login failure
  }
}

export async function logout() {
  const token = localStorage.getItem('_id_');
  if (!token) {
    console.log('No token found, skipping logout');
    return;
  }
  
  // Send a request to the logout endpoint
  const response = await fetchAuth(`${Config.API_SERVER}/api/user/logout`, {
      method: 'GET',
      // // credentials: 'include',
      headers: {
        'Authorization': `Bearer ${token}`
      }
  });

  // remove token and user from local storage
  localStorage.removeItem('_id_');
  localStorage.removeItem('user');
}

export async function changePassword(newPassword) {
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/user/change-password`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ new_password: newPassword })
    });
    if (response.ok) {
      return true;
    }
    return false;
  }
  catch (error) {
    _notifyException(error);
    return false;
  }
}

export async function getUserFromServer() {
  try {
      // Make the GET request to fetch all users
      const response = await fetchAuth(`${Config.API_SERVER}/api/user/info`, {
          method: 'GET',
          // credentials: 'include'
      });
      if (response.ok) {
          const user = await response.json();
          return user;
      }
      return null;
  } 
  catch (error) {
    // window.alert('Error getting users:', error.message);
    return null;
  }
}

export async function viewSourceDocument(documentIdOrPath, isPath) {
  let result = { data: null, isError: true }; // Default result in case of error
  try {
    let url = null;
    if (isPath) {
      url = `${Config.API_SERVER}/doc/send?documentPath=${encodeURIComponent(documentIdOrPath)}`
    }
    else {
      url = `${Config.API_SERVER}/doc/send?documentId=${documentIdOrPath}`
    }
    const response = await fetchAuth(url);
    
    if (response.ok) {
      // Get the blob data and return it
      const blob = await response.blob();
      result = { data: blob, isError: false };
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

export async function highlightPdf(pdfUrl, pageNumber, highlights) {
  let result = { data: null, isError: true }; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/doc/highlight-pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        pdfUrl: pdfUrl,
        pageNumber: pageNumber,
        highlights: highlights
      })
    });
    
    if (response.ok) {
      // Get the response as a blob
      const blob = await response.blob();
      result = { data: blob, isError: false };
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

export async function getExcerptByHash(hash) {
  let result = { data: null, isError: true }; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/excerpt/${hash}`, {
      method: 'GET',
    });

    if (response.ok) {
      const payload = await response.json();
      result = { data: payload, isError: false };
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

export async function downloadPdf(reportData) {
  let result = { data: null, isError: true }; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/reports/download-pdf-report`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(reportData),
    });

    if (response.ok) {
      const blob = await response.blob();
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${reportData.sessionName || 'report'}.pdf`;
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      result = { data: 'success', isError: false };
      
      notify({
        title: 'PDF Downloaded',
        message: 'Your report has been downloaded successfully.',
        color: 'positive',
        icon: 'download',
        duration: 3000,
        position: 'bottom-right'
      });
    }
  } 
  catch (error) {
    _notifyException(error);
  }

  return result;
}

export async function runKBBuilder() {
  let result = "Error"; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/kb_builder/start`, {
      method: 'POST',
    });
    if (response.ok) {
      const payload = await response.json();
      result = payload.status;
    }
  }
  catch (error) {
    _notifyException(error);
  }
  return result;
}

export async function getKBBuilderStatus() {
  let result = 'Error'; // Default result in case of error
  try {
    const response = await fetchAuth(`${Config.API_SERVER}/api/kb_builder/status`, {
      method: 'GET',
    });
    if (response.ok) {
      const payload = await response.json();
      result = payload.status;
    }
  }
  catch (error) {
    _notifyException(error);
  }
  return result;
}