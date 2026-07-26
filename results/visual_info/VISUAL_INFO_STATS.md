# Visual-Information Annotation — TimeWarp

Dataset: [`anonymous-submission-1827/timewarp`](https://huggingface.co/datasets/anonymous-submission-1827/timewarp) — 231 tasks (128 train / 103 test).

Each task's goal description was classified by how much **visual information** (rendered-pixel content: images, colors, icons, layout geometry — as opposed to text available in the DOM/accessibility tree) is needed to complete it. Method: two independent LLM sub-agent annotators per task (rubric-literal and text-only-agent simulation framings) with a third sub-agent adjudicating disagreements; see `PLAN.md`. Full per-task votes and rationales: `annotations.json`.

## Overall distribution

| Category | Tasks | Share |
|---|---:|---:|
| Required | 8 | 3.5% |
| Helpful | 51 | 22.1% |
| Irrelevant | 172 | 74.5% |
| **Total** | **231** | 100.0% |

## By split

| Split | Tasks | Required | Helpful | Irrelevant |
|---|---:|---:|---:|---:|
| train | 128 | 4 (3.1%) | 30 (23.4%) | 94 (73.4%) |
| test | 103 | 4 (3.9%) | 21 (20.4%) | 78 (75.7%) |

## By environment

| Environment | Tasks | Required | Helpful | Irrelevant |
|---|---:|---:|---:|---:|
| Wiki | 70 | 0 (0.0%) | 20 (28.6%) | 50 (71.4%) |
| News | 47 | 0 (0.0%) | 8 (17.0%) | 39 (83.0%) |
| Shop | 64 | 8 (12.5%) | 16 (25.0%) | 40 (62.5%) |
| Multi | 50 | 0 (0.0%) | 7 (14.0%) | 43 (86.0%) |

## Annotation reliability

- Inter-annotator agreement: **209/231** tasks (90.5%), Cohen's κ = **0.759**
- Decisions: 209 by agreement, 22 adjudicated.

## Tasks labeled Required

| Id | Env | Goal |
|---|---|---|
| train-092 | Shop | What is the focal length range in millimeters of the stock lens on the Canon PowerShot S3 camera product pi... |
| train-093 | Shop | How many of the color options for the Nautica headphones have two distinct visible colors? |
| train-094 | Shop | What's the color of the Rifle Scope Mount Camera Adapter in the product picture? |
| train-096 | Shop | What's written on the body of the 20x50 Binoculars? If there are multiple 20x50 Binoculars, pick the first ... |
| test-071 | Shop | What color is most prominent on the exterior body of the navy and yellow Nautica headphones? |
| test-072 | Shop | What is the color of the TASYL USB lightning camera adapter? |
| test-073 | Shop | Search for the word "camera." Among the search results, which of the following colors is most common in the... |
| test-074 | Shop | Is there a remote in the product picture of the 4-Channel Wireless Bluetooth Power Amplifier? |
