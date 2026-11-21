---
haul: "NNN"
status: draft
target_date: null
publish_date: null
publish_url: null
video_status: pending
source_url: null
photos: []
books: []
---

# Haul NNN

analog doomscrolling, courtesy of the public library.  
testing how far the unlimited checkout policy goes.

part NNN

## Production notes

Copy the [checklist](checklist.md) here and record any duplicate decisions or open items.

## Frontmatter guide

- Use `draft`, `scheduled`, or `published` for the post and `pending` or `archived` for the video.
- Use quoted `YYYY-MM-DD` dates (Cincinnati local time) or `null`. `publish_url` is the live TikTok post URL. `source_url` is the GitHub URL of the final MP4.
- List the carousel images under `photos` using paths relative to the haul folder. Leave an unavailable page photo as `null`.
- List one entry per book under `books`, in top-to-bottom order. Optional `isbn`, `note`, and `catalog_url` fields can help resolve duplicate or attribution questions. For example:

```yaml
books:
  - title: "Remarkable Diaries"
    page_photo: photos/01-page.jpg
```
