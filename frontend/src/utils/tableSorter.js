/** 
 * Table sorting utility for HTML tables in search results
 */
export function initializeTableSorting() {
  // Find all tables that should be sortable
  const tables = document.querySelectorAll('.chunk-text table, .message-content table, .explorer table');
  // console.log(`Found ${tables.length} tables to check for sorting.`);
  
  tables.forEach(table => {
    // Check if the table has multiple rows with <th> elements
    const rows = table.querySelectorAll('tr');

    if (rows.length <= 2) { // if the table has only 2 rows, it's a header row and a data row, so skip it
      if (rows.length == 1) {
        // remove background color property from all th and td elements:
        table.querySelectorAll('th').forEach(element => {
          element.classList.add('transparent-bg');
        });
      }
      return;
    }

    let headerRowCount = 0;
    rows.forEach(row => {
      if (row.querySelectorAll('th').length > 0) {
        headerRowCount++;
      }
    });
    
    // console.log(`Table has ${headerRowCount} header rows.`);
    if (headerRowCount === 1) {
      makeTableSortable(table);
    } 
  });
}

/**
 * Array to store event listeners for the table sorting
 * @type {Array<{header: HTMLElement, listener: () => void}>}
 */
let eventListeners = [];

/**
 * Function to remove all event listeners
 */
export function removeEventListeners() {
  try {
    eventListeners.forEach(({ header, listener }) => {
      if (header) { // Check if header still exists
        header.removeEventListener('click', listener);
      }
    });
    // Clear the array
    eventListeners = [];
  } 
  catch (error) {
    console.error('Error removing event listeners:', error);
  }
}

/**
 * Make the table sortable
 * 
 * @param {HTMLElement} table - The table to make sortable 
 */
function makeTableSortable(table) {
  const headers = table.querySelectorAll('th');
  headers.forEach(header => {
    // Set cursor to pointer to indicate clickability
    header.style.cursor = 'pointer';
    // add class sortable-header to the header
    header.classList.add('sortable-header');
    
    // Check if the sort indicator already exists
    if (!header.querySelector('.sort-indicator')) {
      const sortIndicator = document.createElement('span');
      sortIndicator.className = 'sort-indicator';
      sortIndicator.textContent = '⬍';
      header.appendChild(sortIndicator);
    }
    // Create event listener function
    const listener = () => {
      try {
        sortTable(table, Array.from(headers).indexOf(header), header);
      } 
      catch (error) {
        console.error('Error sorting table:', error);
      }
    };
    // Add event listener for sorting
    header.addEventListener('click', listener);
    // Store the event listener
    eventListeners.push({ header, listener });
  });
}
/**
 * Sort the table by the column index and header
 * 
 * @param {HTMLElement} table - The table to sort
 * @param {number} columnIndex - The index of the column to sort
 * @param {HTMLElement} header - The header of the column to sort
 */
function sortTable(table, columnIndex, header) {
  const tbody = table.querySelector('tbody') || table;
  const rows = Array.from(tbody.querySelectorAll('tr')).filter(row => 
    row.querySelectorAll('td').length > 0 // Only data rows, not header rows
  );
  
  if (rows.length === 0) return;
  
  // Determine current sort direction
  const isAscending = header.classList.toggle('sort-asc');
  header.classList.toggle('sort-desc', !isAscending);
  // console.log(`Sorting column ${columnIndex} in ${isAscending ? 'ascending' : 'descending'} order`);
  
  // Clear all sort indicators
  table.querySelectorAll('th').forEach(th => {
    if (th !== header) {
      th.classList.remove('sort-asc', 'sort-desc');
      const indicator = th.querySelector('.sort-indicator');
      if (indicator) {
        indicator.innerHTML = '⬍';
        indicator.style.opacity = '0.5';
      }
    }
  });
  
  // Set current header sort direction
  const currentIndicator = header.querySelector('.sort-indicator');
  if (currentIndicator) {
    currentIndicator.innerHTML = isAscending ? '↑' : '↓';
    currentIndicator.style.opacity = '1';
  }
  
  // Sort rows
  rows.sort((a, b) => {
    const aCell = a.cells[columnIndex];
    const bCell = b.cells[columnIndex];
    
    if (!aCell || !bCell) return 0;
    
    let aValue = aCell.textContent.trim();
    let bValue = bCell.textContent.trim();
    
    // Try to parse as numbers
    const aNum = parseFloat(aValue);
    const bNum = parseFloat(bValue);
    
    let comparison = 0;
    
    if (!isNaN(aNum) && !isNaN(bNum)) {
      // Numeric comparison
      comparison = aNum - bNum;
    } else {
      // String comparison
      comparison = aValue.localeCompare(bValue, undefined, { 
        numeric: true, 
        sensitivity: 'base' 
      });
    }
    
    return isAscending ? comparison : -comparison;
  });
  
  // Re-append sorted rows
  rows.forEach(row => tbody.appendChild(row));
}