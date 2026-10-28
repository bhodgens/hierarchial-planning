# Pitfall 33 - Single-Leaf Trees Skip Interface Contracts and Architecture Overview

When to use: authoring a simple single-leaf plan tree (master.md + 1 leaf).
Lesson: include every required section even when the scope seems trivial - the omissions violate the template contract and the scanner catches them.

When authoring single-leaf trees, it's tempting to omit "optional" sections like `## Interface Contract` and `## Architecture Overview` because the scope seems trivial. In one codebase-review session, 3 of 4 single-leaf masters were missing Interface Contracts (89% completeness) and 1 was missing Architecture Overview (78% for Config Extraction).

The omissions don't block implementation, but they violate the template contract and reduce clarity for future readers.

## Prevention

Even for trivial single-leaf trees, include all required sections:

- **Interface Contracts** (single-leaf): document what the leaf exposes - errors defined, constants added, behavior changes.
- **Architecture Overview**: write 2-3 sentences explaining the system context.

The compliance scanner (`check_template_compliance.py`) catches these - run it before committing (Pitfall 32). Fix effort: about 5 minutes per missing section. Related scanner strictness: Pitfalls 34 and 36.
