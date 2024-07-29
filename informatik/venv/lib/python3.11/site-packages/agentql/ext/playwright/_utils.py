def post_process_accessibility_tree(accessibility_tree: dict):
    """Post-process the accessibility tree by removing node's attributes that are Null."""
    if "children" in accessibility_tree and accessibility_tree.get("children") is None:
        del accessibility_tree["children"]

    for child in accessibility_tree.get("children", []):
        post_process_accessibility_tree(child)


def merge_iframe_tree_into_page(
    iframe_id, accessibility_tree: dict, iframe_accessibility_tree: dict
):
    """
    Stitches the iframe accessibility tree with the page accessibility tree.

    Parameters:
    ----------
    iframe_id (str): The ID of the iframe.
    accessibility_tree (dict): The accessibility tree of the page.
    iframe_accessibility_tree (dict): The accessibility tree of the iframe.

    Returns:
    --------
    None
    """
    children = accessibility_tree.get("children", []) or []
    for child in children:
        attributes = child.get("attributes", {})
        if "tf623_id" in attributes and attributes["tf623_id"] == iframe_id:
            if not child.get("children"):
                child["children"] = []
            child["children"].append(iframe_accessibility_tree)
            break
        merge_iframe_tree_into_page(iframe_id, child, iframe_accessibility_tree)
