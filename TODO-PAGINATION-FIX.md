# COA Pagination Fix - Implementation Notes

## Problem
The report table was not splitting into multiple pages when content overflowed.

## Solution
Integrated `coa_paginate_v2.js` pagination script with the print template.

## Files Modified

### 1. `templates/reports/coa_doc.html`
- Added `{% block content %}` wrapper around the print page content

### 2. `templates/reports/coa_print.html`
- Added pagination infrastructure elements:
  - `#coa-page-prototype` - Template for continuation pages (with simplified header)
  - `#coa-result-source` - Contains content to be paginated
  - `#coa-tail-source` - Contains tail content (END OF REPORT, remarks)
  - `#coa-measure-root` - Hidden measurement container
  - `#coa-rendered-pages` - Container for generated pages
  - `#coa-debug-status` - Debug output
- Included `coa_paginate_v2.js` script
- Added initialization JavaScript to move content from source to first page

### 3. `templates/reports/partials/coa_letterhead.html`
- Added `is_continuation` parameter support
- When `is_continuation=1`, renders simplified header (no full letterhead, just cert number and page number)
- First page now has empty `.coa-page-result` container (populated by JS)

### 4. `static/css/coa.css`
- Added continuation page header styles
- Added page break CSS for continuation pages
- Added print-specific styles for continuation headers

## How It Works

1. Page loads with content in `#coa-result-source`
2. JavaScript moves content to first page's result container
3. `coa_paginate_v2.js` runs:
   - Collects all content items (tables, paragraphs, etc.)
   - For each page, fits as much content as possible
   - Splits tables row-by-row if they don't fit
   - Generates continuation pages with simplified headers
4. Pages are rendered with proper page numbers and footers

## Testing

1. Navigate to a COA report print preview
2. Look for the debug status at bottom-left corner
3. Check if multiple pages are generated
4. Click "Print" to test PDF output

## Debug

The debug status shows pagination messages:
- "v2-fixed loaded" - Script loaded
- "no result content found" - No content to paginate
- "page 1: N items" - Items added to first page
- "overflow at item N" - Overflow detected

## Troubleshooting

If pagination doesn't work:
1. Check browser console for errors
2. Verify `report_ceo_content` is being passed to template
3. Check that CSS variables for page height are defined
4. Verify `preview_mode=True` is set in view
