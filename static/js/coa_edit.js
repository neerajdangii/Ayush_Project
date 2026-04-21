(function(){
  'use strict';

  document.addEventListener('DOMContentLoaded', function(){
    const savePopup = document.querySelector('.coa-save-popup');
    if (savePopup) {
      setTimeout(() => {
        savePopup.classList.add('is-hidden');
      }, 3500);
    }

    const targets = document.querySelectorAll('textarea[data-editor="tinymce"]');

    if (targets.length && window.tinymce) {
      const defaultResultTable = `
      <table style="width:100%;border-collapse:collapse;" border="1">
        <thead>
          <tr>
            <th style="width:8%;text-align:center;">S.No.</th>
            <th style="width:32%;text-align:center;">Test Parameters</th>
            <th style="width:25%;text-align:center;">Results/Observation</th>
            <th style="width:20%;text-align:center;">Specification/Limits</th>
            <th style="width:15%;text-align:center;">Method</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="text-align:center;">1</td>
            <td>Parameter Name</td>
            <td style="text-align:center;">&nbsp;</td>
            <td style="text-align:center;">&nbsp;</td>
            <td style="text-align:center;">&nbsp;</td>
          </tr>
        </tbody>
      </table>
      `;

      const defaultRow = `
        <tr>
          <td style="text-align:center;">#</td>
          <td>New Parameter</td>
          <td style="text-align:center;">Result</td>
          <td style="text-align:center;">Limit</td>
          <td style="text-align:center;">Method</td>
        </tr>
      `;

      tinymce.init({
        selector: 'textarea[data-editor="tinymce"]',
        height: 520,
        menubar: 'file edit view insert format table tools',
        branding: false,
        plugins: 'lists table link code advlist charmap searchreplace wordcount preview',
        toolbar_sticky: true,
        toolbar: 'undo redo | addTest addParameter | blocks fontfamily fontsize | bold italic underline forecolor backcolor | alignleft aligncenter alignright alignjustify | outdent indent | bullist numlist | table tabledelete | removeformat code preview',
        font_family_formats: 'Helvetica=helvetica,arial,sans-serif;Times New Roman=times new roman,times,serif;Calibri=calibri,sans-serif;Courier New=courier new,courier,monospace',
        content_style: 'body{font-family:Helvetica,Arial,sans-serif;font-size:12pt;line-height:1.35;} table{border-collapse:collapse;} table td, table th{border:1px solid #111;padding:6px;}',
        table_default_attributes: { border: '1', style: 'border-collapse:collapse;width:100%;' },
        table_default_styles: {},
        table_responsive_width: true,
        license_key: 'gpl',
        setup: (editor) => {
          const syncEditorContent = () => {
            editor.save();
          };

          editor.on('change input undo redo setcontent', syncEditorContent);

          editor.ui.registry.addMenuButton('addTest', {
            text: 'Add Test',
            fetch: (callback) => {
              callback([
                {
                  type: 'menuitem',
                  text: 'Load Simple Result Table',
                  onAction: () => {
                    const existingContent = (editor.getContent({ format: 'text' }) || '').trim();
                    const shouldReplace = !existingContent || window.confirm(
                      'Load the simple result table? This will replace the current editor content.'
                    );

                    if (!shouldReplace) {
                      return;
                    }

                    editor.setContent(defaultResultTable);
                    editor.focus();
                  }
                },
                {
                  type: 'menuitem',
                  text: 'Insert Test Row',
                  onAction: () => editor.insertContent(defaultRow)
                }
              ]);
            }
          });
          editor.ui.registry.addMenuButton('addParameter', {
            text: 'Add Parameter',
            fetch: (callback) => {
              callback([
                {
                  type: 'menuitem',
                  text: 'Insert Simple Test Row',
                  onAction: () => editor.insertContent(`
                    <tr>
                      <td style="padding:6px;text-align:center;">#</td>
                      <td style="padding:6px;">New Parameter</td>
                      <td style="padding:6px;text-align:center;">&nbsp;</td>
                      <td style="padding:6px;text-align:center;">&nbsp;</td>
                      <td style="padding:6px;text-align:center;">&nbsp;</td>
                    </tr>
                  `)
                }
              ]);
            }
          });
        }
      });
    }

    const coaForm = document.querySelector('.coa-editor-shell form');
    if (coaForm) {
      coaForm.addEventListener('submit', () => {
        if (window.tinymce) {
          window.tinymce.triggerSave();
        }
      });
    }

    const summarySection = document.getElementById('coa-summary');
    const summaryToggle = document.getElementById('coa-summary-toggle');
    if (summarySection) {
      summarySection.classList.add('is-hidden');
    }
    if (summaryToggle && summarySection) {
      summaryToggle.addEventListener('click', () => {
        const hidden = summarySection.classList.toggle('is-hidden');
        summaryToggle.textContent = hidden ? 'Show Sample Details' : 'Hide Sample Details';
      });
    }

    const remarkScript = document.getElementById('remark-options-data');
    const remarkPicker = document.getElementById('id_remark_picker');
    const remarkPickerWrap = document.getElementById('coaRemarkPicker');
    const remarkDropdown = document.getElementById('coaRemarkDropdown');
    const remarkOptionsList = document.getElementById('coaRemarkOptions');
    const remarkSelect = document.getElementById('id_selected_remarks');
    const remarkTextarea = document.getElementById('id_remark_text');
    const hiddenRemarkSelect = document.getElementById('id_selected_remark');
    if (remarkScript && remarkPicker && remarkPickerWrap && remarkDropdown && remarkOptionsList && remarkSelect && remarkTextarea) {
      try {
        const remarkOptions = JSON.parse(remarkScript.textContent);
        const appendRemarkText = (content) => {
          const nextContent = (content || '').trim();
          if (!nextContent) {
            return;
          }

          const existingText = (remarkTextarea.value || '').trim();
          const blocks = existingText ? existingText.split(/\n{2,}/).map((item) => item.trim()).filter(Boolean) : [];
          if (!blocks.includes(nextContent)) {
            blocks.push(nextContent);
          }
          remarkTextarea.value = blocks.join('\n\n');
          remarkTextarea.dispatchEvent(new Event('input'));
        };

        const normalizeText = (value) => (value || '').trim().toLowerCase();

        const getSelectedRemarkIds = () => Array.from(remarkSelect.selectedOptions).map((option) => String(option.value));

        const openRemarkDropdown = () => {
          remarkDropdown.classList.remove('d-none');
        };

        const closeRemarkDropdown = () => {
          remarkDropdown.classList.add('d-none');
        };

        const renderRemarkOptions = (term) => {
          const normalizedTerm = normalizeText(term);
          const selectedIds = getSelectedRemarkIds();
          const filtered = remarkOptions.filter((item) => {
            const label = normalizeText(item.title || item.content || '');
            return !normalizedTerm || label.includes(normalizedTerm);
          });

          remarkOptionsList.innerHTML = '';

          if (!filtered.length) {
            const emptyState = document.createElement('div');
            emptyState.className = 'coa-remark-picker__empty';
            emptyState.textContent = 'No matching remarks found.';
            remarkOptionsList.appendChild(emptyState);
            return;
          }

          filtered.forEach((item) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'coa-remark-picker__option';
            button.dataset.value = String(item.id);
            button.textContent = (item.content || item.title || '').trim();
            if (selectedIds.includes(String(item.id))) {
              button.classList.add('is-selected');
            }
            remarkOptionsList.appendChild(button);
          });
        };

        const selectRemark = (selectedValue) => {
          const selected = remarkOptions.find((opt) => String(opt.id) === String(selectedValue));
          if (!selected) {
            return;
          }

          const hiddenOption = Array.from(remarkSelect.options).find((option) => String(option.value) === selectedValue);
          if (hiddenOption) {
            hiddenOption.selected = true;
          }

          const selectedValues = Array.from(remarkSelect.selectedOptions).map((option) => String(option.value));
          if (hiddenRemarkSelect) {
            hiddenRemarkSelect.value = selectedValues[0] || selectedValue;
          }

          appendRemarkText(selected.content);
          remarkPicker.value = '';
          renderRemarkOptions('');
          closeRemarkDropdown();
        };

        renderRemarkOptions('');

        remarkPicker.addEventListener('focus', () => {
          renderRemarkOptions(remarkPicker.value);
          openRemarkDropdown();
        });

        remarkPicker.addEventListener('click', () => {
          renderRemarkOptions(remarkPicker.value);
          openRemarkDropdown();
        });

        remarkPicker.addEventListener('input', () => {
          renderRemarkOptions(remarkPicker.value);
          openRemarkDropdown();
        });

        remarkPicker.addEventListener('keydown', (event) => {
          if (event.key === 'Escape') {
            closeRemarkDropdown();
          }
        });

        remarkOptionsList.addEventListener('click', (event) => {
          const optionButton = event.target.closest('.coa-remark-picker__option');
          if (!optionButton) {
            return;
          }
          selectRemark(optionButton.dataset.value);
        });

        document.addEventListener('click', (event) => {
          if (!remarkPickerWrap.contains(event.target)) {
            closeRemarkDropdown();
          }
        });
      } catch (err) {
        console.error('Unable to parse remark list', err);
      }
    }

    const reportTemplateScript = document.getElementById('report-template-options-data');
    const reportTemplateSelect = document.getElementById('id_report_template');
    const applyTemplateButton = document.getElementById('apply-report-template');
    const templateContentUrlNode = document.getElementById('report-template-content-url');
    if (reportTemplateScript && reportTemplateSelect && applyTemplateButton && templateContentUrlNode) {
      try {
        const reportTemplates = JSON.parse(reportTemplateScript.textContent);
        const templateContentUrlPattern = JSON.parse(templateContentUrlNode.textContent || '""');
        applyTemplateButton.addEventListener('click', () => {
          const selected = reportTemplates.find((item) => String(item.id) === reportTemplateSelect.value);
          if (!selected) {
            alert('Please select a template first.');
            return;
          }

          const shouldReplace = window.confirm('Load this template into the result section? This will replace the current editor content.');
          if (!shouldReplace) {
            return;
          }

          applyTemplateButton.disabled = true;
          const requestUrl = templateContentUrlPattern.replace(/0\/$/, `${selected.id}/`);

          fetch(requestUrl, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
          })
            .then((response) => {
              if (!response.ok) {
                throw new Error('Template request failed');
              }
              return response.json();
            })
            .then((payload) => {
              const content = payload.content || '';
              if (window.tinymce) {
                const editor = window.tinymce.get('editor');
                if (editor) {
                  editor.setContent(content);
                  editor.focus();
                  return;
                }
              }

              const textarea = document.getElementById('editor');
              if (textarea) {
                textarea.value = content;
                textarea.dispatchEvent(new Event('input'));
              }
            })
            .catch((err) => {
              console.error('Unable to load selected report template', err);
              alert('Unable to load the selected template.');
            })
            .finally(() => {
              applyTemplateButton.disabled = false;
            });
        });
      } catch (err) {
        console.error('Unable to parse report template list', err);
      }
    }

    const oldReportScript = document.getElementById('old-report-options-data');
    const oldReportSearchInput = document.getElementById('id_old_report_search');
    const oldReportPickerWrap = document.getElementById('coaOldReportPicker');
    const oldReportDropdown = document.getElementById('coaOldReportDropdown');
    const oldReportOptionsList = document.getElementById('coaOldReportOptions');
    const oldReportSelect = document.getElementById('id_old_report_source');
    const applyOldReportButton = document.getElementById('apply-old-report-data');
    const reportApiDetailUrlNode = document.getElementById('report-api-detail-url');
    if (
      oldReportScript &&
      oldReportSearchInput &&
      oldReportPickerWrap &&
      oldReportDropdown &&
      oldReportOptionsList &&
      oldReportSelect &&
      applyOldReportButton &&
      reportApiDetailUrlNode
    ) {
      try {
        const oldReports = JSON.parse(oldReportScript.textContent);
        const reportApiDetailUrlPattern = JSON.parse(reportApiDetailUrlNode.textContent || '""');
        const normalizeText = (value) => (value || '').trim().toLowerCase();

        const buildOldReportLabel = (item) => {
          const sampleName = (item.sample_name || '').trim() || 'Sample';
          const customerName = (item.customer_name || '').trim() || 'Customer';
          const batchNo = (item.batch_no || '').trim() || '-';
          return `${sampleName} | ${customerName} | ${batchNo}`;
        };

        const buildOldReportMeta = (item) => {
          const details = [];
          if (item.updated_at) {
            details.push(item.updated_at);
          }
          return details.join(' | ');
        };

        const openOldReportDropdown = () => {
          oldReportDropdown.classList.remove('d-none');
        };

        const closeOldReportDropdown = () => {
          oldReportDropdown.classList.add('d-none');
        };

        const syncOldReportSearchValue = () => {
          const selected = oldReports.find((item) => String(item.id) === String(oldReportSelect.value));
          oldReportSearchInput.value = selected ? (selected.sample_name || '').trim() : '';
        };

        const renderOldReportOptions = (term) => {
          const normalizedTerm = normalizeText(term);
          const filtered = oldReports.filter((item) => {
            const searchableText = normalizeText([
              item.sample_name,
              item.customer_name,
              item.batch_no,
            ].join(' '));
            return !normalizedTerm || searchableText.includes(normalizedTerm);
          });

          oldReportOptionsList.innerHTML = '';

          if (!filtered.length) {
            const emptyState = document.createElement('div');
            emptyState.className = 'coa-old-report-picker__empty';
            emptyState.textContent = 'No matching previous reports found.';
            oldReportOptionsList.appendChild(emptyState);
            return;
          }

          filtered.forEach((item) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'coa-old-report-picker__option';
            button.dataset.value = String(item.id);
            const title = document.createElement('strong');
            title.textContent = buildOldReportLabel(item);
            button.appendChild(title);

            const meta = buildOldReportMeta(item);
            if (meta) {
              const metaText = document.createElement('span');
              metaText.className = 'coa-old-report-picker__meta';
              metaText.textContent = meta;
              button.appendChild(metaText);
            }
            if (String(oldReportSelect.value) === String(item.id)) {
              button.classList.add('is-selected');
            }
            oldReportOptionsList.appendChild(button);
          });
        };

        const selectOldReport = (selectedValue) => {
          const selected = oldReports.find((item) => String(item.id) === String(selectedValue));
          if (!selected) {
            return null;
          }
          oldReportSelect.value = String(selected.id);
          syncOldReportSearchValue();
          renderOldReportOptions('');
          closeOldReportDropdown();
          return selected;
        };

        const fetchAndApplyOldReport = (selected) => {
          if (!selected) {
            alert('No previous report found for this sample name and company.');
            return;
          }

          const shouldReplace = window.confirm(
            'Load result data from this previous report? This will replace the current editor content.'
          );
          if (!shouldReplace) {
            return;
          }

          applyOldReportButton.disabled = true;
          const requestUrl = reportApiDetailUrlPattern.replace(/0\/$/, `${selected.id}/`);

          fetch(requestUrl, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
          })
            .then((response) => {
              if (!response.ok) {
                throw new Error('Old report request failed');
              }
              return response.json();
            })
            .then((payload) => {
              const content = payload.content || '';
              if (window.tinymce) {
                const editor = window.tinymce.get('editor');
                if (editor) {
                  editor.setContent(content);
                  editor.focus();
                  return;
                }
              }

              const textarea = document.getElementById('editor');
              if (textarea) {
                textarea.value = content;
                textarea.dispatchEvent(new Event('input'));
              }
            })
            .catch((err) => {
              console.error('Unable to load selected old report data', err);
              alert('Unable to load the selected old report data.');
            })
            .finally(() => {
              applyOldReportButton.disabled = false;
            });
        };

        renderOldReportOptions('');
        oldReportSelect.value = '';
        oldReportSearchInput.value = '';

        oldReportSearchInput.addEventListener('focus', () => {
          renderOldReportOptions(oldReportSearchInput.value);
          openOldReportDropdown();
        });

        oldReportSearchInput.addEventListener('click', () => {
          renderOldReportOptions(oldReportSearchInput.value);
          openOldReportDropdown();
        });

        oldReportSearchInput.addEventListener('input', () => {
          oldReportSelect.value = '';
          renderOldReportOptions(oldReportSearchInput.value);
          openOldReportDropdown();
        });

        oldReportSearchInput.addEventListener('keydown', (event) => {
          if (event.key === 'Escape') {
            closeOldReportDropdown();
          } else if (event.key === 'Enter') {
            const firstOption = oldReportOptionsList.querySelector('.coa-old-report-picker__option');
            if (firstOption) {
              event.preventDefault();
              selectOldReport(firstOption.dataset.value);
            }
          }
        });

        oldReportOptionsList.addEventListener('click', (event) => {
          const optionButton = event.target.closest('.coa-old-report-picker__option');
          if (!optionButton) {
            return;
          }
          selectOldReport(optionButton.dataset.value);
        });

        document.addEventListener('click', (event) => {
          if (!oldReportPickerWrap.contains(event.target)) {
            closeOldReportDropdown();
          }
        });

        applyOldReportButton.addEventListener('click', () => {
          const latestMatchingReport = oldReports[0] || null;
          fetchAndApplyOldReport(latestMatchingReport);
        });
      } catch (err) {
        console.error('Unable to parse old report list', err);
      }
    }

    document.querySelectorAll('.copy-tracking').forEach((btn) => {
      btn.addEventListener('click', () => {
        const value = btn.dataset.copy;
        if (!value) return;
        (navigator.clipboard?.writeText(value) || Promise.reject()).then(() => {
          btn.textContent = 'Copied!';
          setTimeout(() => { btn.textContent = 'Copy'; }, 1600);
        }).catch(() => {
          alert('Copy failed. Please copy manually: ' + value);
        });
      });
    });
  });
})();
