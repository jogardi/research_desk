# specific concerns we need to look for

# are we putting the right amount of weight on bm25

# is it reliably finding exact matches? It would be a real endictment to miss an exact match

## is chunkless rag behaving reasonably?
I should rerun lib/shared/tests/test_joint_emb.py and also add more test cases. 
More cases can be found in my jupter notebooks.

## is the hnswlib doing much worse than exact search?

## is the bm25 score being very large actually a problem?
we should look for cases where a rare word which exactly matches should not have been included in search results.
It is hard to imagine such a case.

## does the way we do top-k make sense?
Right now we have top-k per category. Why per category and not per document?
Also, the system is returning more than top-k  chunks because it is returning top-k chunks + adjacent chunks. 

# is it ok that there is a hard rule of bringing back adjacent chunks


# LLM preference
This seems like what we should have done in the first place. 

Only complaints about this approach are:
- LLM without vision would not be able to judge how well formatted the search results are
- running this benchmark would be slow since it is running the system end to end
- people will say they don't trust the LLM

# vision language model preference
It looks like claude is quite good at QA for formatting by using it's vision. https://claude.ai/share/46d45b7b-aa3b-4309-b43a-4ea2818b3611


# BEIR 
BEIR and benchmarks like it are based on the ranking that results from the cosine similarity of the embeddings. 

I look at academic benchmarks like BEIR and I take the model that does best.
I'm not trying to compete with the models listed in those leaderboards. I just take the best they have to offer.

But the difference between academia and what we are doing is that these academic benchmarks are ranking prechunked text 
while we have to do parsing, chunking and concatenate search results for each document. Then rank the documents.

# QA accuracy
One surprise I encountered here is that simply setting the top k to be very larger  easily allows
 the LLM to get near 100% accuracy. LLMs are just so good with long  context. 
 
So then I should make the goal to be getting the best accuracy while also minimizing the number of characters retrieved. 
That way, it is not as simple as using large top-k.

Another doubt I had is weather or not the model is just answering from what it knows in it's training data.

Another doubt is that it is limited to a narrow benchmark that may not resemble real-world corpora.

The nice thing is that this is based on using human provided labels in a dataset. 
This QA accuracy feels like what would be legit looking for an academic paper. 

# mimic the reranker

The nice thing about this is that it could allow me to iterate exremey quickly and maybe even do supervised learning with gradient descent. 


# can a vision language model judge the quality of the formatting?
