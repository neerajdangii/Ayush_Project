(function () {
  "use strict";

  var FOOTER_SAFETY_GAP = 24;
  var MAX_PAGES = 120;
  var MAX_ITERATIONS = 2000;
  var BLOCK_TAGS = {
    p: true,
    ul: true,
    ol: true,
    li: true,
    h1: true,
    h2: true,
    h3: true,
    h4: true,
    h5: true,
    h6: true,
    blockquote: true,
    pre: true,
    hr: true
  };
  var TABLE_FRAGMENT_TAGS = {
    caption: true,
    colgroup: true,
    col: true,
    thead: true,
    tbody: true,
    tfoot: true,
    tr: true,
    th: true,
    td: true
  };

  var VAR_PAGE_HEIGHT = "--coa-page-height";
  var VAR_LETTERHEAD_TOP = "--coa-letterhead-top";
  var VAR_PLAIN_TOP = "--coa-plain-top";
  var VAR_PAGE_PADDING_BOTTOM = "--coa-page-padding-bottom";
  var VAR_FOOTER_RESERVE = "--coa-footer-reserve";

  function setDebugStatus(message) {
    var debugNode = document.getElementById("coa-debug-status");
    if (debugNode) {
      debugNode.textContent = "COA debug: " + message;
    }
  }

  function nonBlankNodes(container) {
    return Array.from(container.childNodes).filter(function (node) {
      return !(node.nodeType === Node.TEXT_NODE && !node.textContent.trim());
    });
  }

  function isElement(node, tagName) {
    return node && node.nodeType === Node.ELEMENT_NODE && node.tagName.toLowerCase() === tagName;
  }

  function isPageBreak(node) {
    return !!(
      node &&
      node.nodeType === Node.ELEMENT_NODE &&
      node.classList &&
      (node.classList.contains("coa-page-break") || node.classList.contains("coa-force-break"))
    );
  }

  function isTableFragmentElement(node) {
    return !!(
      node &&
      node.nodeType === Node.ELEMENT_NODE &&
      TABLE_FRAGMENT_TAGS[node.tagName.toLowerCase()]
    );
  }

  function isTailBlock(node) {
    return !!(
      node &&
      node.nodeType === Node.ELEMENT_NODE &&
      node.classList &&
      node.classList.contains("coa-tail-block")
    );
  }

  function tableRowCount(table) {
    if (!table || !table.querySelectorAll) return 0;

    var bodyRows = table.querySelectorAll("tbody > tr");
    if (bodyRows.length) return bodyRows.length;

    return Array.from(table.rows || []).filter(function (row) {
      return row.parentElement === table;
    }).length;
  }

  function pruneEmptyTableSections(table) {
    if (!table) return;

    Array.from(table.querySelectorAll("tbody, tfoot")).forEach(function (section) {
      if (!(section.rows && section.rows.length)) {
        section.parentNode.removeChild(section);
      }
    });
  }

  function parseCssLengthToPixels(cssVar, defaultValue) {
    var root = document.documentElement;
    var value = getComputedStyle(root).getPropertyValue(cssVar).trim();

    if (!value) return defaultValue;

    var temp = document.createElement("div");
    temp.style.cssText = [
      "position:absolute",
      "visibility:hidden",
      "pointer-events:none",
      "left:-99999px",
      "top:0",
      "width:1px",
      "height:" + value
    ].join(";");
    document.documentElement.appendChild(temp);
    var pixels = temp.offsetHeight || defaultValue;
    document.documentElement.removeChild(temp);
    return pixels;
  }

  function getResultContainerMaxHeight() {
    var pageHeight = parseCssLengthToPixels(VAR_PAGE_HEIGHT, 297 * 3.7795);
    var letterheadTop = parseCssLengthToPixels(VAR_LETTERHEAD_TOP, 42 * 3.7795);
    var plainTop = parseCssLengthToPixels(VAR_PLAIN_TOP, 42 * 3.7795);
    var paddingBottom = parseCssLengthToPixels(VAR_PAGE_PADDING_BOTTOM, 12 * 3.7795);
    var footerReserve = parseCssLengthToPixels(VAR_FOOTER_RESERVE, 190);

    var topOffset = Math.max(letterheadTop, plainTop);
    var available = pageHeight - topOffset - paddingBottom - footerReserve - FOOTER_SAFETY_GAP;

    return Math.max(200, available);
  }

  function cloneFixedTableParts(sourceTable, targetTable) {
    Array.from(sourceTable.children).forEach(function (child) {
      if (!child.tagName) return;
      var tag = child.tagName.toLowerCase();
      if (tag === "caption" || tag === "colgroup" || tag === "thead") {
        targetTable.appendChild(child.cloneNode(true));
      }
    });
  }

  function createSplitTable(sourceTable) {
    var table = sourceTable.cloneNode(false);
    cloneFixedTableParts(sourceTable, table);
    return table;
  }

  function buildTableSections(table) {
    var sections = [];
    Array.from(table.children).forEach(function (child) {
      if (child.tagName && child.tagName.toLowerCase() === "tbody") {
        sections.push({ source: child, rows: Array.from(child.rows) });
      }
    });
    if (!sections.length) {
      sections.push({
        source: document.createElement("tbody"),
        rows: Array.from(table.rows).filter(function (row) {
          return row.parentElement === table;
        })
      });
    }
    return sections;
  }

  function buildRowGroups(rows) {
    var groups = [];
    var index = 0;
    while (index < rows.length) {
      var row = rows[index];
      var span = 1;
      Array.from(row.cells || []).forEach(function (cell) {
        span = Math.max(span, cell.rowSpan || 1);
      });
      groups.push(rows.slice(index, Math.min(index + span, rows.length)));
      index += span;
    }
    return groups;
  }

  function createPage(prototype) {
    var page = prototype.firstElementChild.cloneNode(true);
    return {
      page: page,
      result: page.querySelector(".coa-page-result")
    };
  }

  function getResultLimit(page, container) {
    var calculatedLimit = getResultContainerMaxHeight();
    var footerBoundary =
      page.querySelector(".coa-page-footer") ||
      page.querySelector(".coa-signature-line") ||
      page.querySelector(".coa-footer-row") ||
      page.querySelector(".coa-footer-barcode");
    var measuredLimit = 0;
    var containerLimit = Math.floor(container.clientHeight || 0);

    if (footerBoundary) {
      var containerRect = container.getBoundingClientRect();
      var footerRect = footerBoundary.getBoundingClientRect();
      measuredLimit = Math.floor(footerRect.top - containerRect.top - FOOTER_SAFETY_GAP);
    }

    if (calculatedLimit > 0 && measuredLimit > 0) {
      return Math.max(0, Math.min(calculatedLimit, measuredLimit, containerLimit || measuredLimit));
    }

    if (measuredLimit > 0) {
      return Math.max(0, Math.min(containerLimit || measuredLimit, measuredLimit));
    }

    if (calculatedLimit > 0) {
      return Math.max(0, Math.min(containerLimit || calculatedLimit, calculatedLimit));
    }

    return containerLimit || 0;
  }

  function applyResultLimit(page, container) {
    var limit = getResultLimit(page, container);
    if (limit > 0) {
      container.style.maxHeight = limit + "px";
      container.style.height = limit + "px";
      container.style.overflow = "hidden";
    }
  }

  function getContentHeight(container) {
    if (!container) return 0;

    var maxHeight = Math.max(
      container.scrollHeight || 0,
      container.offsetHeight || 0,
      container.clientHeight || 0
    );
    var lastChild = container.lastElementChild;

    if (lastChild) {
      var containerRect = container.getBoundingClientRect();
      var childRect = lastChild.getBoundingClientRect();
      maxHeight = Math.max(
        maxHeight,
        Math.ceil(childRect.bottom - containerRect.top),
        lastChild.scrollHeight || 0,
        lastChild.offsetHeight || 0
      );
    }

    return maxHeight;
  }

  function isOverflowing(page, container) {
    return getContentHeight(container) > getResultLimit(page, container) + 1;
  }

  function createSyntheticTable(nodes) {
    var table = document.createElement("table");
    var tbody = null;

    nodes.forEach(function (node) {
      var tagName;
      var row;

      if (!isTableFragmentElement(node)) return;

      tagName = node.tagName.toLowerCase();

      if (tagName === "td" || tagName === "th") {
        if (!tbody) {
          tbody = document.createElement("tbody");
          table.appendChild(tbody);
        }
        row = document.createElement("tr");
        row.appendChild(node.cloneNode(true));
        tbody.appendChild(row);
        return;
      }

      if (tagName === "tr") {
        if (!tbody) {
          tbody = document.createElement("tbody");
          table.appendChild(tbody);
        }
        tbody.appendChild(node.cloneNode(true));
        return;
      }

      table.appendChild(node.cloneNode(true));
    });

    return table;
  }

  function collectPageItems(source, tail) {
    var items = [];

    function normalize(node) {
      var tagName;
      var textNodeWrapper;
      var children;

      if (node.nodeType === Node.TEXT_NODE) {
        if (node.textContent.trim()) {
          textNodeWrapper = document.createElement("p");
          textNodeWrapper.textContent = node.textContent.trim();
          items.push(textNodeWrapper);
        }
        return;
      }

      if (isPageBreak(node) || isElement(node, "table")) {
        items.push(node.cloneNode(true));
        return;
      }

      if (node.nodeType !== Node.ELEMENT_NODE) return;

      if (isTailBlock(node)) {
        if (node.classList && node.classList.contains("coa-keep-together")) {
          items.push(node.cloneNode(true));
          return;
        }
        nonBlankNodes(node).forEach(normalize);
        return;
      }

      if (node.classList && node.classList.contains("coa-keep-together")) {
        items.push(node.cloneNode(true));
        return;
      }

      tagName = node.tagName.toLowerCase();
      if (BLOCK_TAGS[tagName]) {
        items.push(node.cloneNode(true));
        return;
      }

      if (tagName === "br") return;

      children = nonBlankNodes(node);
      if (children.length && children.every(isTableFragmentElement)) {
        items.push(createSyntheticTable(children));
        return;
      }

      normalizeNodeList(children);
    }

    function normalizeNodeList(nodes) {
      var index = 0;

      while (index < nodes.length) {
        if (isTableFragmentElement(nodes[index])) {
          var fragmentNodes = [];

          while (index < nodes.length && isTableFragmentElement(nodes[index])) {
            fragmentNodes.push(nodes[index]);
            index += 1;
          }

          items.push(createSyntheticTable(fragmentNodes));
          continue;
        }

        normalize(nodes[index]);
        index += 1;
      }
    }

    normalizeNodeList(nonBlankNodes(source));
    normalizeNodeList(nonBlankNodes(tail));
    return items;
  }

  function appendWholeNode(page, container, node) {
    var clone = node.cloneNode(true);
    container.appendChild(clone);

    if (!isOverflowing(page, container)) {
      return { type: "fit" };
    }

    container.removeChild(clone);
    return { type: "nofit" };
  }

  function splitParagraphNode(page, container, node, pageHasContent) {
    var text = (node.textContent || "").replace(/\s+/g, " ").trim();
    var words = text ? text.split(" ") : [];
    var clone = node.cloneNode(false);
    var low = 1;
    var high = words.length;
    var bestFit = 0;

    if (!words.length) return appendWholeNode(page, container, node);

    container.appendChild(clone);

    while (low <= high) {
      var mid = Math.floor((low + high) / 2);
      clone.textContent = words.slice(0, mid).join(" ");

      if (isOverflowing(page, container)) {
        high = mid - 1;
      } else {
        bestFit = mid;
        low = mid + 1;
      }
    }

    if (!bestFit) {
      container.removeChild(clone);
      if (!pageHasContent) {
        container.appendChild(node.cloneNode(true));
        return { type: "fit" };
      }
      return { type: "nofit" };
    }

    clone.textContent = words.slice(0, bestFit).join(" ");

    if (bestFit === words.length) return { type: "fit" };

    var remainder = node.cloneNode(false);
    remainder.textContent = words.slice(bestFit).join(" ");
    return { type: "split", remainder: remainder };
  }

  function splitTableNode(page, container, sourceTable, pageHasContent) {
    var workingTable = createSplitTable(sourceTable);
    var remainderTable = createSplitTable(sourceTable);
    var sections = buildTableSections(sourceTable);
    var workingSections = [];
    var remainderSections = [];
    var fittedRows = 0;
    var stopped = false;

    sections.forEach(function (section) {
      var workingSection = section.source.cloneNode(false);
      var remainderSection = section.source.cloneNode(false);
      workingTable.appendChild(workingSection);
      remainderTable.appendChild(remainderSection);
      workingSections.push(workingSection);
      remainderSections.push(remainderSection);
    });

    container.appendChild(workingTable);

    sections.forEach(function (section, sectionIndex) {
      var rowGroups = buildRowGroups(section.rows);

      if (stopped) {
        section.rows.forEach(function (row) {
          remainderSections[sectionIndex].appendChild(row.cloneNode(true));
        });
        return;
      }

      rowGroups.forEach(function (group, groupIndex) {
        if (stopped) {
          group.forEach(function (row) {
            remainderSections[sectionIndex].appendChild(row.cloneNode(true));
          });
          return;
        }

        var appendedGroupRows = [];

        group.forEach(function (row) {
          var rowClone = row.cloneNode(true);
          workingSections[sectionIndex].appendChild(rowClone);
          appendedGroupRows.push(rowClone);
        });

        if (isOverflowing(page, container)) {
          appendedGroupRows.forEach(function (rowClone) {
            if (rowClone.parentNode) rowClone.parentNode.removeChild(rowClone);
          });

          group.forEach(function (row) {
            remainderSections[sectionIndex].appendChild(row.cloneNode(true));
          });
          for (var remainderGroupIndex = groupIndex + 1; remainderGroupIndex < rowGroups.length; remainderGroupIndex += 1) {
            rowGroups[remainderGroupIndex].forEach(function (remainingRow) {
              remainderSections[sectionIndex].appendChild(remainingRow.cloneNode(true));
            });
          }
          stopped = true;
          return;
        }

        fittedRows += group.length;
      });
    });

    pruneEmptyTableSections(workingTable);
    pruneEmptyTableSections(remainderTable);

    if (!fittedRows) {
      if (!pageHasContent && sections.length && sections[0].rows.length) {
        var wb = workingTable.querySelector("tbody");
        if (!wb) {
          wb = document.createElement("tbody");
          workingTable.appendChild(wb);
        }
        wb.appendChild(sections[0].rows[0].cloneNode(true));
        Array.from(remainderTable.querySelectorAll("tbody")).some(function (rb) {
          if (rb.rows.length > 0) {
            rb.removeChild(rb.rows[0]);
            return true;
          }
          return false;
        });
        pruneEmptyTableSections(remainderTable);
        if (!tableRowCount(remainderTable)) return { type: "fit" };
        return { type: "split", remainder: remainderTable };
      }
      container.removeChild(workingTable);
      return { type: "nofit" };
    }

    if (!tableRowCount(remainderTable)) return { type: "fit" };

    (function () {
      var allTbodies = workingTable.querySelectorAll("tbody");
      if (!allTbodies.length) return;
      var lastTbody = allTbodies[allTbodies.length - 1];
      var lastRow = lastTbody.rows[lastTbody.rows.length - 1];
      if (!lastRow) return;
      Array.from(lastRow.cells).forEach(function (cell) {
        cell.style.borderBottom = "1px solid #111";
        cell.style.boxShadow = "inset 0 -1px 0 0 #111";
      });
    })();

    return { type: "split", remainder: remainderTable };
  }

  function appendNode(page, container, node, pageHasContent) {
    if (isPageBreak(node)) return { type: "break" };

    if (isElement(node, "table")) {
      var fitResult = appendWholeNode(page, container, node);
      if (fitResult.type === "fit") return fitResult;
      return splitTableNode(page, container, node, pageHasContent);
    }

    if (node.nodeType === Node.ELEMENT_NODE && BLOCK_TAGS[node.tagName.toLowerCase()]) {
      return splitParagraphNode(page, container, node, pageHasContent);
    }

    if (
      node.nodeType === Node.ELEMENT_NODE &&
      node.classList &&
      node.classList.contains("coa-keep-together")
    ) {
      var keepResult = appendWholeNode(page, container, node);
      if (keepResult.type === "fit") return keepResult;

      if (!pageHasContent) {
        container.appendChild(node.cloneNode(true));
        return { type: "fit" };
      }

      return { type: "nofit" };
    }

    var blockResult = appendWholeNode(page, container, node);
    if (blockResult.type === "fit") return blockResult;

    if (!pageHasContent) {
      container.appendChild(node.cloneNode(true));
      return { type: "fit" };
    }

    return { type: "nofit" };
  }

  function renderQRCodes(root) {
    root.querySelectorAll(".coa-qr-code").forEach(function (target) {
      var payload = target.dataset.qrPayload;
      if (!payload || !window.QRCode) return;
      target.innerHTML = "";
      new window.QRCode(target, { text: payload, width: 90, height: 90 });
    });
  }

  function renderFallbackFirstPage(source, tail) {
    var firstPage = document.getElementById("coa-page-first");
    var firstResult = firstPage ? firstPage.querySelector(".coa-page-result") : null;

    if (!firstPage || !firstResult) return;

    firstResult.innerHTML = "";
    if (source && source.innerHTML.trim()) {
      firstResult.innerHTML = source.innerHTML;
    }
    if (tail && tail.innerHTML.trim()) {
      firstResult.insertAdjacentHTML("beforeend", tail.innerHTML);
    }

    renderQRCodes(firstPage);
    document.body.classList.remove("coa-rendered-ok");
    document.body.classList.add("coa-pagination-failed");
    document.dispatchEvent(new CustomEvent("coa:ready"));
  }

  function paginate() {
    var firstPrototype = document.getElementById("coa-page-prototype-first");
    var continuationPrototype = document.getElementById("coa-page-prototype-continuation");
    var source = document.getElementById("coa-result-source");
    var tail = document.getElementById("coa-tail-source");
    var renderedPages = document.getElementById("coa-rendered-pages");
    var measureRoot = document.getElementById("coa-measure-root");
    var pendingNodes;
    var pages = [];
    var iterations = 0;

    if (!firstPrototype || !continuationPrototype || !source || !tail || !renderedPages || !measureRoot) {
      setDebugStatus("missing required DOM nodes");
      renderFallbackFirstPage(source, tail);
      return;
    }

    setDebugStatus("v2-fixed loaded");

    pendingNodes = collectPageItems(source, tail);
    if (!pendingNodes.length) {
      setDebugStatus("no result content found");
      renderFallbackFirstPage(source, tail);
      return;
    }

    renderedPages.innerHTML = "";
    measureRoot.innerHTML = "";

    while (pendingNodes.length && pages.length < MAX_PAGES) {
      var prototype = pages.length === 0 ? firstPrototype : continuationPrototype;
      var pageParts = createPage(prototype);
      var page = pageParts.page;
      var resultContainer = pageParts.result;
      var pageHasContent = false;

      iterations += 1;
      if (iterations > MAX_ITERATIONS) {
        setDebugStatus("pagination hit safety limit");
        renderFallbackFirstPage(source, tail);
        measureRoot.innerHTML = "";
        return;
      }

      measureRoot.appendChild(page);
      applyResultLimit(page, resultContainer);

      while (pendingNodes.length) {
        var candidate = pendingNodes[0];
        var result = appendNode(page, resultContainer, candidate, pageHasContent);

        if (result.type === "fit") {
          pendingNodes.shift();
          pageHasContent = true;
          continue;
        }

        if (result.type === "split") {
          pendingNodes[0] = result.remainder;
          pageHasContent = true;
          break;
        }

        if (result.type === "break") {
          pendingNodes.shift();
          if (pageHasContent) break;
          continue;
        }

        break;
      }

      if (!pageHasContent) {
        measureRoot.removeChild(page);
        setDebugStatus("page " + (pages.length + 1) + " had no appendable content");
        renderFallbackFirstPage(source, tail);
        measureRoot.innerHTML = "";
        return;
      }

      pages.push(page);
    }

    if (!pages.length) {
      setDebugStatus("no rendered pages created");
      renderFallbackFirstPage(source, tail);
      return;
    }

    var firstPage = document.getElementById("coa-page-first");
    var firstResult = firstPage ? firstPage.querySelector(".coa-page-result") : null;
    if (firstResult) {
      firstResult.innerHTML = "";
    }

    pages.forEach(function (page, index) {
      var pageNumberTarget = page.querySelector(".coa-page-number");
      if (pageNumberTarget) {
        pageNumberTarget.textContent = (index + 1) + " of " + pages.length;
      }
      renderedPages.appendChild(page);
    });

    measureRoot.innerHTML = "";
    renderQRCodes(renderedPages);
    document.body.classList.add("coa-rendered-ok");
    setDebugStatus("pages created: " + pages.length);
    document.dispatchEvent(new CustomEvent("coa:ready"));
  }

  document.addEventListener("DOMContentLoaded", function () {
    try {
      paginate();
    } catch (error) {
      setDebugStatus("error: " + error.message);
      console.error("COA pagination failed", error);
      renderFallbackFirstPage(
        document.getElementById("coa-result-source"),
        document.getElementById("coa-tail-source")
      );
    }
  });
})();
