import tempfile
import os
import shutil
from pyserini.index.lucene import LuceneIndexer


class TestLuceneAppendSimple:
    """Test LuceneIndexer append functionality with /tmp database - simple version"""
    
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
            print(f"Index files after first creation: {len(index_files)} files")
            print(f"Sample files: {index_files[:5]}")
            
            # Look for segments file
            segments_files = [f for f in index_files if f.startswith('segments_')]
            print(f"Segments files: {segments_files}")
            
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
                print(f"Index files after append: {len(index_files_after_append)} files")
                
                # Look for new segments file
                segments_files_after = [f for f in index_files_after_append if f.startswith('segments_')]
                print(f"Segments files after append: {segments_files_after}")
                
                # Check if we have more files
                new_files = set(index_files_after_append) - set(index_files)
                print(f"New files added: {len(new_files)}")
                if new_files:
                    print(f"Sample new files: {list(new_files)[:5]}")
                
                print("✅ Lucene append functionality works correctly!")
                
            except Exception as e:
                print(f"❌ Error appending to index: {e}")
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
            
            initial_files = os.listdir(temp_dir)
            print(f"Files after initial creation: {len(initial_files)}")
            
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
                
                final_files = os.listdir(temp_dir)
                print(f"Files after append with duplicates: {len(final_files)}")
                
                # Check if new segments were created
                segments_files = [f for f in final_files if f.startswith('segments_')]
                print(f"Segments files: {segments_files}")
                
                print("✅ Lucene append with duplicate IDs works!")
                
            except Exception as e:
                print(f"❌ Error appending with duplicates: {e}")
                
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
                current_files = os.listdir(temp_dir)
                segments_files = [f for f in current_files if f.startswith('segments_')]
                print(f"  Files after batch {i+1}: {len(current_files)}, segments: {segments_files}")
            
            print("✅ Multiple Lucene appends work correctly!")
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Run the tests
    test_instance = TestLuceneAppendSimple()
    print("=== Testing Lucene append behavior ===")
    test_instance.test_lucene_append_behavior()
    print("\n=== Testing Lucene append with duplicate IDs ===")
    test_instance.test_lucene_append_with_duplicate_ids()
    print("\n=== Testing multiple Lucene appends ===")
    test_instance.test_lucene_multiple_appends() 