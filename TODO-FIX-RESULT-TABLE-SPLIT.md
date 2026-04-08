# Fix Result Table Splitting in COA Print - Approved Plan

## Status: [x] Completed

**Plan Summary:**
- Improve table pagination to prevent footer overlap
- Update JS height calcs, CSS reserves, minor template wrapper

## Steps:

**1. [x] Plan approved by user** (Done)

**2. [x] Create this TODO** (Done)

**3. [x] Edit static/js/coa_paginate.js** (Done)

**4. [x] Edit static/css/coa.css** (Done)

**5. [x] Edit templates/reports/coa_print.html** (Skipped - no target div)
   - FOOTER_SAFETY_GAP=40px
   - Dynamic footer height sum (.coa-signature-line + .coa-footer-row + .coa-footer-barcode +50px)
   - Table split: MIN_TABLE_ROWS_PER_PAGE=4, detect small tables → keep together
   - Add coa-keep-together on thead+first rows

**4. [ ] Edit static/css/coa.css**
   - --coa-footer-reserve: 190px
   - .coa-page-main padding/min-height calc
   - Print: table page-break-inside: auto

**5. [ ] Edit templates/reports/coa_print.html** (minor)
   - Add class='coa-results' to #coa-result-source wrapper

**6. [ ] Test**
   ```
   python manage.py shell
   from reports.models import Report
   long_report = Report.objects.filter(ceo_content__icontains='table').order_by('-pk').first()
   # Visit /reports/{long_report.pk}/coa/print/?autoprint=1
   ```
   - Tables split cleanly before signature
   - Multi-page tables: thead repeats, no overlap
   - PDF download: proper layout

**7. [ ] Collect static**
   ```
   python manage.py collectstatic --noinput
   ```

**8. [ ] Mark complete**
   - Update all ✓
   - attempt_completion
