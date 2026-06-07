In order to accurately maintain the list of messages 
for the chatbot conversation,
the server needs to send back
not only the response for the user but also the tool calls and responses back 
to the client via websocket. 
The client should add all this stuff sent back to it's list of messages.
Sending tool responses back means that when the user asks a follow up question, the search results 
from the agent's previous tool calls will still be visible to the agent. 

However, we cannot send back the tool call and response for read_page because
the image takes too many tokens. 



