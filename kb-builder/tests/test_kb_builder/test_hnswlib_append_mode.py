import pytest
import numpy as np
import tempfile
import os
import hnswlib


class TestHnswlibAppendMode:
    """Test hnswlib behavior when loading existing index and adding duplicate IDs"""
    
    def test_hnswlib_append_mode_duplicate_ids(self):
        """Test what happens when you load an existing index and add duplicate IDs"""
        # Create a temporary file for the database
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            dim = 3
            
            # === PHASE 1: Create initial index ===
            print("=== PHASE 1: Creating initial index ===")
            index1 = hnswlib.Index(space='cosine', dim=dim)
            index1.init_index(max_elements=1000, ef_construction=200, M=16)
            
            # Add initial embeddings
            embeddings1 = np.array([
                [1.0, 2.0, 3.0],
                [4.0, 5.0, 6.0],
                [7.0, 8.0, 9.0]
            ], dtype=np.float32)
            ids1 = [1, 2, 3]
            
            index1.add_items(embeddings1, ids1)
            print(f"Added initial items. Count: {index1.element_count}")
            print(f"Initial IDs: {sorted(index1.get_ids_list())}")
            
            # Save the index
            index1.save_index(db_path)
            print(f"Saved index to: {db_path}")
            
            # === PHASE 2: Load existing index (append mode) ===
            print("\n=== PHASE 2: Loading existing index (append mode) ===")
            index2 = hnswlib.Index(space='cosine', dim=dim)
            index2.load_index(db_path, max_elements=1000)
            
            print(f"Loaded index. Count: {index2.element_count}")
            print(f"Loaded IDs: {sorted(index2.get_ids_list())}")
            
            # === PHASE 3: Add items with duplicate IDs ===
            print("\n=== PHASE 3: Adding items with duplicate IDs ===")
            embeddings2 = np.array([
                [10.0, 11.0, 12.0],  # ID 1 (duplicate)
                [13.0, 14.0, 15.0],  # ID 4 (new)
                [16.0, 17.0, 18.0]   # ID 2 (duplicate)
            ], dtype=np.float32)
            ids2 = [1, 4, 2]  # Mix of duplicate and new IDs
            
            try:
                index2.add_items(embeddings2, ids2)
                print("Successfully added items with duplicate IDs")
                
                print(f"Final count: {index2.element_count}")
                print(f"Final IDs: {sorted(index2.get_ids_list())}")
                
                # Check if we can retrieve the items
                print("\n=== Checking retrieved items ===")
                for test_id in [1, 2, 3, 4]:
                    if test_id in index2.get_ids_list():
                        try:
                            item = index2.get_items([test_id])
                            print(f"ID {test_id}: {item[0]}")
                        except Exception as e:
                            print(f"Error retrieving ID {test_id}: {e}")
                
                # Save the updated index
                index2.save_index(db_path)
                print("Saved updated index")
                
            except Exception as e:
                print(f"Exception when adding duplicate IDs: {e}")
                print(f"Exception type: {type(e)}")
            
            # === PHASE 4: Reload and verify ===
            print("\n=== PHASE 4: Reloading to verify persistence ===")
            index3 = hnswlib.Index(space='cosine', dim=dim)
            index3.load_index(db_path, max_elements=1000)
            
            print(f"Reloaded count: {index3.element_count}")
            print(f"Reloaded IDs: {sorted(index3.get_ids_list())}")
            
        finally:
            # Clean up temporary file
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_hnswlib_same_id_multiple_times_append_mode(self):
        """Test adding the same ID multiple times when loading existing index"""
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            dim = 2
            
            # Create and save initial index
            print("=== Creating initial index ===")
            index1 = hnswlib.Index(space='cosine', dim=dim)
            index1.init_index(max_elements=1000, ef_construction=200, M=16)
            
            initial_embedding = np.array([[1.0, 2.0]], dtype=np.float32)
            index1.add_items(initial_embedding, [1])
            index1.save_index(db_path)
            
            print(f"Initial: Count={index1.element_count}, IDs={sorted(index1.get_ids_list())}")
            
            # Load and add same ID multiple times
            print("\n=== Loading and adding same ID multiple times ===")
            for i in range(3):
                index = hnswlib.Index(space='cosine', dim=dim)
                index.load_index(db_path, max_elements=1000)
                
                new_embedding = np.array([[float(i+10), float(i+20)]], dtype=np.float32)
                print(f"Attempt {i+1}: Adding ID 1 with embedding {new_embedding[0]}")
                
                try:
                    index.add_items(new_embedding, [1])
                    print(f"  Success: Count={index.element_count}, IDs={sorted(index.get_ids_list())}")
                    
                    # Check what embedding we get back
                    retrieved = index.get_items([1])
                    print(f"  Retrieved for ID 1: {retrieved[0]}")
                    
                    # Save for next iteration
                    index.save_index(db_path)
                    
                except Exception as e:
                    print(f"  Exception: {e}")
                    break
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_hnswlib_append_mode_edge_cases(self):
        """Test edge cases in append mode"""
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            dim = 2
            
            # Create initial index with gaps in IDs
            print("=== Creating index with gaps in IDs ===")
            index1 = hnswlib.Index(space='cosine', dim=dim)
            index1.init_index(max_elements=1000, ef_construction=200, M=16)
            
            embeddings1 = np.array([
                [1.0, 1.0],
                [5.0, 5.0],
                [10.0, 10.0]
            ], dtype=np.float32)
            ids1 = [1, 5, 10]  # Gaps in IDs
            
            index1.add_items(embeddings1, ids1)
            index1.save_index(db_path)
            print(f"Initial IDs with gaps: {sorted(index1.get_ids_list())}")
            
            # Load and fill some gaps + add duplicates
            print("\n=== Loading and filling gaps + duplicates ===")
            index2 = hnswlib.Index(space='cosine', dim=dim)
            index2.load_index(db_path, max_elements=1000)
            
            embeddings2 = np.array([
                [2.0, 2.0],   # ID 2 (fill gap)
                [1.5, 1.5],   # ID 1 (duplicate)
                [15.0, 15.0], # ID 15 (new, beyond existing)
                [5.5, 5.5]    # ID 5 (duplicate)
            ], dtype=np.float32)
            ids2 = [2, 1, 15, 5]
            
            try:
                index2.add_items(embeddings2, ids2)
                print(f"Final count: {index2.element_count}")
                print(f"Final IDs: {sorted(index2.get_ids_list())}")
                
                # Check specific retrievals
                print("\n=== Checking specific retrievals ===")
                for test_id in [1, 2, 5, 10, 15]:
                    if test_id in index2.get_ids_list():
                        item = index2.get_items([test_id])
                        print(f"ID {test_id}: {item[0]}")
                
            except Exception as e:
                print(f"Exception: {e}")
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


if __name__ == "__main__":
    # Run the tests
    test_instance = TestHnswlibAppendMode()
    print("=== Testing hnswlib append mode with duplicate IDs ===")
    test_instance.test_hnswlib_append_mode_duplicate_ids()
    print("\n" + "="*60)
    print("=== Testing same ID multiple times in append mode ===")
    test_instance.test_hnswlib_same_id_multiple_times_append_mode()
    print("\n" + "="*60)
    print("=== Testing append mode edge cases ===")
    test_instance.test_hnswlib_append_mode_edge_cases() 