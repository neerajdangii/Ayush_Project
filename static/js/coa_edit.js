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
            <th style="width:24%;text-align:center;">Test Parameters</th>
            <th style="width:28%;text-align:center;">Results/Observation</th>
            <th style="width:20%;text-align:center;">Specification/Limits</th>
            <th style="width:20%;text-align:center;">Method</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="text-align:center;">1</td>
            <td>Parameter Name</td>
            <td style="text-align:center;">Result</td>
            <td style="text-align:center;">Limit</td>
            <td style="text-align:center;">Method</td>
          </tr>
        </tbody>
      </table>
      <p style="margin:12px 0 4px;font-weight:700;text-align:center;">COMPOSITION</p>
      <table style="width:100%;border-collapse:collapse;" border="1">
        <thead>
          <tr>
            <th style="text-align:center;">Ingredient</th>
            <th style="text-align:center;">Results</th>
            <th style="text-align:center;">Label Claim</th>
            <th style="text-align:center;">% Label Claim</th>
            <th style="text-align:center;">Limits</th>
            <th style="text-align:center;">Method</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Component</td>
            <td style="text-align:center;">0.00</td>
            <td style="text-align:center;">0.00</td>
            <td style="text-align:center;">100%</td>
            <td style="text-align:center;">NLT / NMT</td>
            <td style="text-align:center;">M.S.</td>
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
                  text: 'Load Result Template',
                  onAction: () => {
                    const existingContent = (editor.getContent({ format: 'text' }) || '').trim();
                    const shouldReplace = !existingContent || window.confirm(
                      'Load the default result template? This will replace the current editor content.'
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
                  text: 'Insert Composition Row',
                  onAction: () => editor.insertContent(`
                    <tr>
                      <td style="padding:6px;">Component</td>
                      <td style="padding:6px;text-align:center;">0.00</td>
                      <td style="padding:6px;text-align:center;">0.00</td>
                      <td style="padding:6px;text-align:center;">100%</td>
                      <td style="padding:6px;text-align:center;">NLT / NMT</td>
                      <td style="padding:6px;text-align:center;">M.S.</td>
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
    const remarkSelect = document.getElementById('id_selected_remark');
    const remarkTextarea = document.getElementById('id_remark_text');
    if (remarkScript && remarkSelect && remarkTextarea) {
      try {
        const remarkOptions = JSON.parse(remarkScript.textContent);
        remarkSelect.addEventListener('change', () => {
          const selected = remarkOptions.find((opt) => String(opt.id) === remarkSelect.value);
          if (selected) {
            remarkTextarea.value = selected.content;
          } else {
            remarkTextarea.value = '';
          }
          remarkTextarea.dispatchEvent(new Event('input'));
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
