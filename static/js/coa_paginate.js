(function () {
  "use strict";

  function isBlankTextNode(node) {
    return node.nodeType === Node.TEXT_NODE && !node.textContent.trim();
  }

  function collectNodes(container) {
    return Array.from(container.childNodes).filter((node) => !isBlankTextNode(node));
  }

  function cloneFixedTableParts(sourceTable, targetTable) {
    Array.from(sourceTable.children).forEach((child) => {
      const tag = child.tagName.toLowerCase();
      if (tag === "caption" || tag === "colgroup" || tag === "thead") {
        targetTable.appendChild(child.cloneNode(true));
      }
    });
  }

  function buildTableSections(table) {
    const sections = [];

    Array.from(table.children).forEach((child) => {
      if (child.tagName && child.tagName.toLowerCase() === "tbody") {
        sections.push({
          source: child,
          rows: Array.from(child.rows),
        });
      }
    });

    if (!sections.length) {
      sections.push({
        source: document.createElement("tbody"),
        rows: Array.from(table.rows).filter((row) => row.parentElement === table),
      });
    }

    return sections;
  }

  function makeSplitTable(sourceTable) {
    const table = sourceTable.cloneNode(false);
    cloneFixedTableParts(sourceTable, table);
    return table;
  }

  function getResultLimit(page, container) {
    const footerBoundary =
      page.querySelector(".coa-signature-line") ||
      page.querySelector(".coa-footer-row") ||
      page.querySelector(".coa-footer-barcode");

    if (!footerBoundary) {
      return container.clientHeight || 0;
    }

    const containerRect = container.getBoundingClientRect();
    const footerRect = footerBoundary.getBoundingClientRect();
    const safeGap = 12;
    return Math.max(0, Math.floor(footerRect.top - containerRect.top - safeGap));
  }

  function applyResultLimit(page, container) {
    const limit = getResultLimit(page, container);
    if (limit > 0) {
      container.style.maxHeight = limit + "px";
      container.style.height = limit + "px";
      container.style.overflow = "hidden";
    }
    return limit;
  }

  function isOverflowing(page, container) {
    const limit = getResultLimit(page, container);
    return container.scrollHeight > limit + 1;
  }

  function tryAppendSimpleNode(page, container, node) {
    const clone = node.cloneNode(true);
    container.appendChild(clone);

    if (!isOverflowing(page, container)) {
      return { type: "fit" };
    }

    container.removeChild(clone);
    return { type: "nofit" };
  }

  function tryAppendTable(page, container, sourceTable) {
    const fullClone = sourceTable.cloneNode(true);
    container.appendChild(fullClone);

    if (!isOverflowing(page, container)) {
      return { type: "fit" };
    }

    container.removeChild(fullClone);

    const workingTable = makeSplitTable(sourceTable);
    const remainderTable = makeSplitTable(sourceTable);
    const sections = buildTableSections(sourceTable);
    const workingSections = [];
    const remainderSections = [];

    sections.forEach((section) => {
      const workingSection = section.source.cloneNode(false);
      const remainderSection = section.source.cloneNode(false);
      workingTable.appendChild(workingSection);
      remainderTable.appendChild(remainderSection);
      workingSections.push(workingSection);
      remainderSections.push(remainderSection);
    });

    container.appendChild(workingTable);

    let fittedAnyRow = false;

    sections.forEach((section, sectionIndex) => {
      section.rows.forEach((row, rowIndex) => {
        const rowClone = row.cloneNode(true);
        workingSections[sectionIndex].appendChild(rowClone);

        if (isOverflowing(page, container)) {
          workingSections[sectionIndex].removeChild(rowClone);

          if (!fittedAnyRow) {
            workingSections[sectionIndex].appendChild(rowClone);
            fittedAnyRow = true;
          } else {
            remainderSections[sectionIndex].appendChild(row.cloneNode(true));
          }

          section.rows.slice(rowIndex + 1).forEach((remainingRow) => {
            remainderSections[sectionIndex].appendChild(remainingRow.cloneNode(true));
          });

          for (let nextSectionIndex = sectionIndex + 1; nextSectionIndex < sections.length; nextSectionIndex += 1) {
            sections[nextSectionIndex].rows.forEach((remainingRow) => {
              remainderSections[nextSectionIndex].appendChild(remainingRow.cloneNode(true));
            });
          }

          throw new Error("__COA_TABLE_SPLIT__");
        }

        fittedAnyRow = true;
      });
    });

    container.removeChild(workingTable);
    return { type: "fit" };
  }

  function splitTableNode(page, container, sourceTable) {
    try {
      const fitResult = tryAppendTable(page, container, sourceTable);
      if (fitResult.type === "fit") {
        return fitResult;
      }
    } catch (error) {
      if (error.message !== "__COA_TABLE_SPLIT__") {
        throw error;
      }
    }

    const appendedTable = container.lastElementChild;
    if (!appendedTable || appendedTable.tagName.toLowerCase() !== "table") {
      return { type: "nofit" };
    }

    const remainderTable = makeSplitTable(sourceTable);
    let hasRemainderRows = false;
    const sourceSections = buildTableSections(sourceTable);
    const appendedSections = buildTableSections(appendedTable);

    sourceSections.forEach((section, sectionIndex) => {
      const usedRows = appendedSections[sectionIndex] ? appendedSections[sectionIndex].rows.length : 0;
      const remainingRows = section.rows.slice(usedRows);
      const remainderSection = section.source.cloneNode(false);

      remainingRows.forEach((row) => {
        remainderSection.appendChild(row.cloneNode(true));
        hasRemainderRows = true;
      });

      if (remainingRows.length) {
        remainderTable.appendChild(remainderSection);
      }
    });

    if (!hasRemainderRows) {
      return { type: "fit" };
    }

    return { type: "split", remainder: remainderTable };
  }

  function appendNodeToPage(page, container, node) {
    if (node.nodeType === Node.ELEMENT_NODE && node.tagName.toLowerCase() === "table") {
      return splitTableNode(page, container, node);
    }

    return tryAppendSimpleNode(page, container, node);
  }

  function createPage(prototype, pageNumber) {
    const page = prototype.firstElementChild.cloneNode(true);
    const pageNumberTarget = page.querySelector(".coa-page-number");
    if (pageNumberTarget) {
      pageNumberTarget.textContent = String(pageNumber);
    }
    return {
      page,
      result: page.querySelector(".coa-page-result"),
    };
  }

  function hasVisibleContent(container) {
    return collectNodes(container).some((node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        return !!node.textContent.trim();
      }
      return true;
    });
  }

  function renderQRCodes(root) {
    root.querySelectorAll(".coa-qr-code").forEach((target) => {
      const payload = target.dataset.qrPayload;
      if (!payload || !window.QRCode) {
        return;
      }

      target.innerHTML = "";
      new window.QRCode(target, {
        text: payload,
        width: 90,
        height: 90,
      });
    });
  }

  function paginate() {
    const prototype = document.getElementById("coa-page-prototype");
    const source = document.getElementById("coa-result-source");
    const tail = document.getElementById("coa-tail-source");
    const renderedPages = document.getElementById("coa-rendered-pages");
    const measureRoot = document.getElementById("coa-measure-root");

    if (!prototype || !source || !tail || !renderedPages || !measureRoot) {
      document.dispatchEvent(new CustomEvent("coa:ready"));
      return;
    }

    const pendingNodes = collectNodes(source).concat(collectNodes(tail));

    if (!pendingNodes.length) {
      pendingNodes.push(document.createElement("p"));
    }

    renderedPages.innerHTML = "";
    measureRoot.innerHTML = "";

    const pages = [];
    let pageNumber = 1;

    while (pendingNodes.length) {
      const pageParts = createPage(prototype, pageNumber);
      const page = pageParts.page;
      const resultContainer = pageParts.result;
      let appendedAnything = false;

      measureRoot.appendChild(page);
      applyResultLimit(page, resultContainer);

      while (pendingNodes.length) {
        const candidate = pendingNodes[0];
        const appendResult = appendNodeToPage(page, resultContainer, candidate);

        if (appendResult.type === "fit") {
          pendingNodes.shift();
          appendedAnything = true;
          continue;
        }

        if (appendResult.type === "split") {
          pendingNodes[0] = appendResult.remainder;
          appendedAnything = true;
          break;
        }

        if (!appendedAnything) {
          const forcedClone = candidate.cloneNode(true);
          resultContainer.appendChild(forcedClone);
          if (isOverflowing(page, resultContainer)) {
            resultContainer.removeChild(forcedClone);
          } else {
            pendingNodes.shift();
            appendedAnything = true;
          }
        }
        break;
      }

      if (hasVisibleContent(resultContainer)) {
        pages.push(page);
      } else {
        measureRoot.removeChild(page);
        break;
      }
      pageNumber += 1;
    }

    pages.forEach((page) => {
      renderedPages.appendChild(page);
    });

    measureRoot.innerHTML = "";
    renderQRCodes(renderedPages);
    document.dispatchEvent(new CustomEvent("coa:ready"));
  }

  document.addEventListener("DOMContentLoaded", paginate);
})();
