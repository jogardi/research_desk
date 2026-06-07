We want citations to still be clickable when the user reloads the page, adds to or removes from 
context, or if the citation is from earlier in the conversation.

We should identify each excerpt in the user context by a 4 character hash. This should be a hash of the chunk ids and the document id. 
We know that all the chunks in an excerpt are in the same document.
In order for the hash to be unique to the excerpt we must include not only the chunk ids but also the document id in the input to the hash because chunks in different categories could have the same chunk id despite being different chunks. 

Have an excerpts table in the database that maps these hashes to the list of chunk ids with their categories. Don't have duplicates in the table. 
This table can go in database/document.db.

Everytime the agent handles a request with some user context, add excerpts to the excerpts table. agent.py should intiialize the excerpts table if it was not 
already created.

In the system prompt for the agent, give the id for each excerpt.

When the user clicks on a citation, the UI sends a request with excerpt id to the server to get the pdf region. The server looks up the list of chunk ids with their categories for that excerpt in the excerpts table.
Then it looks up those chunks in the chunks table to get the corresponding pdf regions. 
Once the UI gets the pdf regions it can highlight them in the embedded pdf viewer. 
