#!/usr/bin/env python3
"""
Example usage of FlashRank for local document reranking.

FlashRank is a lightweight, CPU-based reranking library that provides
fast local reranking without requiring API calls or GPU resources.
"""

from webservice.llm.together.rerank import Reranker


def main():
    # Initialize the reranker
    reranker = Reranker(model="test-model")
    
    # Example query and documents
    query = "How to improve machine learning model performance?"
    
    documents = [
        "Feature selection is crucial for improving machine learning model performance by reducing dimensionality.",
        "The weather forecast shows rain tomorrow with a 70% chance of precipitation.",
        "Hyperparameter tuning using grid search or random search can significantly boost model accuracy.",
        "This recipe for chocolate cake requires flour, sugar, eggs, and cocoa powder.",
        "Cross-validation techniques help prevent overfitting and provide better model evaluation.",
        "Regular exercise and a balanced diet are important for maintaining good health.",
        "Ensemble methods like Random Forest and Gradient Boosting often outperform single models.",
        "The stock market showed volatility today with tech stocks leading the decline."
    ]
    
    print("Original Document Order:")
    for i, doc in enumerate(documents):
        print(f"{i+1}. {doc[:60]}...")
    
    print("\n" + "="*80)
    print("FLASHRANK RERANKING RESULTS")
    print("="*80)
    
    # Use FlashRank for reranking
    results = reranker.flashrank(query, documents)
    
    print(f"\nQuery: {query}")
    print(f"Reranked {len(results)} documents using FlashRank:\n")
    
    for rank, result in enumerate(results, 1):
        doc_index = result['index']
        score = result['score']
        doc_text = documents[doc_index]
        
        print(f"Rank {rank}: (Score: {score:.6f})")
        print(f"  Original Index: {doc_index}")
        print(f"  Text: {doc_text}")
        print()
    
    # Show the top 3 most relevant documents
    print("="*80)
    print("TOP 3 MOST RELEVANT DOCUMENTS:")
    print("="*80)
    
    for i in range(min(3, len(results))):
        result = results[i]
        doc_text = documents[result['index']]
        print(f"{i+1}. Score: {result['score']:.6f}")
        print(f"   {doc_text}")
        print()


if __name__ == "__main__":
    main() 