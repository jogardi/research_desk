from pathlib import Path
from shared.sqlite import SQLite
from shared.config import Config
from shared.logger import Logger
from shared.config import Config, load_cli_args
load_cli_args()

from shared.kb_folders import DB_FOLDER

class ResearchDeskLLMRoleSqlite:      
    def create_role(self, role: str, owner_id: str, kb_name: str):
        """Create a new LLM role."""
        db_path = Path(DB_FOLDER(kb_name)) / 'rd.db' 
        sqldb = SQLite(db_path) 
        
        try:
            sqldb.open() 
            role_id = sqldb.insert("insert into LLM_ROLE (ROLE, OWNER_ID) values (?, ?)", (role, owner_id))
            sqldb.commit()
            
            # Get the created role
            sqldb.select("select ID, ROLE, OWNER_ID from LLM_ROLE where ID = ?", (role_id,))
            row = sqldb.fetchone()
            
            if row:
                return {
                    'id': str(row[0]),
                    'role': row[1],
                    'owner_id': row[2]
                }, None, None
            else:
                return None, "Failed to create role", 500
                
        except Exception as e:
            Logger.error(f"Failed to create LLM role for owner {owner_id}", exception=e)
            return None, f"Exception: Failed to create LLM role: {str(e)}", 500
        finally:
            sqldb.close()
    
    def get_roles(self, owner_id: str, kb_name: str):
        """Get all LLM roles for a user."""
        db_path = Path(DB_FOLDER(kb_name)) / 'rd.db' 
        sqldb = SQLite(db_path) 
        
        try:
            sqldb.open() 
            sqldb.select("select ID, ROLE from LLM_ROLE where OWNER_ID = ?", (owner_id,))
            rows = sqldb.fetchall()

            #if no roles, get default roles
            if len(rows) == 0:
                sqldb.select("select ID, ROLE from LLM_ROLE_DEFAULT")
                rows = sqldb.fetchall()

                #insert default roles into LLM_ROLE table
                for row in rows:
                    sqldb.insert("insert into LLM_ROLE (ROLE, OWNER_ID) values (?, ?)", (row[1], owner_id))
                    sqldb.commit()
            
            roles = [
                {
                    "id": str(row[0]),
                    "role": row[1],
                    "owner_id": owner_id
                }
                for row in rows
            ]
 
            return roles, None, None
        except Exception as e:
            Logger.error(f"Failed to get LLM roles for owner {owner_id}", exception=e)
            return None, f"Exception: Failed to get LLM roles: {str(e)}", 500
        finally:
            sqldb.close()
    
    def get_role(self, role_id: str, kb_name: str):
        """Get a specific LLM role by ID."""
        db_path = Path(DB_FOLDER(kb_name)) / 'rd.db' 
        sqldb = SQLite(db_path) 
        
        try:
            sqldb.open() 
            sqldb.select("select ID, ROLE, OWNER_ID from LLM_ROLE where ID = ? ", (role_id,))
            row = sqldb.fetchone()
            
            if row:
                return {
                    'id': str(row[0]),
                    'role': row[1],
                    'owner_id': row[2]
                }, None, None
            else:
                return None, "Role not found", 404
                
        except Exception as e:
            Logger.error(f"Failed to get LLM role {role_id}", exception=e)
            return None, f"Exception: Failed to get LLM role: {str(e)}", 500
        finally:
            sqldb.close()
    
    def update_role(self, role_id: str, role: str, kb_name: str):
        """Update an LLM role."""
        db_path = Path(DB_FOLDER(kb_name)) / 'rd.db' 
        sqldb = SQLite(db_path) 
        
        try:
            sqldb.open() 
            sqldb.update("update LLM_ROLE set ROLE = ? where ID = ?", 
                        (role, role_id))
            sqldb.commit()
                
            return None, None
        except Exception as e:
            Logger.error(f"Failed to update LLM role {role_id}", exception=e)
            return f"Exception: Failed to update LLM role: {str(e)}", 500
        finally:
            sqldb.close()
 
    def delete_role(self, role_id: str, kb_name: str):
        """Delete an LLM role."""
        db_path = Path(DB_FOLDER(kb_name)) / 'rd.db' 
        sqldb = SQLite(db_path) 
        
        try:
            sqldb.open() 
            sqldb.delete("delete from LLM_ROLE where ID = ?", (role_id,))
            sqldb.commit()
                    
            return None, None
        except Exception as e:
            Logger.error(f"Failed to delete LLM role {role_id}", exception=e)
            return f"Exception: Failed to delete LLM role: {str(e)}", 500
        finally:
            sqldb.close()


def main(kb_name: str):
    """Test function for LLM Role CRUD operations."""
    print("=== Testing LLM Role CRUD Operations ===\n")
    
    # Initialize the database
    db = ResearchDeskLLMRoleSqlite()
    
    # Test data
    test_owner_id = "test-user-123"
    test_role_1 = "You are a helpful research assistant."
    test_role_2 = "You are a coding expert."
    test_role_updated = "You are an updated research assistant."
    
    created_role_ids = []
    
    try:
        # Test 1: Create Role
        print("1. Testing CREATE role...")
        role, error, status_code = db.create_role(test_role_1, test_owner_id, kb_name)
        if error:
            print(f"   ❌ CREATE failed: {error}")
        else:
            print(f"   ✅ CREATE successful: {role}")
            created_role_ids.append(role['id'])
        
        # Test 2: Create another role
        print("\n2. Testing CREATE second role...")
        role2, error, status_code = db.create_role(test_role_2, test_owner_id, kb_name)
        if error:
            print(f"   ❌ CREATE failed: {error}")  
        else:
            print(f"   ✅ CREATE successful: {role2}")
            created_role_ids.append(role2['id'])
        
        # Test 3: Get all roles
        print("\n3. Testing GET all roles...")
        roles, error, status_code = db.get_roles(test_owner_id, kb_name)
        if error:
            print(f"   ❌ GET all failed: {error}")
        else:
            print(f"   ✅ GET all successful: Found {len(roles)} roles")
            for role in roles:
                print(f"      - ID: {role['id']}, Role: {role['role'][:50]}...")
        
        # Test 4: Get specific role
        if created_role_ids:
            print(f"\n4. Testing GET specific role (ID: {created_role_ids[0]})...")
            role, error, status_code = db.get_role(created_role_ids[0], kb_name)
            if error:
                print(f"   ❌ GET specific failed: {error}")
            else:
                print(f"   ✅ GET specific successful: {role}")

        # Test 5: Update role
        if created_role_ids:
            print(f"\n5. Testing UPDATE role (ID: {created_role_ids[0]})...")
            error, status_code = db.update_role(created_role_ids[0], test_role_updated, kb_name)
            if error:
                print(f"   ❌ UPDATE failed: {error}")
            else:
                print(f"   ✅ UPDATE successful")
                
                # Verify the update
                updated_role, error, status_code = db.get_role(created_role_ids[0], kb_name)
                if not error:
                    print(f"      Verified: {updated_role['role'][:50]}...")
        
        # Test 6: Get non-existent role
        print("\n6. Testing GET non-existent role...")
        role, error, status_code = db.get_role("99999", kb_name)
        if error:
            print(f"   ✅ GET non-existent correctly returned error: {error}")
        else:
            print(f"   ❌ GET non-existent should have failed but returned: {role}")
        
        # Test 7: Delete role
        if created_role_ids:
            print(f"\n7. Testing DELETE role (ID: {created_role_ids[1]})...")
            error, status_code = db.delete_role(created_role_ids[1], kb_name)
            if error:
                print(f"   ❌ DELETE failed: {error}")
            else:
                print(f"   ✅ DELETE successful")
                
                # Verify the deletion
                deleted_role, error, status_code = db.get_role(created_role_ids[1], kb_name)
                if error:
                    print(f"      Verified: Role correctly deleted (error: {error})")
                else:
                    print(f"      ❌ Role still exists after deletion: {deleted_role}")
        
        # Test 8: Final state check
        print("\n8. Testing final state...")
        roles, error, status_code = db.get_roles(test_owner_id, kb_name)
        if error:
            print(f"   ❌ Final GET all failed: {error}")
        else:
            print(f"   ✅ Final state: {len(roles)} roles remaining")
            for role in roles:
                print(f"      - ID: {role['id']}, Role: {role['role'][:50]}...")
        
        print("\n=== Test Summary ===")
        print("✅ All CRUD operations tested successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main("demo")
        
