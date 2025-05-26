# `webui/navigation/` Module: Guide

This document explains the `navigation/` subdirectory within the `src/ai_research_assistant/webui/` module. It details how navigation components, particularly the main `NavigationRail`, are structured and how to modify them.

## Purpose

The `navigation/` directory houses the core UI elements responsible for top-level navigation within the AI Research Assistant's web interface. This primarily involves defining the items that appear in the main vertical navigation rail and how they link to different "pages" (views) defined under the `pages/` directory.

## Key Components

-   **`navigation_rail.py`**: This is the central file for defining the application's main navigation structure.
    -   It typically contains a class or functions that generate the list of navigation items (e.g., "Orchestrator", "Agents", "Settings").
    -   Each navigation item is associated with a specific page view from the `pages/` module.
    -   It handles the visual presentation of the navigation rail (icons, text, collapsible groups if any).

## How to Add or Modify Navigation Items

1.  **Identify Target Page**: Ensure the page you want to link to exists within the `pages/` directory (e.g., `pages/my_new_page/my_new_page_view.py`). Refer to `README_WEBUI_PAGES.md` for creating new pages.

2.  **Edit `navigation_rail.py`**:
    -   Open `src/ai_research_assistant/webui/navigation/navigation_rail.py`.
    -   Locate the list or structure where navigation items are defined.
    -   Add a new entry for your page, specifying:
        -   An icon (e.g., emoji or an icon class if a library is used).
        -   A display name (label) for the navigation item.
        -   The key or identifier that links to your page's view function (this often matches the page's directory name or a specific route).

3.  **Link to Page View**: Ensure the main UI orchestrator (usually `src/ai_research_assistant/webui/interface.py`) correctly maps the navigation item's key to the function that creates your page's view (e.g., `create_my_new_page_view()`).

4.  **Test**: Run the WebUI and verify:
    -   The new navigation item appears correctly in the sidebar.
    -   Clicking it loads the intended page.
    -   The active state of the navigation item is correctly highlighted.

## Theming and Layout Considerations

-   The visual appearance of the navigation rail (width, background, item styling) is generally controlled by the application's theme (see `README_WEBUI_THEME.md`) and global CSS (`static/modern-ui.css`).
-   The `NavigationRail` component itself might have parameters for basic layout adjustments, but significant styling changes should be done via the theme or CSS.
-   Ensure that new navigation items follow the existing visual style and information hierarchy.

For overall WebUI structure, refer to `README_WEBUI_OVERVIEW.md`.
For details on page creation, refer to `README_WEBUI_PAGES.md`.