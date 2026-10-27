# Experimental dice button

An ordinary 🎲 message has a 44-point number-picker button beside its media.
It uses the right side when there is space, otherwise the left, and avoids the
existing share control. It is hidden during message selection and omitted for
stake dice, secret chats, preview controllers and layouts with no free space.
Tap it to choose 1–6, then confirm preparation and sending to the original chat/topic.

The backend selects real server rolls in Saved Messages, with at most 24 attempts.
It verifies the value and absence of `fwd_from` in a test forward before sending
to a recipient. If Telegram preserves attribution, it stops and reports that
failure. This adds a direct picker; it does not establish a working method of
sending a chosen native dice value without attribution. The final send may
still differ from the test and its actual response is checked and reported.

The placement tests compile the actual geometry helper on macOS and cover
incoming/outgoing positions, narrow layouts, media overlap and share-button
overlap. Runtime appearance and Telegram forwarding behavior require an iPhone
test. This native UI feature requires a new IPA; an imported `.plugin` cannot
add it to an older build.
