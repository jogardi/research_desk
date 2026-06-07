# Table Sorting Functionality

This module provides table sorting functionality for HTML tables rendered within the Research Desk application. It automatically makes tables sortable by clicking on column headers.

## Features

- **Automatic Detection**: Automatically finds and makes sortable all tables within elements with specific CSS classes
- **Visual Indicators**: Shows sort arrows (↑↓) in table headers to indicate sort direction
- **Smart Sorting**: Handles both numeric and text data appropriately
- **Multiple Tables**: Supports multiple tables on the same page
- **Responsive**: Works with dynamically loaded content

## Target CSS Classes

The table sorting functionality targets tables within elements that have these CSS classes:
- `.chunk-text table` - Tables in search result chunks and context content
- `.message-content table` - Tables in chat messages and AI responses  
- `.explorer table` - Tables in explorer content and reports

## Usage

### Basic Integration

```javascript
import { initializeTableSorting, reinitializeTableSorting } from 'src/utils/tableSorter.js';

// Initialize sorting for all tables on page load
onMounted(() => {
  nextTick(() => {
    setTimeout(() => {
      initializeTableSorting();
    }, 200);
  });
});

// Reinitialize when content changes
watch(() => dataSource, () => {
  nextTick(() => {
    setTimeout(() => {
      reinitializeTableSorting();
    }, 200);
  });
}, { deep: true });
```

### With Markdown Rendering

```javascript
function compiledMarkdown(content) {
  const html = marked(content);
  
  // Initialize table sorting after DOM update
  nextTick(() => {
    setTimeout(() => {
      initializeTableSorting();
    }, 100);
  });
  
  return html;
}
```

## API Reference

### `initializeTableSorting()`
Finds all tables within target CSS classes and makes them sortable. Safe to call multiple times.

### `reinitializeTableSorting()`
Removes existing sorting functionality and reinitializes it. Use when content is dynamically updated.

## Components Integration

The table sorting functionality has been integrated into these components:

### Chat Components
- **Chat.vue**: Sorts tables in AI chat responses
- **Report.vue**: Sorts tables in generated reports
- **ExplorerReportDlg.vue**: Sorts tables in explorer report dialogs

### Explorer Components  
- **Explorer.vue**: Sorts tables in explorer content (summary, insights, concepts, questions)

### Context Builder Components
- **ContextPanel.vue**: Sorts tables in context content chunks
- **SemanticSearchPanel.vue**: Sorts tables in semantic search results
- **TextSearchPanel.vue**: Sorts tables in text search results
- **StashPanel.vue**: Sorts tables in stashed content

### Other Components
- Document excerpt views: sorts tables in selected source text

## Styling

The table sorting styles are defined in `src/css/app.css`:

```css
.sortable-header {
  cursor: pointer !important;
  user-select: none !important;
  position: relative !important;
  transition: background-color 0.2s ease;
}

.sortable-header:hover {
  background-color: rgba(255, 255, 255, 0.1) !important;
}

.sortable-header.sort-asc,
.sortable-header.sort-desc {
  background-color: rgba(0, 123, 255, 0.1) !important;
}

.sort-indicator {
  opacity: 0.5;
  margin-left: 5px;
  font-size: 0.8em;
}

.sortable-header.sort-asc .sort-indicator,
.sortable-header.sort-desc .sort-indicator {
  opacity: 1;
  color: #007bff;
}
```

## How It Works

1. **Detection**: Scans for tables within elements with target CSS classes
2. **Header Enhancement**: Adds click handlers and sort indicators to table headers
3. **Sorting Logic**: 
   - Detects numeric vs text data automatically
   - Uses `parseFloat()` for numeric comparison
   - Uses `localeCompare()` with numeric option for text comparison
4. **Visual Feedback**: Updates sort indicators (↑↓) and header background colors
5. **DOM Manipulation**: Reorders table rows based on sort criteria

## Browser Compatibility

- Modern browsers with ES6+ support
- Uses `Array.from()`, `localeCompare()`, and arrow functions
- Requires DOM manipulation capabilities

## Performance Considerations

- Uses timeouts to ensure DOM is ready before initialization
- Efficient row sorting using native array methods
- Minimal DOM queries by caching elements
- Safe to call multiple times without performance impact

## Files

### `src/utils/tableSorter.js`
Main utility file containing the table sorting logic.

#### Functions:
- `initializeTableSorting()` - Finds and initializes sorting for all supported tables
- `makeTableSortable(table)` - Adds sorting functionality to a specific table
- `sortTable(table, columnIndex, header)` - Sorts table rows by the specified column
- `reinitializeTableSorting()` - Removes existing sorting and reinitializes (for dynamic content)

## Integration

The table sorting functionality is integrated into the following components:

### Search Components
- `src/components/context-builder/TextSearchPanel.vue`
- `src/components/context-builder/SemanticSearchPanel.vue`

### Report Components
- `src/components/Report.vue`
- `src/components/ExplorerReportDlg.vue`

### Chat Components
- `src/pages/Chat.vue`

### Explorer Components
- `src/pages/Explorer.vue`

## CSS Styling

Table sorting styles are defined in both theme files:
- `src/css/dark-theme.scss`
- `src/css/light-theme.scss`

### Key CSS Classes:
- `.sortable-header` - Applied to clickable headers
- `.sort-asc` - Applied to headers sorted in ascending order
- `.sort-desc` - Applied to headers sorted in descending order
- `.sort-indicator` - Visual indicator showing sort direction

## Usage

### Automatic Initialization
The sorting functionality is automatically initialized when:
- Components are mounted
- Search results are updated
- Content is dynamically loaded

### Manual Initialization
```javascript
import { initializeTableSorting } from 'src/utils/tableSorter.js';

// Initialize sorting for all supported tables
initializeTableSorting();
```

### Reinitializing After Content Changes
```javascript
import { reinitializeTableSorting } from 'src/utils/tableSorter.js';

// Remove existing sorting and reinitialize
reinitializeTableSorting();
```

## Features

### Sorting Logic
- **Numeric data**: Automatically detected and sorted numerically
- **Text data**: Sorted alphabetically with natural sorting (e.g., "item10" comes after "item2")
- **Mixed data**: Uses intelligent comparison based on data type

### Visual Indicators
- **Default state**: ↕️ (bidirectional arrow, 50% opacity)
- **Ascending**: ↑ (up arrow, full opacity)
- **Descending**: ↓ (down arrow, full opacity)

### User Interaction
- **First click**: Sort ascending
- **Second click**: Sort descending
- **Header hover**: Background color change
- **Active sort**: Different background color

### Empty Cells
- Empty headers are skipped (not made sortable)
- Empty cells are handled gracefully in sorting

## Browser Compatibility

The implementation uses modern JavaScript features:
- `Array.from()`
- `querySelectorAll()`
- `classList` API
- `localeCompare()` with options

These are supported in all modern browsers (IE11+).

## Performance

- Sorting is performed client-side for fast interaction
- Event listeners are efficiently managed
- DOM manipulation is minimized during sorting
- No external dependencies required

## Troubleshooting

### Tables Not Sortable
1. Check if table has correct CSS class (`.chunk-text`, `.message-content`, or `.explorer`)
2. Ensure `initializeTableSorting()` is called after content is rendered
3. Verify table structure has proper `<th>` elements

### Sort Not Working
1. Check browser console for JavaScript errors
2. Ensure table has data rows with `<td>` elements
3. Verify headers have text content (empty headers are skipped)

### Performance Issues
1. Large tables (>1000 rows) may have slower sort performance
2. Consider implementing virtual scrolling for very large datasets
3. Use `reinitializeTableSorting()` sparingly as it recreates all event listeners

## Future Enhancements

Possible improvements for future versions:
- Multi-column sorting
- Custom sort functions for specific data types
- Sort persistence across page reloads
- Export sorted data functionality
- Keyboard navigation support 
