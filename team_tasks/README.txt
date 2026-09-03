HOW WE WORK TODAY (send this to everyone along with their file)

TEAM:
Person 1: Agent controller + integration lead (owns base.py contract)
Person 2: Single-image tools (VQA + caption or grounding)
Person 3: Change analysis (bi-temporal)
Person 4: Preprocessing + fine-tuning + optical-SAR fusion
Person 5: Frontend + API + reporting

RULES:
1. First hour: everyone reads README.md, docs/ARCHITECTURE.md, docs/RESEARCH.md, then a 15 min call to lock the two contracts: ToolResult shape (base.py) and the API response dict.
2. Research time-boxed: max 1 hour, then commit to a choice. A working simple thing beats a broken fancy thing.
3. Never blocked: mock what you are waiting for. Person 1 mocks tools, Person 5 mocks the backend, Persons 2/3 use plain PNGs until the validator lands.
4. One branch per person, small PRs into main, merge often (at least every 2-3 hours). Person 1 resolves conflicts on shared files.
5. Never commit datasets or model weights. They are gitignored, keep it that way.
6. When you finish a tool, message the group so Person 1 swaps the mock.
7. Every decision you make: one line in docs/ARCHITECTURE.md under "Open decisions".

CHECKPOINTS:
- Midday: end-to-end pipeline works with mocks + validator done.
- Mid-afternoon: real tools replacing mocks one by one, fine-tuning running.
- Evening: full demo run-through, fix what breaks, record demo.
