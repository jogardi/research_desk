The noun highlighting is currently the slowest part of the search.
Let's move this from the server (python to the client).
Use this https://huggingface.co/Xenova/all-MiniLM-L6-v2
The server is currently using the mebedding model, all-MiniLM-L6-v2,
to see what nouns match the query. 
There is a javascript version of the exact same model.
Example usage:
```
import { pipeline } from '@huggingface/transformers';

// Create a feature-extraction pipeline
const extractor = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');

// Compute sentence embeddings
const sentences = ['This is an example sentence', 'Each sentence is converted'];
const output = await extractor(sentences, { pooling: 'mean', normalize: true });
```

So we can make our code work on the client.
