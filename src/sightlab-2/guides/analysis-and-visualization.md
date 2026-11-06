# Analysis and visualisation

Sources: help.worldviz.com/sightlab ai-data-analysis, additional-visual-analytics, sightlab-dashboard; the earlier assistant's `visualization_sample.py`.

When to read: the researcher asks what is in the data, wants charts, or wants an analysis
script beside the experiment.

## The files

`rules/gaze-objects-and-data.md` lists what a session writes. For analysis the two that
matter most: the per-trial **summary** (one row per registered object per trial, with dwell,
fixation and timing columns plus any custom columns) and the per-frame **trial data**. Both are
plain CSV with a header row; `pandas.read_csv` reads them directly. Participant and date are
in the folder and file names.

## Charts without code

In the Dashboard, a project's detail page offers "Generate Barchart" (grouped bars of total
and average dwell time per object from a summary CSV; no AI) and "Generate Visualizations"
(an LLM, local through Ollama or OpenAI or Anthropic, proposes a set of charts for a CSV).

The scripts behind them sit in the projects folder (`Documents\Sightlab2`) and can be run
directly for the researcher:

- `generate_barchart.py <summary.csv> [--data-dir DIR]`: one PNG per `Label` (condition) in a
  `Charts/` folder beside the CSV or under `DIR`; skips the `ENTIRE_SCENE` row; needs pandas
  and matplotlib, no AI.
- `generate_visualizations.py <csv>`: the LLM route; the default is a local Gemma model
  through Ollama, `-p openai` or `-p claude` use an API key the researcher has set.

## Shipped analysis scripts

- `examples/Barchart`: a matplotlib bar chart of gaze on objects of interest; the simplest
  starting point for a custom chart.
- `examples/VisualizationTools`: `barchart_histogram.py` (compare a condition column, default
  `Label`, with a measure, default `Fixation Count`, for one summary file),
  `barchart_histogram_entireFolder.py` (all summaries in a data folder),
  `comparison_label_TTFF.py` (condition against time to first fixation), `boxPlot_2_by_3.py`,
  Plotly charts of views and walk paths, and a real-time plot example.
- `examples/AI_Data_Analysis`: natural-language questions over one CSV or a whole data tree
  through OpenAI or an offline Ollama model (`AI_Data_Analysis.py`,
  `AI_Data_Analysis_Entire_Folder.py`), plus video-frame tools that detect what was looked at
  in a recording. These need an API key or a local model set up by the researcher.

To adapt a shipped script: change the code between where it loads the data frame and where
it saves the figure; keep the loading and saving.

## Writing an analysis script for a study

- Put it in an `Analysis/` folder beside the experiment so the Dashboard shows it.
- Read every `*_experiment_summary.csv` under `data/`, concatenate, group by `Label` (or the
  custom condition column) and by `ROI/Object`.
- Measures worth a first chart: `Total Dwell Time (secs)`, `Fixation Count`,
  `Time to First Fixation (secs)`, and any custom column the brief defined.
- Save figures as PNG beside the script with the date in the name; never write into
  `data/`.

## Gotchas

- Column names contain spaces and parentheses; quote them exactly.
- Rows for objects that were never looked at still exist, with zeros and a time to first
  fixation of `-1`; do not drop them silently, and leave the `-1` out of any average.
- Fixation counts depend on the fixation thresholds in force when the data was recorded
  (`setFixationSaccadeThresholds`; defaults 1° dispersion, 0.1 s duration); compare studies
  only at the same thresholds.
- A study run with `oldHeaders=True` writes the older column names (`Object`, `View Count`,
  `Total Dwell Time`, `Avg Time`); read the header row before assuming a name.
- Per-frame files are large; aggregate per trial before plotting.
- The autopilot's `.autopilot/runs/` folders contain test data, not research data; exclude
  them.
