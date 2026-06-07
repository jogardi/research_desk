After looking up the most relevant chunks and grouping those chunks by document,
we rank the documents using a reranker. The reranker sees the relevant chunks from each document. 

Right now the reranker is too slow so I want to replace the reranker with a formula based on the scores from 
the embedding model and bm25. So I want to do 
```
f(chunks, p) = \frac{\sum_i p_1 emb_score(chunks[i]) + p_2 bm25_score(chunks[i])}{len(chunks)^{p_3}}
\argmin_p (ranker_score(chunks) -  f(chunks, p))^2
.1 < p_3 <= 1
p_1 >= 0
p_2 >= 0
```
chunks is the array of most relevant chunks for a given document. 

I want to use gradient descent to optimize p.

The semanticSearchByDoc function takes a list of categories and a query as input.

To make training data we will use the ~/query_log2.csv for examples of real queries.
There is a CATEGORIES column and QUERY column. Deduplicate queries where queries are considered dupliate
if they are the same after running `x.lower().replace(' ', '')`. 

Run semanticSearchByDoc on each of these examples.

We need to modify semanticSearchByDoc to have the option to return the bm25 score and 
semantic score for each chunk. It already gives the score from the reranker.

The dataset resulting dataset will be a csv file with columns. 


