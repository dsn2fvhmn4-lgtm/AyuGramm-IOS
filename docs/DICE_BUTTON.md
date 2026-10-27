# Experimental floating dice button

A 44-point dice button stays at the right side of the current chat, including an
empty chat. It opens the 1–6 picker directly. It follows the visible chat area
when the keyboard opens or the device rotates, respecting the navigation bar,
home indicator and side safe areas. Selection, editing, preview and read-only
states hide it. Secret chats are excluded.

The backend selects real server rolls in Saved Messages, with at most 24 attempts.
It verifies the value and absence of `fwd_from` in a test forward before sending
to a recipient. If Telegram preserves attribution, it stops and reports that
failure. This adds a direct picker; it does not establish a working method of
sending a chosen native dice value without attribution. The final send may
still differ from the test and its actual response is checked and reported.

Placement tests compile the actual geometry helper on macOS and cover portrait,
landscape, keyboard, side safe areas and insufficient-space cases. Runtime
appearance and Telegram forwarding behavior require an iPhone test. This native
UI feature requires a new IPA; an imported `.plugin` cannot add it to an older build.
