import pytest
import numpy as np
import tempfile
import os
import hnswlib


class TestHnswlibDuplicateIds:
    """Test what happens when adding items with duplicate IDs to hnswlib directly"""
    
    def test_duplicate_ids_behavior(self):
        """Test adding items with the same IDs to see what happens"""
        # Create a temporary file for the database
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            # Initialize hnswlib index directly
            dim = 3
            index = hnswlib.Index(space='cosine', dim=dim)
            
            # Create some test embeddings
            embeddings1 = np.array([
                [1.0, 2.0, 3.0],
                [4.0, 5.0, 6.0],
                [7.0, 8.0, 9.0]
            ], dtype=np.float32)
            
            embeddings2 = np.array([
                [10.0, 11.0, 12.0],
                [13.0, 14.0, 15.0]
            ], dtype=np.float32)
            
            # IDs for first batch
            ids1 = [1, 2, 3]
            
            # Initialize and add first batch of items
            print("Initializing index and adding first batch of items...")
            index.init_index(max_elements=1000, ef_construction=200, M=16)
            index.add_items(embeddings1, ids1)
            
            # Check item count after first addition
            count_after_first = index.element_count
            print(f"Item count after first addition: {count_after_first}")
            
            # Try to add items with duplicate IDs
            duplicate_ids = [1, 2]  # These IDs already exist
            
            print("Adding items with duplicate IDs...")
            try:
                index.add_items(embeddings2, duplicate_ids)
                print("Successfully added items with duplicate IDs")
                
                # Check item count after duplicate addition
                count_after_duplicate = index.element_count
                print(f"Item count after duplicate addition: {count_after_duplicate}")
                
                # Check if the items were actually added or replaced
                if count_after_duplicate > count_after_first:
                    print("New items were added (duplicates allowed)")
                elif count_after_duplicate == count_after_first:
                    print("Items were replaced (duplicates overwritten)")
                else:
                    print("Unexpected behavior: item count decreased")
                    
                # Let's also check what IDs are actually in the index
                all_ids = index.get_ids_list()
                print(f"All IDs in index: {sorted(all_ids)}")
                    
            except Exception as e:
                print(f"Exception occurred when adding duplicate IDs: {e}")
                print(f"Exception type: {type(e)}")
                
        finally:
            # Clean up temporary file
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_same_id_multiple_times(self):
        """Test adding the same ID multiple times in sequence"""
        try:
            dim = 2
            index = hnswlib.Index(space='cosine', dim=dim)
            index.init_index(max_elements=1000, ef_construction=200, M=16)
            
            # Add same ID multiple times with different embeddings
            for i in range(3):
                embedding = np.array([[float(i), float(i+1)]], dtype=np.float32)
                print(f"Adding ID 1 for the {i+1}th time with embedding {embedding}")
                
                try:
                    index.add_items(embedding, [1])
                    count = index.element_count
                    print(f"Item count after {i+1}th addition: {count}")
                    
                    # Check what IDs are in the index
                    all_ids = index.get_ids_list()
                    print(f"All IDs in index: {sorted(all_ids)}")
                    
                except Exception as e:
                    print(f"Exception on {i+1}th addition: {e}")
                    break
                    
        except Exception as e:
            print(f"Exception in test setup: {e}")
    
    def test_mixed_duplicate_and_new_ids(self):
        """Test adding a mix of duplicate and new IDs"""
        try:
            dim = 2
            index = hnswlib.Index(space='cosine', dim=dim)
            index.init_index(max_elements=1000, ef_construction=200, M=16)
            
            # First batch
            embeddings1 = np.array([
                [1.0, 2.0],
                [3.0, 4.0],
                [5.0, 6.0]
            ], dtype=np.float32)
            ids1 = [1, 2, 3]
            
            print("Adding first batch...")
            index.add_items(embeddings1, ids1)
            print(f"Item count after first batch: {index.element_count}")
            print(f"IDs after first batch: {sorted(index.get_ids_list())}")
            
            # Second batch with mix of duplicate and new IDs
            embeddings2 = np.array([
                [7.0, 8.0],  # ID 1 (duplicate)
                [9.0, 10.0], # ID 4 (new)
                [11.0, 12.0] # ID 2 (duplicate)
            ], dtype=np.float32)
            ids2 = [1, 4, 2]
            
            print("Adding mixed batch (duplicates and new)...")
            try:
                index.add_items(embeddings2, ids2)
                final_count = index.element_count
                final_ids = sorted(index.get_ids_list())
                print(f"Final item count: {final_count}")
                print(f"Final IDs: {final_ids}")
                
                if final_count == 4:  # 3 original + 1 new
                    print("Duplicates were replaced, new items added")
                elif final_count == 6:  # 3 original + 3 new
                    print("All items were added (duplicates allowed)")
                else:
                    print(f"Unexpected final count: {final_count}")
                    
            except Exception as e:
                print(f"Exception with mixed batch: {e}")
                
        except Exception as e:
            print(f"Exception in test setup: {e}")
    
    def test_save_and_load_with_duplicates(self):
        """Test saving and loading an index with duplicate IDs"""
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            dim = 2
            index = hnswlib.Index(space='cosine', dim=dim)
            index.init_index(max_elements=1000, ef_construction=200, M=16)
            
            # Add initial items
            embeddings1 = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
            ids1 = [1, 2]
            index.add_items(embeddings1, ids1)
            
            # Add duplicate
            embeddings2 = np.array([[5.0, 6.0]], dtype=np.float32)
            ids2 = [1]  # Duplicate ID
            index.add_items(embeddings2, ids2)
            
            print(f"Before save - Count: {index.element_count}, IDs: {sorted(index.get_ids_list())}")
            
            # Save and reload
            index.save_index(db_path)
            
            # Create new index and load
            new_index = hnswlib.Index(space='cosine', dim=dim)
            new_index.load_index(db_path, max_elements=1000)
            
            print(f"After load - Count: {new_index.element_count}, IDs: {sorted(new_index.get_ids_list())}")
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


if __name__ == "__main__":
    # Run the tests
    test_instance = TestHnswlibDuplicateIds()
    print("=== Testing duplicate IDs behavior ===")
    test_instance.test_duplicate_ids_behavior()
    print("\n=== Testing same ID multiple times ===")
    test_instance.test_same_id_multiple_times()
    print("\n=== Testing mixed duplicate and new IDs ===")
    test_instance.test_mixed_duplicate_and_new_ids()
    print("\n=== Testing save and load with duplicates ===")
    test_instance.test_save_and_load_with_duplicates() 