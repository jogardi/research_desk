# agentic chunking and post correction
We will use a vision language model to both make corrections to the transcription and do chunking of the text into sentence like chunks. 
Provide an image of the pdf page to the model. 
Also provide the pdf blocks from marker seperated by "\n\n==8529==\n\n"
The model should output a mostly identical copy of it's text input except 
with some transcription errors corrected and with the single unicode character ✂️ as a delimiter to indicate boundaries between appropriate chunks.

For example, 
```
0: We attended the 1pm showing of Elio and showed up when the doors opened at 12:30pm so that we could ensure enough time for food to be ordered/delivered. We got to our seats, checked out the menu and placed an order around 12:45. 1:45 came and still no meal or drinks.

==8529==

1: Before I left I closed out my tab outside of the theater and asked for a copy and it still had an item that never came that the server mentioned that they would remove. 
```

becomes 

```
0: We attended the 1pm showing of Elio and showed up when the doors opened at 12:30pm so that we could ensure enough time for food to be ordered/delivered. ✂️We got to our seats, checked out the menu and placed an order around 12:45. 1:45 came and still no meal or drinks.

==8529==

1: Before I left I closed out my tab outside of the theater and asked for a copy and it still had an item that never came that the server mentioned that they would remove. 
```

When this feature is enabled, chunker.py will simply do `text.split('✂️')`