---
name: ui
description: >-
  Build a one-off HTML page as a side-channel UI in the browser when the user has a lot of small, structured decisions to grind through (triage lists, per-item assessments, multi-row picks, forms), or when they want to chat with you through a floating popover instead of the terminal. A tiny local HTTP server serves the page; the browser POSTs user input + chat messages to JSON files you watch with Monitor, and polls response JSON files you write.
user-invocable: true
---

# UI — browser-side collaboration surface (Experimental)

A side-channel for tasks that would otherwise look like "ok, next… ok, next…" in
chat, *or* for chat itself when the user wants to see your replies in a browser
popover and reply from there.

Two surfaces, mix and match per task:

1. **Structured UI** — the main page content (table, form, list, etc.).
  Browser ↔ you via `in.json` / `out.json`.
2. **Chat popover** — floating chat panel in the corner. **Always embedded by
  default**, even alongside a structured-UI page. Only omit it if the user
   explicitly asks you to (e.g. "no chat popover", "skip the chat panel").
   Browser ↔ you via `chat-in.json` / `chat-out.json`. Same plumbing; separate
   files.

## When to reach for it

When the user explicitly invokes it.

## Setup

1. Create a randomly-named serve dir. Its name is the only thing keeping random network neighbours off the page, so don't print it anywhere public:
  ```sh
   SERVE_DIR=/tmp/ui-$(python3 -c 'import secrets; print(secrets.token_hex(12))')
   mkdir -p "$SERVE_DIR"
  ```
2. Write a self-contained page at `$SERVE_DIR/index.html`. Inline CSS and JS, no build step, no external assets, no file picker. The server will hand it to the browser at `http://127.0.0.1:<port>/`.
  In the page JS, talk to the server over same-origin HTTP:
   Debounce `saveInput` ~400ms. Poll `pollOutput` every 1–2s.
   Embed the chat popover template by default — see **Chat popover** below.
   Skip it only if the user explicitly opted out.
3. Start the bundled server scoped to that dir, on an OS-assigned port, in the background:
  ```sh
   SERVE_ROOT=$SERVE_DIR python3 .claude/skills/ui/references/server.py
  ```
   Run via Bash with `run_in_background: true`. Read the first stdout line from the task output file to find the assigned port (`serving … at http://127.0.0.1:<port>`).
4. Tell the user: open `http://127.0.0.1:<port>/`. No Connect button, no file picker — the page is already wired to the server it came from.

## Event shape

You decide per task. Defaults that work:

- **In** (`in.json`, browser → you): one JSON object, fully rewritten on every save. Keys are row/item ids, values are whatever the user is filling. Easy to diff between writes.
- **Out** (`out.json`, you → browser): a JSON array of events, append-only. Each entry: `{ id, type, payload }`. Browser tracks last-seen id and only acts on new ones.

Pick `type` names that match what the UI does — `highlight`, `markDone`, `setNote`, `toast`, `finish`, etc. Build the browser-side handler for each type before you start using it. The browser ignores unknown types.

## Chat popover

A floating panel that lets the user read your replies and write back from the
browser. Reuses the same server; just adds two more files.

**Default-on.** Every page you generate under this skill should include the
popover unless the user explicitly told you not to. It's the fallback chat
channel when the structured UI doesn't have a natural place to ask a question.

**Files (relative to `$SERVE_DIR`):**

- `chat-in.json` — full array of user messages, browser rewrites via `/write` on each send.
- `chat-out.json` — full array of your messages, you rewrite via the Write tool when you reply.

Each entry: `{ id: number, text: string, ts: number }` where `ts` is `Date.now()`
at write time. The page merges both arrays by `ts` to render the conversation
in order.

**Embedding the popover:**

The template lives at `.claude/skills/ui/references/chat-popover.html`. It contains three
blocks (`<style>`, two DOM nodes, `<script>`) — paste them straight into the
`<head>`/`<body>` of your generated `index.html`. The template is same-origin
and self-wires; no init call needed.

For chat-only sessions, the popover can be your entire UI — start it open by
default (`data-open="true"` on `#uiChatPanel`) and skip rendering anything
else in the page body.

**"Claude is thinking" indicator.** The template renders a pulsing-dots bubble
at the bottom of the log whenever the latest user message has no later
assistant reply — i.e. the user has spoken and you haven't answered yet. It
auto-clears as soon as you write a reply to `chat-out.json` with a `ts` newer
than the user's last message (this is one of the reasons real system-clock
timestamps matter — see **Sending a reply** below). A 90-second safety timeout
hides it if no reply lands, so the UI doesn't get stuck when you're not
monitoring.

**Watching incoming chat:**

Run a second persistent Monitor command alongside the task one, watching
`$SERVE_DIR/chat-in.json` for new entries:

```sh
last=""
while sleep 1; do
  cur=$(jq -r '.[] | "\(.id)\t\(.text)"' "$SERVE_DIR/chat-in.json" 2>/dev/null || true)
  if [ "$cur" != "$last" ]; then
    diff <(printf '%s\n' "$last") <(printf '%s\n' "$cur") | grep '^>' || true
    last="$cur"
  fi
done
```

Each notification batch carries any new user lines; respond when they land.

**Sending a reply:**

When you have something to say, append your message to `chat-out.json` (read it
first if it exists, append, write the full array back). Keep ids monotonic and
unique. The browser's poller picks it up within ~1.5s and renders it in the
panel; if the panel is closed the FAB shows an unread badge.

**Timestamps must come from the real system clock**, not from your head. The
browser merges user and assistant messages by `ts`, so a stale or invented value
re-orders the conversation. Always fetch the current epoch-ms with the shell
before composing the entry:

```sh
python3 -c 'import time;print(int(time.time()*1000))'
```

Use that value as `ts`. macOS `date` doesn't support `%N`, so the Python form is
the portable default. Never paste a previous timestamp or guess a number that
"looks recent" — the only way to guarantee correct ordering is to read the clock
at the moment you write the reply.

A reply is just text — no event-type wrapper, no payload. Use it for:

- Acknowledging task progress that doesn't need its own event type (`out.json`)
- Asking the user a free-form question mid-task
- Whole-conversation chat when the page exists for chat alone

## Watching

Use the Monitor tool, persistent, polling `$SERVE_DIR/in.json` once a second with `jq` to diff against the previous content. Emit one stdout line per changed row so each save fires a single notification batch. Respond when notifications land.

Run a second Monitor against `chat-in.json` in parallel — same pattern. Skip
this only if the user opted out of the chat popover for this session.

## Responding

Rewrite `$SERVE_DIR/out.json` with the full array plus a fresh incrementing id appended. The browser's poller picks it up on its next tick and runs the matching handler.

For chat replies, do the same with `chat-out.json` (see **Chat popover** above).

## Live reload

When any non-JSON file under `$SERVE_DIR` changes, the server fires a reload
event to the open tab within ~1s. The injected snippet performs a **soft swap**,
not a full `location.reload()`:

1. Fetches the new HTML.
2. Replaces `<head>` and `<body>` content with the new document.
3. Restores `[data-preserve]` subtrees: any element in the live DOM with a
  `data-preserve` attribute (and an `id`) is detached before the swap and
   re-attached over the matching placeholder in the new DOM, preserving node
   identity.
4. Executes only the `<script>` elements whose source text (or `src`) wasn't
  already executed on this page — existing IIFE closures, timers, and event
   listeners keep running.
5. Restores `window.scrollY` and re-focuses the previously-active element if it
  survived the swap.

Result: in-memory JS state (variables in IIFEs, EventSource connections, poll
timers) survives reloads as long as the script's text didn't change. Form
inputs, scroll positions, and panel-open state survive on any subtree marked
`data-preserve`.

`*.json` files are excluded from the watch so `in.json` / `out.json` /
`chat-*.json` writes don't trigger reloads.

### `data-preserve` convention

Add `data-preserve` (plus a stable `id`) to any element whose DOM identity
should outlive a swap — typically containers that hold transient UI state the
script tracks via direct node references. The chat popover's FAB and panel
already carry it. Examples of nodes worth marking:

- Floating panels / modals you've opened
- Inputs / textareas the user is mid-typing in
- Scrollable lists with current scroll position
- Anything wrapping a third-party widget that costs to re-initialise

If you change the *script* itself (not just markup), the new text counts as a
new script and runs fresh. The previous IIFE's closures stay alive in memory
until their listeners are cleared — if those listeners were bound to a
`data-preserve`'d node, the OLD listener and the NEW listener both fire on
every event. The old one usually runs first, which is enough to break a
form-submit flow: the old handler reads `input.value`, clears it, and the new
handler sees an empty string.

**Always start a script that binds to preserved nodes with a clone-replace
step.** `cloneNode(true)` deep-clones a node — attributes carry over,
listeners do not. Replace each preserved node with its clone before
re-querying and binding:

```js
for (const id of ['uiChatFab', 'uiChatPanel']) {
  const el = document.getElementById(id);
  if (!el || !el.parentNode) continue;
  // form-field values are properties, not attributes — preserve manually
  const fields = Array.from(el.querySelectorAll('input, textarea, select'));
  const values = fields.map((f) => [f.id, f.value]);
  el.parentNode.replaceChild(el.cloneNode(true), el);
  for (const [iid, val] of values) {
    if (!iid) continue;
    const fresh = document.getElementById(iid);
    if (fresh) fresh.value = val;
  }
}
```

Anything that runs on a timer (`setInterval`, `setTimeout` chain, EventSource)
should also stash its handle on `window.__yourFeatureName...` so the next IIFE
can clear it — otherwise you leak one timer per script change.

**Event-listener gotcha (non-preserved nodes).** A direct
`btn.addEventListener(...)` against a button that isn't `data-preserve`'d
binds the listener to *that node*. After a swap, the live DOM has a *fresh*
button — the old listener is still alive but attached to a now-detached node,
so clicks on the visible button do nothing. Two ways to dodge this:

1. **Mark the listener's target `data-preserve`** so the same node carries
  through the swap. Then apply the clone-replace pattern above. Works for a
   small handful of interactive elements.
2. **Use event delegation on a preserved parent** — put `data-preserve` (and an
  `id`) on a container, attach one listener there, dispatch on
   `e.target.closest('[data-action]')`. The parent persists; the children inside
   can be swapped freely without losing interactivity. Prefer this for any UI
   with multiple interactive elements or markup you expect to evolve.

If the soft swap throws (fetch fails, parse error), the snippet falls back to a
full `location.reload()`.

## Teardown

When done: `kill $(lsof -ti:<port>)` and `rm -rf "$SERVE_DIR"`.

## Caveats

- The random serve dir name is your only access control while the server runs. Don't put the URL anywhere public, and tear the server down when the task is finished.
- Never put secrets in the HTML or the JSON files — they live in `/tmp/` in plain text. This applies double to the chat popover, since users may type freely.
- The server has no listings (`/` only resolves to `index.html`) and refuses POSTs anywhere outside `/write`, but it does not authenticate — anything that knows the port and path can read and write.

