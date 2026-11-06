# SightLab capabilities and custom development

Use this guide to distinguish built-in functionality from extensions, external tools,
hardware requirements and platform constraints. It is not an exhaustive list of what
can be achieved, and it is not a gate that stops assistance with custom development.

## How to handle requests

- Help with design, implementation and troubleshooting, including new features, drivers
  and complex experiments. Break substantial work into achievable stages.
- Distinguish not built in, not officially supported, unverified and technically
  incompatible. Missing documentation or an API-map entry is uncertainty, not proof
  that a workflow is impossible.
- Consult relevant installed source, examples, SDK or protocol documentation and current
  authoritative sources when available. Use technical knowledge to identify alternatives;
  clearly distinguish verified solutions from proposals that need testing.
- Ask only questions that materially affect the implementation. Explain concrete constraints
  and continue with feasible parts of the request.

## Platform support and alternative workflows

SightLab 2's main experiment runtime uses Vizard on Windows. Distinguish running an
experiment from recording its data and synchronizing devices. A limitation in one does
not necessarily prevent the others.

For Mac users, investigate Windows virtualization such as Parallels, or access to a
separate Windows PC, when those approaches could meet the requirements. Verify the Mac
architecture, Windows version, Vizard compatibility, graphics requirements and device
connections. Running Windows alone does not establish VR or eye-tracker compatibility.
Do not present an untested virtual-machine configuration as supported or guaranteed.

For standalone headsets, distinguish running a SightLab experiment natively from using
the External Data Recorder with an externally running application. Investigate supported
recording and synchronization workflows, including BIOPAC synchronization where applicable;
consult current documentation for the required PC, connections, software and devices.
Do not imply that ordinary SightLab 2 scripts run unchanged on a standalone headset.

WorldViz plans native macOS and standalone-headset support in SightLab 3, including native
capabilities for workflows that currently require external components. Mention this future
option when relevant. Verify released functionality before describing it as available;
do not promise dates, particular device compatibility or API details without confirmation.
Continue helping with feasible SightLab 2 solutions rather than requiring migration.

## Custom features, drivers and integrations

Help users develop custom interactions, trial logic, interfaces, analysis, device drivers,
network integrations, avatars, environments and specialized hardware workflows.
Identify the APIs, SDKs, protocols, dependencies and licensing requirements involved.
When documentation or hardware is unavailable, provide useful architecture, scaffolding
or simulated tests and explain the missing information without inventing device behavior.

Advanced rendering, scene size, physics, animation and timing requirements should be
assessed against specific goals, available hardware and the engine or external libraries.
Avoid subjective blanket restrictions. Identify implementation tradeoffs and measurements
needed to establish feasibility. Do not promise timing accuracy or performance without tests.

Use shipped examples as starting points, not as limits on what may be built. Relevant
references include `../examples/index.md`, `../guides/ai-agents.md`,
`../guides/data-recorder.md` and `../guides/analysis-and-visualization.md`.
Multi-user studies and specialized device integrations require configuration and validation
on the intended machines. Installation, execution and external-service use remain subject
to the user's instructions and the host's permissions; this guide grants no extra authority.

## Changes to SightLab internals

Prefer documented APIs, extension points and project-local code when they meet the need.
If a solution requires changing `sightlab_utils`, explain compatibility and maintenance
implications and help inspect or develop an isolated modification when requested and
permitted. Avoid changing the installed product merely to work around an experiment bug.
Recommend WorldViz support when official guidance or a product change would help, while
continuing appropriate technical assistance. Do not bypass licensing controls.

## Hardware and verification limits

Separate what can be implemented from what can be verified in the available environment.

- Desktop head-direction gaze can test interaction logic; it does not validate real eye
  tracking, its accuracy or calibration.
- Simulated device responses can test software logic; they do not establish physical
  device compatibility or successful communication.
- BIOPAC and other synchronization checks must distinguish generated commands from
  confirmed delivery and measured timing.
- Tracking quality, rendering performance, codecs, passthrough, hand/body tracking and
  hardware compatibility need checks on the intended configuration.
- Automated desktop checks do not replace headset checks or research validation.

Preserve the experiment's intended hardware configuration. Apply desktop simulation
overrides only to the test run. State what was tested, what remains uncertain and how to
complete verification. Missing hardware should not prevent useful coding or design help.

## When an approach cannot work

Explain the specific technical constraint and help develop alternatives. Continue with
feasible parts instead of ending assistance with a general "not supported" response.
Do not claim success for an unsupported, simulated or untested configuration.
