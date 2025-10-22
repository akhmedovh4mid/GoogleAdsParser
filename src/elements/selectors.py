from src.models import NodeSelector


class Blocks:
    google_app = NodeSelector(
        className="android.widget.FrameLayout",
        resourceId="com.google.android.googlequicksearchbox:id/googleapp_content",
    )

    search_box = NodeSelector(
        className="android.widget.FrameLayout",
        resourceId="com.google.android.googlequicksearchbox:id/googleapp_facade_search_box_view",
    )

    navigation_bar = NodeSelector(
        className="android.widget.FrameLayout",
        resourceId="com.google.android.googlequicksearchbox:id/googleapp_navigation_bar_container",
    )

    topbar_container = NodeSelector(
        className="android.widget.FrameLayout",
        resourceId="com.google.android.googlequicksearchbox:id/googleapp_topbar_container",
    )

    news_feed_box = NodeSelector(
        className="android.support.v7.widget.RecyclerView",
        resourceId="com.google.android.googlequicksearchbox:id/googleapp_discover_recycler_view",
    )

    toolbar_container = NodeSelector(
        className="android.widget.FrameLayout",
        resourceId="com.android.chrome:id/toolbar",
    )


class Accounts:
    account_management = NodeSelector(
        resourceId="com.google.android.googlequicksearchbox:id/account_management_expandable_content"
    )

    accounts_label = NodeSelector(
        resourceId="com.google.android.googlequicksearchbox:id/og_bento_account_management_header_container"
    )

    accounts = NodeSelector(
        resourceId="com.google.android.googlequicksearchbox:id/accounts"
    )

    accounts_info = NodeSelector(
        resourceId="com.google.android.googlequicksearchbox:id/og_secondary_account_information"
    )

    accounts_scroll_container = NodeSelector(
        resourceId="com.google.android.googlequicksearchbox:id/og_bento_main_scroll_content"
    )


class Buttons:
    more_option = NodeSelector(
        className="android.view.ViewGroup",
        description="More options",
    )

    more_stories = NodeSelector(
        className="android.view.ViewGroup",
        description="More stories",
    )

    share = NodeSelector(descriptionStartsWith="Share ")

    share_link = NodeSelector(descriptionStartsWith="Share link")

    home = NodeSelector(
        resourceId="com.google.android.googlequicksearchbox:id/googleapp_navigation_bar_discover"
    )

    selected_account = NodeSelector(
        resourceId="com.google.android.googlequicksearchbox:id/googleapp_selected_account_disc"
    )


class Items:
    content_preview_text = NodeSelector(resourceId="android:id/content_preview_text")


class Classes:
    view_group = NodeSelector(
        className="android.view.ViewGroup",
    )

    image_view = NodeSelector(
        className="android.widget.ImageView",
    )

    recycler_view = NodeSelector(
        className="android.support.v7.widget.RecyclerView",
    )

    frame_layout = NodeSelector(
        className="android.widget.FrameLayout",
    )

    text_view = NodeSelector(
        className="android.widget.TextView",
    )
