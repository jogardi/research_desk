import sqlite3
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from contextlib import contextmanager

@lru_cache()
def mutex(db_file_path):
    from threading import Lock
    return Lock()

class SQLite:
    """This class provides a simple interface to the database."""
    def __init__(self, db_file_path: str):
        """Initialize the database instance with the given database file path."""
        self.db_file_path = db_file_path
        self.conn = None
        self.cursor = None

    def exists(self) -> bool:
        return os.path.exists(self.db_file_path)

    def open(self) -> None:
        """
        Open a database connection.

        Important: 
            Calling this method closes existing connection if already open!
        
        returns: None
        """
        # Close the connection if it's already open - "re-open" the DB
        if self.conn is not None:
            self.close()

        db_path = Path(self.db_file_path)
        try:
            self.conn = sqlite3.connect(str(db_path),    timeout=30.0,  isolation_level='IMMEDIATE' )
        except Exception as e:
            print(f"Error occurred while opening the database: {e} at file path {db_path}")
            raise e

        self.cursor = self.conn.cursor()

    def close(self) -> None:
        """Close the database cursor and connection."""
        if self.cursor:
            self.cursor.close()  # Close the cursor
            self.cursor = None
        if self.conn:
            self.conn.close()  # Close the connection
            self.conn = None

    def begin_transaction(self) -> None:
        """
            Begin a new transaction. 
            This can be used for clarity when executing multiple db operations in a single transaction.
        """
        self.cursor.execute("BEGIN")

    def commit(self) -> None:
        """Commit the current transaction."""
        self.conn.commit()

    def rollback(self) -> None:
        """Roll back to the start of any pending transaction."""
        if self.conn is None:
            print("got rollback error")
            # print stack trace
            import traceback
            print(traceback.format_exc())
        else:
            self.conn.rollback()

    def execute(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """
        Execute a SQL query.

        params:
            query: str - the SQL query to execute
            params: Tuple - the parameters to pass to the query

        returns: sqlite3.Cursor - the cursor object
        """
        self.cursor.execute(query, params)
        return self.cursor
    
    def select(self, select_statement: str, params: Tuple = ()) -> None:
        """
        Select records from the database.
        Use the desired fetch method to retrieve the results.

        params:
            select_statement: str - the SELECT statement to execute
            params: Tuple - the parameters to pass to the query

        returns: None
        """
        self.cursor.execute(select_statement, params)

    def fetchall(self) -> List[Tuple]:
        """
        Fetch all rows of a query result.

        Returns: a list of tuples, where each tuple represents a row.
        """
        return self.cursor.fetchall()
    
    def fetchone(self) -> Optional[Tuple]:
        """
        Fetch the next row of a query result set.
        A result set is a set of rows returned by a query.

        Returns: a tuple representing a row, or None if no more rows are available.
        """
        return self.cursor.fetchone()
    
    def fetchmany(self, size: int) -> List[Tuple]:
        """
        Fetch the next set of rows of a query result, up to 'size' rows.

        params:
            size: int - the number of rows to fetch

        Returns: a list of tuples, where each tuple represents a row.
    
        """
        return self.cursor.fetchmany(size)
    
    def insert(self, insert_statement: str, params: Tuple = ()) -> int:
        """
        Insert a new record into the database and return its ID.

        params:
            insert_statement: str - the INSERT statement to execute
            params: Tuple - the parameters to pass to the query

        returns: int - the ID of the last row inserted
        """
        self.cursor.execute(insert_statement, params)
        return self.cursor.lastrowid  # Return the ID of the last row inserted
    
    def update(self, update_statement: str, params: Tuple = ()) :
        """
        Update a record into the database and return its ID.

        params:
            update_statement: str - the UPDATE statement to execute
            params: Tuple - the parameters to pass to the query

        returns: int - the ID of the last row inserted
        """
        self.cursor.execute(update_statement, params)
       
      
    def delete(self, delete_statement: str, params: Tuple = ()) -> int:
        """
        Detes a record from the database.

        params:
            delete_statement: str - the DELETE statement to execute
            params: Tuple - the parameters to pass to the query

        """
        self.cursor.execute(delete_statement, params)
        return self.cursor.rowcount  # Return the number of rows that were deleted
    
    def insert_without_id(self, insert_statement: str, params: Tuple = ()) -> None:
        """
        Insert a new record into the database without returning its ID.

        params:
            insert_statement: str - the INSERT statement to execute
            params: Tuple - the parameters to pass to the query

        returns: None
        """
        self.cursor.execute(insert_statement, params)

    def insert_many(self, table_name: str, records: List) -> None:
        """
        Insert multiple records into the database.

        params:
            table_name: str - the name of the table to insert the records into
            records: List - a list of dictionaries, where each dictionary represents a record to insert

        returns: None
        """
        # Define columns based on the keys of the first dictionary in the data list
        columns = list(records[0].keys())
        placeholders = ', '.join(['?'] * len(columns))
        columns_string = ', '.join(columns)

        sql = f"INSERT INTO {table_name} ({columns_string}) VALUES ({placeholders});"

        # Prepare the list of tuples for the insert statement
        records_to_insert = [tuple(d[col] for col in columns) for d in records]

        # Execute the batch insert
        self.cursor.executemany(sql, records_to_insert)

    @contextmanager
    def connection(self):
        """Provide a transactional scope around a series of operations."""
        try:
            self.open()
            yield self
        finally:
            self.close()

    @contextmanager
    def transaction(self):
        with self.connection() as conn:
            conn.begin_transaction()
            yield conn
            conn.commit()

    @contextmanager
    def lock(self):
        mutex(self.db_file_path).acquire()
        yield
        mutex(self.db_file_path).release()
