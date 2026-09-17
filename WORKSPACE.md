# ece298a

Your workspace on iiks1. Everything you make lives under this folder and nowhere else on the box.

## Project channels

- `#ece298a` is this workspace. Say `new project <name>` there and you get `#ece298a--<name>`, its updates lane
  and a project under here. That line counts only from you or the owner — a SESSION saying it is ignored, so a
  session either asks you for it or runs `cc slack project <name>` itself, which asks the box for the same
  channel — three an hour, that way.
- A project can also announce ITSELF. Put one glob a line in `.cc/projects` — a lessons workspace writes
  `*/COURSE.md` — and every directory a line like that matches gets its channel within a quarter of an hour,
  with nobody typing anything. Same three an hour, same rules on the name: it is your folder's name, so a name
  the box cannot use is refused with the reason rather than turned into some other channel.
- `#ece298a-updates` carries the automated flow — progress, budget notices, audits.

The owner is in every channel the box makes for you. See `docs/design-member-workspaces.md`.
