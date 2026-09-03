READ THIS FIRST (everyone), THEN YOUR OWN FILE
================================================

WHAT WE ARE BUILDING (the simple version)
-----------------------------------------
ISRO's problem: satellite images contain answers to important questions
(which villages are flooded, how much a city has grown, where forests were
cut). But today, only trained experts with GIS software can pull those
answers out. A district officer or a scientist without coding skills cannot
just ask "which areas are underwater?" and get an answer.

Our solution: a website where a user uploads 1 or 2 satellite images, types
a question in plain English, and gets back:
  1. a text answer
  2. the image with the evidence highlighted (boxes / colored regions)
  3. a confidence score
  4. a log showing exactly which AI models were used and how (judges grade this log)

Think of it like a hospital. The user talks to a receptionist (our "agent
controller"). The receptionist looks at what they brought (one image? two
dates? optical + radar?) and what they asked, then sends them to the right
specialist doctor (a VQA model, a change-detection model, etc.), collects
the specialist's report, and hands back one clear answer with proof.

The 3 types of input we must handle:
  1. ONE image           -> answer questions, describe it, or point at things in it
  2. TWO DATES same area -> say what changed and where
  3. OPTICAL + SAR pair  -> combine them (SAR is radar: sees through clouds
                            and at night, but looks like grey noise to
                            humans; optical is a normal photo). Together
                            they are more reliable than either alone.
                            This matters to ISRO because during monsoon
                            floods, clouds block optical images exactly when
                            answers are needed most.

WHAT IS MANDATORY (from the problem statement, we fail without these):
  [ ] Single-image VQA (answer questions about one image)
  [ ] One more single-image task: captioning OR grounding
  [ ] Change analysis from two dates
  [ ] Optical + SAR joint analysis
  [ ] At least ONE model fine-tuned on remote-sensing data (BigEarthNet)
      A stock ChatGPT-style model with no adaptation = disqualified
  [ ] The agent controller that picks tools automatically
  [ ] Working web app with evidence, confidence, execution log, downloadable report

HARD RULES FOR TODAY
--------------------
1. ZERO PAID APIs. No OpenAI key, no paid Anthropic key. Everything runs
   locally, on the 5070 Ti machine, or on free Colab/Kaggle GPUs.
   If you need an LLM for text work, use Ollama (free, local):
   https://ollama.com then `ollama pull qwen2.5:3b`
2. Bare minimum first. Every person's file has a "MINIMUM" and a "BETTER"
   section. Nobody starts BETTER until their MINIMUM works end to end.
3. Research is time-boxed to 1 hour. Then pick and build. A simple thing
   that runs beats an impressive thing that doesn't.
4. Never blocked. If you are waiting on someone, use the mock/fake version
   (they exist already) and keep moving.
5. One branch per person. Merge to main every 2-3 hours. Person 1 is merge
   master and resolves conflicts.
6. Never commit datasets or model weights (they are gitignored).
7. Every decision you make = one line in docs/ARCHITECTURE.md.

WHAT ALREADY EXISTS IN THE REPO (do not rebuild these)
------------------------------------------------------
- backend/tools/base.py ........ the contract every tool follows (Tool, ToolResult)
- backend/tools/mocks.py ....... 5 fake tools so the pipeline runs today
- backend/agent/controller.py .. working router (rules + optional local LLM)
- backend/agent/registry.py .... the tool menu, swap mock -> real here
- scripts/run_controller_demo.py runs 5 example queries end to end, TRY IT:
      PYTHONPATH=. python3 scripts/run_controller_demo.py
- docs/RESEARCH.md ............. links to every model/repo we shortlisted
- docs/ARCHITECTURE.md ......... decisions log + the API response shape

WHO DOES WHAT (one line each)
-----------------------------
Person 1: the receptionist. Owns routing, integration, and the final glue.
Person 2: the single-image specialist doctor (VQA + grounding/caption model).
Person 3: the "what changed between these two dates" specialist.
Person 4: image plumbing (read GeoTIFFs, detect SAR vs optical), the
          MANDATORY fine-tune, and the optical+SAR fusion tool. Has the 5070 Ti.
Person 5: the website, the evidence overlays, the downloadable report.

TIMELINE (be honest at checkpoints, say if you are behind)
----------------------------------------------------------
Hour 1:      everyone reads docs, 15-min call, lock contracts, start.
Midday:      pipeline runs with mocks + validator works + models chosen.
Mid-aftn:    real tools replacing mocks. Fine-tune running on the 5070 Ti.
Evening:     freeze features. Full demo run-through. Fix, record, prepare pitch.
