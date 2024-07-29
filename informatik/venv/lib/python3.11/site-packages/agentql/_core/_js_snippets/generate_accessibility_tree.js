({
  currentGlobalId,
  roleTagMap,
  processIFrames = true,
  iframePath = "",
  includeAriaHidden = false,
  nodeIdsToIgnore = [],
}) => {
  function generate_unqie_dom_id() {
    currentGlobalId++;
    window["tf_generated_dom_id"] = currentGlobalId;
    return currentGlobalId;
  }

  function buildAccessibilityTree() {
    const rootNode = document.documentElement;
    const tree = createNode(rootNode, iframePath);
    return tree;
  }

  function extractAttributes(node) {
    const attributes = { html_tag: node.nodeName.toLowerCase() };
    const skippedAttributes = ["style", "srcdoc"];
    for (let i = 0; i < node.attributes.length; i++) {
      const attribute = node.attributes[i];
      if (!attribute.specified || !skippedAttributes.includes(attribute.name)) {
        attributes[attribute.name] = attribute.value || true;
      }
    }
    return attributes;
  }

  function processHTML(node) {
    for (let child of node.childNodes) {
      const childTag = child.nodeName.toLowerCase();
      if (childTag === "head") {
        return processHead(child);
      }
    }
    return null;
  }

  function processHead(node) {
    for (let child of node.childNodes) {
      const childTag = child.nodeName.toLowerCase();
      if (childTag === "title") {
        child.setAttribute("tf623_id", generate_unqie_dom_id());
        return {
          role: "webArea",
          name: child.textContent.trim(),
          attributes: extractAttributes(child),
        };
      }
    }
    return null;
  }

  function getRole(node) {
    const role = node.getAttribute("role") || node.getAttribute("aria-role");
    if (role) {
      return role;
    }
    const tag = node.nodeName.toLowerCase();
    if (tag == "input") {
      const type = node.getAttribute("type");
      if (type) {
        return roleTagMap.input[type] || type;
      }
      return "textbox";
    }
    return roleTagMap.role[tag] || "generic";
  }

  function getName(element) {
    // Special case: textContent for button elements
    if (element.tagName.toLowerCase() === "button") {
      const textContent = element.textContent.trim();
      if (textContent) {
        return textContent;
      }
    }

    // List of attributes in the order they should be checked
    const attributes = [
      "aria-label",
      "placeholder",
      "alt",
      "title",
      "value",
      "name",
    ];

    // Iterate over the attributes and return the first non-empty one
    for (const attribute of attributes) {
      if (element.hasAttribute(attribute)) {
        const value = element.getAttribute(attribute).trim();
        if (value) {
          return value;
        }
      }
    }

    // Fallback to empty string if no non-empty attribute is found
    return "";
  }

  function isElementHidden(element) {
    // Check if the element exists
    if (!element) {
      return true;
    }
    const style = window.getComputedStyle(element);

    // Check if the element is hidden by display property
    if (style.display === "none") {
      return true;
    }

    // Check if the element is hidden by visibility property
    if (style.visibility !== "visible") {
      return true;
    }

    // Check if the element is hidden by opacity
    if (style.opacity === "0") {
      return true;
    }

    return false;
  }

  function createNode(node, currentIframePath = "") {
    if (!node) {
      return null;
    }
    const ariaHidden =
      node.getAttribute("aria-hidden") === "true" ||
      node.getAttribute("aria-hidden") === true;
    const tag = node.nodeName.toLowerCase();
    const skippedTags = [
      "script",
      "style",
      "path",
      "g",
      "hr",
      "br",
      "noscript",
      "head",
      "code",
    ];
    if (skippedTags.includes(tag) || nodeIdsToIgnore.includes(node.id)) {
      return null;
    }

    let webAreaNode = null;
    let iframe_path = node.getAttribute("iframe_path");
    if (tag === "html" && !iframe_path) {
      webAreaNode = processHTML(node);
    }

    let role = getRole(node);
    let name = getName(node) || "";
    let newIframePath = currentIframePath;

    let children = [];
    let currentChildNodes = node.childNodes;

    let nodeId = node.getAttribute("tf623_id");
    if (!nodeId) {
      nodeId = generate_unqie_dom_id();
      node.setAttribute("tf623_id", nodeId);
    }

    if (currentIframePath && processIFrames) {
      node.setAttribute("iframe_path", currentIframePath);
    }

    if (node.shadowRoot) {
      const shadowRootChildren = node.shadowRoot.children;
      const childrenNodeList = Array.prototype.slice.call(shadowRootChildren);

      if (childrenNodeList.length > 0) {
        currentChildNodes = Array.from(childrenNodeList);
      } else if (node.shadowRoot.textContent.trim() !== "") {
        name = node.shadowRoot.textContent.trim();
      }
    } else if (tag == "slot") {
      currentChildNodes = node.assignedNodes();
    } else if (tag == "iframe") {
      const iframeDocument = node.contentDocument;
      if (currentIframePath) {
        newIframePath = currentIframePath + "." + nodeId;
      } else {
        newIframePath = nodeId;
      }
      if (iframeDocument && processIFrames) {
        if (iframeDocument.body) {
          currentChildNodes = iframeDocument.body.childNodes;
        } else {
          currentChildNodes = iframeDocument.childNodes;
        }
      } else if (node.src) {
        role = "iframe"; // iframe without contentDocument
      }
    }
    const childNodes = Array.from(currentChildNodes).filter((childNode) => {
      return (
        childNode.nodeType === Node.ELEMENT_NODE ||
        (childNode.nodeType === Node.TEXT_NODE &&
          childNode.textContent.trim() !== "")
      );
    });
    for (let i = 0; i < childNodes.length; i++) {
      let childNode = childNodes[i];
      if (childNode.nodeType === Node.TEXT_NODE) {
        const text = childNode.textContent.trim();
        if (text) {
          if (childNodes.length > 1) {
            const span = document.createElement("span");
            span.textContent = text;
            if (node.contains(childNode)) {
              node.insertBefore(span, childNode);
              node.removeChild(childNode);
            }
            childNode = span;
          } else if (childNodes.length == 1) {
            if (!role || role == "generic") {
              role = "text";
            }
            name = text;
          }
        }
      }
      if (childNode.nodeType === Node.ELEMENT_NODE) {
        const child = createNode(childNode, newIframePath);
        if (child) {
          children.push(child);
        }
      }
    }
    if (children.length === 0) {
      children = undefined;
    }

    if (!role && !name && !children) {
      return null;
    }

    if (isElementHidden(node) || (ariaHidden && !includeAriaHidden)) {
      return null;
    }

    let node_dict = {
      role: role || "generic",
      name,
      attributes: extractAttributes(node),
    };
    if (children) {
      node_dict["children"] = children;
    }
    if (webAreaNode) {
      webAreaNode["children"] = [node_dict];
    }
    return webAreaNode || node_dict;
  }

  return {
    tree: buildAccessibilityTree(),
    lastUsedId: currentGlobalId,
  };
};
