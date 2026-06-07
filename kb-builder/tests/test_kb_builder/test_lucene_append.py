import pytest
import tempfile
import os
import shutil
from pyserini.index.lucene import LuceneIndexer


class TestLuceneAppend:
    """Test LuceneIndexer append functionality with /tmp database"""
    
    def test_lucene_append_behavior(self):
        """Test creating a database in /tmp and then adding to it again"""
        # Create a temporary directory in /tmp
        temp_dir = tempfile.mkdtemp(dir='/tmp', prefix='lucene_test_')
        
        try:
            print(f"Created temporary directory: {temp_dir}")
            
            # First batch of documents
            documents1 = [
                {
                    'id': '1',
                    'contents': 'This is the first document about machine learning.'
                },
                {
                    'id': '2', 
                    'contents': 'This is the second document about artificial intelligence.'
                },
                {
                    'id': '3',
                    'contents': 'This is the third document about deep learning.'
                }
            ]
            
            # Create initial index
            print("Creating initial Lucene index...")
            lucene1 = LuceneIndexer(temp_dir, append=False)  # Create new index
            lucene1.add_batch_dict(documents1)
            lucene1.close()
            
            # Check if index files were created
            index_files = os.listdir(temp_dir)
            print(f"Index files after first creation: {index_files}")
            
            # Second batch of documents
            documents2 = [
                {
                    'id': '4',
                    'contents': 'This is the fourth document about neural networks.'
                },
                {
                    'id': '5',
                    'contents': 'This is the fifth document about computer vision.'
                }
            ]
            
            # Try to append to existing index
            print("Appending to existing Lucene index...")
            try:
                lucene2 = LuceneIndexer(temp_dir, append=True)  # Append to existing
                lucene2.add_batch_dict(documents2)
                lucene2.close()
                print("Successfully appended to existing index")
                
                # Check if new files were added
                index_files_after_append = os.listdir(temp_dir)
                print(f"Index files after append: {index_files_after_append}")
                
                # Try to read the index to see if all documents are there
                print("Attempting to read the combined index...")
                try:
                    from pyserini.search.lucene import LuceneSearcher
                    searcher = LuceneSearcher(temp_dir)
                    total_docs = searcher.num_docs
                    print(f"Total documents in index: {total_docs}")
                    
                    # Try a simple search to verify documents are accessible
                    hits = searcher.search("machine learning", k=10)
                    print(f"Search results for 'machine learning': {len(hits)} hits")
                    for i, hit in enumerate(hits):
                        print(f"  Hit {i+1}: docid={hit.docid}, score={hit.score}")
                    
                    searcher.close()
                    
                except Exception as e:
                    print(f"Error reading index: {e}")
                    
            except Exception as e:
                print(f"Error appending to index: {e}")
                print(f"Exception type: {type(e)}")
                
        finally:
            # Clean up
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temporary directory: {temp_dir}")
    
    def test_lucene_append_with_duplicate_ids(self):
        """Test appending documents with duplicate IDs"""
        temp_dir = tempfile.mkdtemp(dir='/tmp', prefix='lucene_duplicate_test_')
        
        try:
            print(f"Created temporary directory: {temp_dir}")
            
            # Initial documents
            documents1 = [
                {
                    'id': '1',
                    'contents': 'Original document with ID 1.'
                },
                {
                    'id': '2',
                    'contents': 'Original document with ID 2.'
                }
            ]
            
            # Create initial index
            print("Creating initial index...")
            lucene1 = LuceneIndexer(temp_dir, append=False)
            lucene1.add_batch_dict(documents1)
            lucene1.close()
            
            # Documents with duplicate IDs
            documents2 = [
                {
                    'id': '1',  # Duplicate ID
                    'contents': 'Updated document with ID 1.'
                },
                {
                    'id': '3',  # New ID
                    'contents': 'New document with ID 3.'
                }
            ]
            
            # Try to append with duplicates
            print("Appending with duplicate IDs...")
            try:
                lucene2 = LuceneIndexer(temp_dir, append=True)
                lucene2.add_batch_dict(documents2)
                lucene2.close()
                print("Successfully appended with duplicate IDs")
                
                # Check the final state
                from pyserini.search.lucene import LuceneSearcher
                searcher = LuceneSearcher(temp_dir)
                total_docs = searcher.num_docs
                print(f"Total documents after append with duplicates: {total_docs}")
                
                # Search for the duplicate ID to see which version we get
                hits = searcher.search("ID 1", k=5)
                print(f"Search results for 'ID 1': {len(hits)} hits")
                for i, hit in enumerate(hits):
                    print(f"  Hit {i+1}: docid={hit.docid}, score={hit.score}")
                    # Get the actual document content
                    doc = searcher.doc(hit.docid)
                    print(f"    Content: {doc.contents()}")
                
                searcher.close()
                
            except Exception as e:
                print(f"Error appending with duplicates: {e}")
                
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_lucene_multiple_appends(self):
        """Test multiple append operations"""
        temp_dir = tempfile.mkdtemp(dir='/tmp', prefix='lucene_multiple_test_')
        
        try:
            print(f"Created temporary directory: {temp_dir}")
            
            # Multiple batches
            batches = [
                [{'id': '1', 'contents': 'Batch 1, document 1'}],
                [{'id': '2', 'contents': 'Batch 2, document 2'}],
                [{'id': '3', 'contents': 'Batch 3, document 3'}],
                [{'id': '4', 'contents': 'Batch 4, document 4'}]
            ]
            
            for i, batch in enumerate(batches):
                print(f"Processing batch {i+1}...")
                
                if i == 0:
                    # First batch - create new index
                    lucene = LuceneIndexer(temp_dir, append=False)
                else:
                    # Subsequent batches - append
                    lucene = LuceneIndexer(temp_dir, append=True)
                
                lucene.add_batch_dict(batch)
                lucene.close()
                
                # Check current state
                from pyserini.search.lucene import LuceneSearcher
                searcher = LuceneSearcher(temp_dir)
                total_docs = searcher.num_docs
                print(f"  Documents after batch {i+1}: {total_docs}")
                searcher.close()
            
            # Final verification
            from pyserini.search.lucene import LuceneSearcher
            searcher = LuceneSearcher(temp_dir)
            final_docs = searcher.num_docs
            print(f"Final document count: {final_docs}")
            
            # Search for all documents
            hits = searcher.search("document", k=10)
            print(f"Search results for 'document': {len(hits)} hits")
            for i, hit in enumerate(hits):
                print(f"  Hit {i+1}: docid={hit.docid}")
            
            searcher.close()
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Run the tests
    test_instance = TestLuceneAppend()
    print("=== Testing Lucene append behavior ===")
    test_instance.test_lucene_append_behavior()
    print("\n=== Testing Lucene append with duplicate IDs ===")
    test_instance.test_lucene_append_with_duplicate_ids()
    print("\n=== Testing multiple Lucene appends ===")
    test_instance.test_lucene_multiple_appends() 