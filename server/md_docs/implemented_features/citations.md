I want to implement citations meaning I want the response from the LLM to have clickable numbers next to it's claims in it's response so that when the user clicks on a number they are taken to the search result that supports that claim. 

or the citations, we will associate an integer id with each excerpt that the chat model is given. Then the chat model can include a citation at any point in it's response by putting the id in brackets (e.g. [1]). Then the UI will make every id in brackets clickable. Clicking an id in brackets will be just like clicking the "show excerpt in source" button.
The prompt will be:
For every fact, statistic, or piece of information in your answer that comes from a specific excerpt, include a citation. Citations should be formatted as numbers in square brackets, e.g., [1], [2], etc., where the number corresponds to the excerpt's position in the list (starting from 1).
   - Example: If you use information from the first excerpt, write: "The capital of France is Paris [1]."
   - If you use information from multiple excerpts, you can cite them together: "The capital of France is Paris [1][2]."

Some of the available sources are excerpts that the user moved to context and some are search results from the search tool. Let's start by making citatations work for excerpts moved to the context.

Current bugs:
- It tries to cite search results even though that is not supported right now
- The incrementing integer ids will get thrown off if something is added to or removed from context. Old messsages could cite someting that is not in the context
- The search results from the search tool don't get sent back to the UI so the agent does not remember those search results in the next conversation turn.