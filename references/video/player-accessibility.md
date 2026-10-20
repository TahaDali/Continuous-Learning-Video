# Mobile and accessibility review

Use the bundled player when creating a course. Customize the visual identity and course data without losing its interaction behavior. Keep the lesson count determined by the material; examples do not establish a fixed curriculum.

## Preserve the player contract

- Keep authored controls and standalone action links at least 44 CSS pixels high, with visible keyboard focus and wrapping layouts. Keep transcript and main lesson reading text at least 1rem. Native media controls vary by browser; inspect them separately.
- Keep the skip link and labelled video, captions, speed, completion and lesson navigation. The transcript shortcut opens and focuses the transcript without changing the lesson fragment or playback position. Transcript jump points retain their existing seek behavior.
- Use a labelled single-choice radio group for each valid exercise. One choice is in the Tab sequence; arrow keys select and wrap, Home/End select the ends, and Space/Enter activate the focused choice. Expose the selected state independently of color. Keep feedback specific to the selected option, announce changes politely, and clear selection/feedback when changing lessons. Answering does not certify completion or readiness.
- Keep the course drawer modal and labelled. Tab and Shift+Tab stay within its visible controls, including opened disclosures and reset confirmation. Escape and Close return focus to the opener; choosing a lesson focuses its heading. Keep both reset actions visible in short landscape viewports. Opening or closing the drawer preserves playback state.
- Keep feedback/progress live regions available before updates, meaningful source-link names, and notice when links open new tabs. Render course strings as text. Keep existing reduced-motion behavior and a visible selection/focus state in forced colors.
- Preserve the current course's language for the document and caption track. Do not hard-code English for other languages.

For an interface-only repair, record hashes of lesson data, media, captions and posters before editing and compare afterward. Compare transcript and reference text too if modifying their HTML wrappers. Avoid regenerating narration or replacing media for a layout repair.

## Check the actual course

Exercise the generated player over HTTP with real course data. Check a narrow phone (320 CSS pixels), common phone sizes (375–390), tablet (768), short landscape (568 × 320), and desktop. Equivalent sizes are acceptable when relevant to the audience. Check enlarged text/zoom as well as viewport emulation. There should be no page-wide horizontal overflow or clipped controls; preserve two-dimensional diagrams and tables inside their own accessible scrolling regions.

Test the skip link, drawer, disclosures, previous/next boundaries, deep links, captions, speed, completion, reset/cancel, transcript shortcut and jump points, exercise selection and feedback. Check forward/backward keyboard navigation, Escape, focus return, visible focus, and what is announced by live regions when a screen reader is available. Verify that interface work did not change saved-progress storage keys or media behavior.

Check text and control contrast in their actual backgrounds and states: normal text 4.5:1, large text 3:1, and essential control boundaries/selection/focus indicators 3:1. Review images/video separately; a DOM text scan cannot assess diagram text or captions painted into video. Contrast and interaction tests are partial evidence, not an accessibility certification.

For wide reference tables, keep a named focusable scroll wrapper, scoped column headers and a visible focus outline. `scripts/write_beat_sheet.py` writes both the existing Markdown sheet and `visual-beat-sheet/beat-sheet.html` with these features. Inspect that HTML with the actual long text. The local sheet is not automatically added to the public exporter; review its contents and publishing scope before linking it from a hosted course.

Record viewport sizes, browser, keyboard checks, content-preservation results and remaining limits in the acceptance record. Distinguish browser emulation from a physical device, semantic inspection from spoken screen-reader testing, and download-content tests from actual file delivery. Do not claim unperformed checks or silently promote a review edition to full accessibility acceptance.
