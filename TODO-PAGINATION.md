# COA Pagination Fix - No Overlaps with Signatures/Footer

## Steps:

**1. [ ] Create this TODO (Done)**

**2. [ ] Replace static/js/coa_paginate.js with improved version**
   - Fixed height calculations (42mm header + 180px footer reserve)
   - Stricter table splitting with 25px safety gap  
   - Better overflow detection
   - Console debug logs

**3. [ ] Update static/css/coa.css**
   - Print-specific max-heights
   - Increased footer padding

**4. [ ] Test**
   ```
   # Find report with long results
   python manage.py shell
   >>> Report.objects.filter(ceo_content__icontains='table').first()
   
   # Print ?autoprint=1
   /reports/[ID]/coa/print/?autoprint=1
   ```
   - ✅ Results split before signature line
   - ✅ Page 2+ has header but no meta-table overlap  
   - ✅ Barcode/signatures visible, no content behind

**5. [ ] Compare PDF download vs sample**
   ```
   Click PDF download button → matches /home/nd/Downloads/ARLPL_COA_210326-025.pdf layout
   ```

**Next:** Edit coa_paginate.js
