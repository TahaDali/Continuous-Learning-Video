# Preserve the learning experience

Use before adapting the manuscript, before bulk rendering, and during acceptance review. These checks address the demonstrated failure in which a technically valid course lost the parent story and replaced explanatory animation with labeled diagrams.

## Parent narrative and adaptation

Author substantial connected parts before choosing video boundaries. A role course should make the organization's purpose, supported direction, operating model and need for the role intelligible. Distinguish a published mission from an interpreted vision, proposed strategy or unknown internal roadmap. Carry the organization into technical work through reader, customer, editorial, employee or business consequences.

Develop scenes around a consequential decision: a person needs something; constraints or disagreement complicate it; evidence changes a hypothesis; alternatives have different consequences; an action produces a result that can be examined. Let the recurring employee learn and sometimes make a consequential mistake. Recurring names alone do not establish a developing story.

Maintain `narrative-map.json` with `parts` (`id`, `title`, `question`) and `chapters` (`id`, `partId`, exact Markdown `heading`, `lessonIds`, `retainedDecisions`, `adaptation`). Each chapter points to its actual manuscript heading; every lesson is assigned. `adaptation` explains retention and any omitted detail. Do not impose a universal lesson count, equal chapter sizes or minimum word quota. Respect the depth and part structure explicitly requested by the user.

Write `review/editorial.json` with `status`, `reviewer`, `findings` and `limitations`. Each finding names a `partId`, a `chapterId` and an `observation` supported by the actual manuscript. Examine organization/strategy, operating handoffs, worked technical reasoning, hiring evidence and the employee learning arc where they belong in scope. Correct thin coverage before recording completion. Point to a concrete scene, plausible alternative, changed or failed hypothesis, consequence and check for each substantial part. A broad paragraph praising a part is not sufficient evidence. Compare source and adapted scope explicitly; do not use word counts as a proxy for understanding. This producer review is not an independent learner test.

## Meaningful motion

For an explanation of change, identify the observable model before implementation:

- **Identity:** What same article, request, record, amount or person persists?
- **Trigger:** What event or unmet condition causes a change?
- **Transformation:** What moves, branches, waits, changes state or gets rejected?
- **Invariant:** What must remain true while that occurs?
- **Exception and result:** What would failure look like, and what evidence shows the corrected behavior?

Write those specifics into the sentence beat sheet, including purposeful holds. Tie key reveals to named words or phrases when sentence starts are too coarse. Pure context may use a static map or date; a label saying “deduplicate” cannot replace two requests visibly producing one intended write.

`visual-design.json` contains `mechanisms`: `id`, `lessonIds`, `question`, named `states` (`id`, `meaning`), and `transitions` (`from`, `to`, `trigger`, `change`, `invariant`). The mechanism may span lessons. Keep the contract small enough to inspect and specific enough to falsify. Its language must describe the actual authored graphics, not promise a simulation that the renderer does not implement.

Examples of falsifiable explanations:

- Send revision 2 before revision 1; let the late revision attempt the same destination; reject it while the displayed article remains revision 2.
- Send the same request ID twice; show two responses but one durable write. Then send a different valid ID to demonstrate a distinct operation.
- Keep most request durations short while a minority grows slow; expose the distribution and queue rather than naming a latency tail beside unrelated bars.
- Carry identifiable records and relationships into the destination; expose and reconcile a missing or incorrect item. Matching counts alone must visibly fail to prove equality.

## Prototype and acceptance review

Before bulk rendering, export silent prototype clips from the authored renderer and inspect their intermediate encoded frames. Cover distinct or difficult mechanisms proportionately, including exceptions. Declare additional local helper files used by the renderer in `course.renderSources`. Record `review/prototypes.json`: `status`, `reviewer`, `worldSha256`, `sourceHashes` (world, motion library and declared helper paths), `clips` (`mechanismId`, project-relative `path`, `observation`) and `limitations`. Refresh the report if the authored world or helpers change. Use exact clips, not an unrelated starter example.

Ask what can be inferred with narration and captions removed. Explain any ambiguity and repair weak behavior. Keep legibility, purposeful pauses, hierarchy and manageable density; adding motion or filling every empty area is not a quality objective. Camera movement earns its place by revealing a relationship. Test the actual encoded result as well as registered geometry: internal shape borders, connectors, graphical semantics and learner interpretation are outside a basic bounds audit.

At delivery, distinguish technical integrity, editorial review, producer visual inspection, complete listening, synchronized viewing and independent learner comprehension. A clean renderer or a completed JSON form is not evidence that all of these occurred.
