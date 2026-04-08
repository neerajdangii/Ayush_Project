# Unified COA Fixes TODO Tracker

## Status Overview
- [x] COA Print Infinite Loop Fix
- [x] Result Table Splitting Fix
- [x] Pagination Improvements

## 1. COA Print / Autoprint
**Implemented**
- `templates/reports/coa_print.html` waits for `coa:ready` before calling `window.print()`
- URL cleanup with `autoprint` removal remains in place
- `window.load` fallback still exists to avoid stuck preview state

**Manual verify**
```
Navigate to /reports/<ID>/coa/print/?autoprint=1
- Prints once only
- URL is cleaned
- No repeated print loop
```

## 2. Result Table Splitting
**Implemented**
- `static/js/coa_paginate.js`
  - row groups are preserved using `rowSpan`
  - split tables continue cleanly across pages
  - continuation notes are added before/after split tables
  - continuation pages rename the heading to `Result of Analysis (Continued)`

- `static/css/coa.css`
  - print-safe table rules kept in place
  - continuation note styling added

## 3. Pagination Improvements
**Implemented**
- paginator runs after layout settles via queued `requestAnimationFrame`
- paginator retries after `window.load` if needed
- `coa:ready` event is dispatched after pagination success or fallback
- tail content still moves backward when space permits

## Testing Command
```bash
python manage.py shell
from reports.models import Report
long_report = Report.objects.filter(ceo_content__icontains='table').first()
print(f'ID: {long_report.pk}')
```

Visit:
`/reports/{ID}/coa/print/?autoprint=1`

## Final Manual Check
- [ ] long result table continues without broken grouped rows
- [ ] page 1 shows `Result continued on next page` when split happens
- [ ] next page shows `Result of Analysis (Continued)`
- [ ] next page shows `Result continued from previous page`
- [ ] END OF REPORT / remark placement stays correct
- [ ] autoprint triggers once after pagination is ready
