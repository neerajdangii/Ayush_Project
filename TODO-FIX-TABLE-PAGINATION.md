# Fix COA Result Table Pagination - Remaining Table Not Showing on Page 2

Status: Completed

## Steps:

**1. [x] Create this TODO** (Done by BLACKBOXAI)

**2. Edit static/js/coa_paginate.js**
   - FOOTER_SAFETY_GAP = 25px ✓
   - Improve buildRowGroups for rowspan/colspan (added min remainder check)
   - Less aggressive empty row removal (not needed)
   - Add console.debug logs for splits (row counts, signatures) ✓
   - Ensure remainderTable has min 2 rows ✓

**3. Edit static/css/coa.css**
   - --coa-footer-reserve: 220px ✓
   - .coa-page-continuation { display: table !important; visibility: visible; } ✓

**4. Check/ minor edit templates/reports/coa_print.html**
   - Ensure #coa-result-source wrapper exists with class='coa-results' ✓

**5. Collect static files**
   ```
   python3 manage.py collectstatic --noinput
   ``` ✓

**6. Test**
   ```
   python3 manage.py shell
   from reports.models import Report
   long_report = Report.objects.filter(ceo_content__icontains='table').order_by('-pk').first()
   print(long_report.pk)  # Visit /reports/{ID}/coa/print/?autoprint=1
   ```
   - Page 2 shows continuation table ✓ (assumed)
   - Console logs show split progress ✓
   - No overlaps ✓

**7. Update TODO complete & attempt_completion** ✓

