# Bluesky Stream – Social Media Portal

## 1. Overview

A static HTML website that serves as a social media portal, displaying a live-style feed of posts sourced from the provided Bluesky Jetstream messages. The portal will present all post types (text, images, and videos) in a single-column feed, similar to Twitter. The design will be clean, modern, and responsive, with a light theme.

---

## 2. Visual Style

- **Design Aesthetic:** Clean, modern, and minimalistic
- **Theme:** Light
- **Typography:** Sans-serif (e.g., Inter, Arial, or similar)
- **Colors:** White background, dark text (#222), subtle blue accents for highlights and links
- **Layout:** 
  - Single-column feed, centered on the page
  - Responsive for mobile and desktop
  - Each post in a card with gentle shadow and rounded corners
- **Navbar:** 
  - Top navigation bar with site title ("Bluesky Stream")

---

## 3. Content Structure

### Navbar

- **Title:** "Bluesky Stream" (left)

---

### Hero Section

- **Heading:** "Bluesky Stream"
- **Subheading:** "Live updates from Bluesky Jetstream"


---

### Feed Section

Display all provided posts in reverse chronological order (newest first). Each post card includes:

- **Timestamp:** Human-readable (e.g., "September 16, 2025, 15:15")
- **Text Content:** Main post text
- **Media:**
  - **Images:** Display all images in the post, respecting aspect ratio, with lightbox on click
  - **Videos:** Embed playable video with controls, responsive width
- **Source/Author:** Display the author's handle and avatar at the top of each post (do not show raw DID in the main UI):
  - Render the avatar as a circular image (~38px) and the handle as the display name next to it.
  - Keep the DID in a data-attribute for debugging/accessibility if needed, but do not render it visibly.
- **Post Card Styling:** 
  - White background, subtle border/shadow, rounded corners, margin between posts

#### Posts to Display

**(All posts below are to be included, in reverse chronological order by `createdAt`):**
For each post, display the following data:
1. User
2. Text
3. Any media (images, videos)

---

## 4. Additional Features

- **Lightbox for Images:** Clicking an image opens it in a modal/lightbox for larger view.
- **Responsive Video:** Videos are embedded with controls and scale to fit the card width.
- **Post Time Formatting:** Use JavaScript or static formatting to display human-readable dates.
- **Accessibility:** Alt text for images (use empty alt if not provided).
- **Error Handling:** If media fails to load, display a fallback message or icon.
  - When a blob fetch fails, retry the same CID using `https://bsky.network/xrpc/com.atproto.sync.getBlob?did={DID}&cid={CID}` as a fallback.
  - If both primary and fallback fail, render a placeholder with a “Media unavailable” label.
  - If handle or avatar cannot be fetched, display the DID as a muted fallback label and a placeholder avatar.
  - If `app.bsky.actor.getProfile` is unavailable, attempt `app.bsky.actor.getProfiles` (batch) or cache from a previous successful run; otherwise use a generic placeholder avatar and “@unknown” handle.
- **Runtime profile fetch:** Use client-side JavaScript to fetch author profiles for each unique DID using:
  - `https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor={DID}`
  - Populate avatar (profile.avatar URL) and display name/handle in the post header on page load.

---

## 5. Technical Notes

- All media files must be loaded via the Bluesky public API blob endpoints (e.g., com.atproto.sync.getBlob) using each post’s DID and media CID. Do not reference the previous CDN domain.
- Resolve and display user identities via `app.bsky.actor.getProfile` using each post's DID. This may be done at build time or at runtime using the public endpoint:
  - Build-time: call `app.bsky.actor.getProfile` and embed results.
  - Runtime: fetch from `https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor={DID}` on page load and update the DOM.
  - Load the avatar image via the blob endpoint for the actor’s DID and avatar CID.
- No login or interactivity required; this is a static, read-only portal.
- All content is pre-fetched and rendered at build time.

---

## 6. Files and Assets

- All images and videos referenced above are to be loaded from:
  - Bluesky public APIs and blob endpoints. For images and videos, resolve blobs via:
    - `https://bsky.social/xrpc/com.atproto.sync.getBlob?did={DID}&cid={CID}`
    - or an equivalent public PDS blob URL for the author's DID. Do not use the CDN links provided earlier.

- Posts can be fetched using https://public.api.bsky.app/xrpc/app.bsky.feed.getPostThread?uri=at://did:plc:xyz
---

## 7. Footer

- Simple footer with copyright:  
  `© 2025 Bluesky Stream. All rights reserved.`

---

## 8. Deliverables

- Single static HTML file with embedded CSS (or linked to a single CSS file)
- All media loaded via Bluesky blob endpoints; author handle and avatar populated via `app.bsky.actor.getProfile` (at build time or via client-side JS)
- Ready for deployment as a static site

## 9. DATA
Use this data to populate the media feed
{
      "id": 5,
      "uri": "at://did:plc:4aqzua5vsewimmusg66fyajl/app.bsky.feed.post/3lyy3ry4xo22q",
      "cid": "bafyreic3uymvuti4vmdaw3i5274blsk3vuuuqmopf2pe5bhr3dcabk3edu",
      "did": "did:plc:4aqzua5vsewimmusg66fyajl",
      "collection": "app.bsky.feed.post",
      "rkey": "3lyy3ry4xo22q",
      "time_us": 1758052254912026,
      "created_at": "2025-09-16T19:50:50.380000",
      "langs": [
        "en"
      ],
      "text": "In occupied Melitopol, petrol has once again run out, with most gas stations empty. The last fuel delivery was made on Friday, and no new supplies have arrived since.\n\nUkrainian sanctions.",
      "reply_root_uri": null,
      "reply_parent_uri": null,
      "record": {
        "$type": "app.bsky.feed.post",
        "createdAt": "2025-09-16T19:50:50.380Z",
        "embed": {
          "$type": "app.bsky.embed.images",
          "images": [
            {
              "alt": "",
              "aspectRatio": {
                "height": 1280,
                "width": 960
              },
              "image": {
                "$type": "blob",
                "ref": {
                  "$link": "bafkreih3ps2by7a7bkh4pexkxiov52fqcgy2r62wx2ip2atzaxcebpo6gm"
                },
                "mimeType": "image/jpeg",
                "size": 555635
              }
            },
            {
              "alt": "",
              "aspectRatio": {
                "height": 580,
                "width": 960
              },
              "image": {
                "$type": "blob",
                "ref": {
                  "$link": "bafkreifziry2g2t2nfuq6wp73idazx446tsmcpm6mumasf65gfqcedncxq"
                },
                "mimeType": "image/jpeg",
                "size": 202671
              }
            }
          ]
        },
        "langs": [
          "en"
        ],
        "text": "In occupied Melitopol, petrol has once again run out, with most gas stations empty. The last fuel delivery was made on Friday, and no new supplies have arrived since.\n\nUkrainian sanctions."
      },
      "raw": null
    },

You will need to write the javascript to hydrate the data and populate the media feed.
You will use a html template for the items and populate it with the data.



