ChatGPT does not seem to keep it's search results from prior 
conversation turns in the conversation history. Meanwhile claude does.

In ChatGPT if you ask a follow up question about something it previously saw in 
search results it has to do another search. Cluade could just answer
from still having the search results in it's messages.

For example,
user: "according to this what happend in 2003 https://spectrum.ieee.org/evolutionary-ai-coding-agents"

Both chat gpt and claude respond by searching. 

user: "for how many iterations did they run the DGM. Don't do another search. Just tell me based on what you already saw from your previous search"

ChatGPT gets confused by this but claude behaves as desired.

In our system, we store all messages on the browser
and send all messages to the server on every conversation turn,

We want citations to work for both the user's context and the search results from the agent's search tool. We don't want a citation of user's context to 
get confused with a citation of the agent's search tool.

We want our agent to be able to cite search results from earlier in the conversation. 

We should identify each excerpt in the user context or search results by a hash of the chunk ids with ther categories. 
Have an excerpts table in the database that maps these hashes to the list of chunk ids with their categories. 
Every time the search tool returns an excerpt, add that excerpt to the excerpts table. 

When the user clicks on a citation, the UI sends a request with excerpt id to the server to get the pdf region. The server looks up the list of chunk ids with their categories for that excerpt in the excerpts table.
Then it looks up those chunks in the chunks table to get the corresponding pdf regions. 

Once the UI gets the pdf regions it can highlight them in the embedded pdf viewer. 

In order for the agent to be able to use search results from prior conversation turns,
the search results need to be sent back to the UI. 
When the agent makes a search request that request needs to be sent back to the UI and appended
 to the list of messages.
Every time the search tool
returns a response, it's response should also be sent back the UI and appended to the list of messages.

prereuiqisite tasks:
- change the citation system for context to use uids. 
- send search results back to UI
