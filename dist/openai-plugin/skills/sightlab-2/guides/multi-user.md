# Multi-user studies

Sources: help.worldviz.com/sightlab multi-user-overview, multi-user-custom-experiments,
known-issues; `reference/sightlab.py` (2.9.3) `SightLabServer` and `SightLabClient`; the
shipped `SightLab_VR_Server.py` and `SightLab_VR_Client.py`.

When to read: two or more participants share one scene (a server PC and a client PC per
participant), or a researcher runs the session from one PC while others are in VR.

## The pair of scripts

`BlankProject` and `SampleProject` ship `SightLab_VR_Server.py` and `SightLab_VR_Client.py`
beside `SightLab_VR.py`. The frame is the single-user one with another class and runner:

```python
sightlab = sl.SightLabServer()        # client script: sl.SightLabClient()

def sightLabExperiment():
    yield viztask.waitEvent(EXPERIMENT_START)
    viz.callback(viz.getEventID('ResetPosition'), sightlab.resetViewPoint)
    for trial in range(sightlab.getTrialCount()):
        yield viztask.waitEvent(TRIAL_START)
        yield viztask.waitEvent(TRIAL_END)

viztask.schedule(sightlab.runServer)   # client script: sightlab.runClient
viztask.schedule(sightLabExperiment)
```

- The server drives the session: its GUI sets the environment, objects and trial start and
  end conditions (not "None" when converting a single-user GUI study), and every client
  follows. The server's default configuration is `hardwareconfig='Desktop Server'`.
- A client finds the server by computer name, chosen in its GUI or passed in code for an
  automatic start: `sl.SightLabClient(configpath='sightlab_configs/<client config>.stlb',
  hardwareconfig='Vive Focus Vision', server='LAB-PC-1')`.
- `sightlab.getClientName()` (client) is the name entered in that client's GUI.
- Each client's starting point is a `SIGHTLAB_START_POINT_<suffix>` node in the environment,
  with the suffix set per client (`setStartPointSuffix`; `guides/inspector.md`).
- Some documentation shows `viztask.waitEvent(EXPERIMENT_START)` without `yield`; it needs it.

## Custom events and shared state

- Shared state from the server: `sightlab.updateSharedServerData(data)` on the server sends
  it to every client; `sightlab.receiveSharedServerData()` on a client returns the latest.
- Custom events go over `viznet`, with the same ID defined in both scripts:
  ```python
  import viznet
  NEXT_STAGE = 'viznet:NEXT_STAGE'
  # server
  viznet.server.send(NEXT_STAGE, client=viz.net.getName())
  # client
  viz.callback(NEXT_STAGE, onNextStage)
  ```
  A client sends to everyone with `viznet.client.sendAll(NEXT_STAGE, client=viz.net.getName())`.
- Branch on the hardware with `sightlab.getConfig()` (the server is usually `'Desktop'` or
  `'Desktop Server'`).
- Voice chat between participants: the `mumble_server`, `mumble_port`, `mumble_password` and
  `mumble_channel` arguments on both classes; `toggleMute()`, `toggleDeafen()`.

## Gotchas

- Every client must have the same number of avatars, or the session fails with "list index
  out of range"; in GUI mode every client also needs the same environment models.
- Keep the server and client scripts in step: the same scene objects, event IDs and trial
  count.
- The desktop autopilot drives one script at a time; a server with its clients is checked
  by people on the real machines and network (`register/capabilities-and-custom-development.md`).

## Shipped examples

`Multi User ExamplesScripts` beside `ExampleScripts` (it is not in `examples/index.md`):
`Shared Data States`, `Gaze_Based_Interactions`, `Drawing_Multi_User`, `Presentation Mode`,
`Latency_Test`, `RatingScale_GUI` and others. Driving has its own pair
(`guides/driving.md`).
