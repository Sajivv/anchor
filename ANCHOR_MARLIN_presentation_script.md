# ANCHOR / MARLIN Presentation Script

## Slide 1: ANCHOR / MARLIN

Today I am presenting my autonomic computing project, ANCHOR and MARLIN. The goal of this project was to explore whether an LLM-supported autonomic manager could reduce the amount of human monitoring needed for a remote maritime sensing node.

The basic idea is that if a device is floating in the water, I cannot treat it like a normal server or laptop. I may not be able to physically reach it, it may have weak connectivity, and it may need to make decisions about battery, sensing, and mission state on its own.

So this project became both a software architecture project and an experiment. I started with the class concept of autonomic computing, translated it into a codebase, tested it with controlled mock scenarios, and then ran a real field test on the water in Tacoma's Foss Harbor.

## Slide 2: The problem: remote maritime devices are hard to manage

The problem I focused on is remote maritime monitoring. A floating sensor node is different from a system in a data center. If something goes wrong, an operator cannot just walk over and restart it.

That creates a few challenges. First, physical access is limited. Second, connectivity can be intermittent or low bandwidth. Third, power matters a lot because the node may be running from a battery. Finally, constant human monitoring does not scale well.

The research question I used was: can an autonomic manager absorb some of the routine decisions that a human operator would normally have to make?

In this project, that meant decisions like whether the node had entered a geofence, whether it should start Wi-Fi scanning, whether it should reduce activity because of low battery, and how it should behave when disconnected from the base station.

## Slide 3: Two project roles: MARLIN and ANCHOR

There are two main roles in the system.

MARLIN stands for Maritime Autonomous Remote Linked Intelligence Node. It represents the remote sensor node. In the long-term hardware concept, a MARLIN would be a buoy-like platform with a Raspberry Pi or similar Linux computer, GPS, temperature and humidity sensing, a Wi-Fi interface, a LoRa radio, and a battery-backed enclosure.

ANCHOR stands for Autonomous Network for Coastal Hardware and Operational Reporting. ANCHOR is the base-station manager. It receives telemetry, stores fleet state, provides the dashboard, invokes the reasoning engine, and sends validated commands back to MARLIN.

The important split is that MARLIN stays close to the environment and handles local policy, while ANCHOR handles higher-order reasoning and operator visibility.

## Slide 4: The original idea had to change once it became code

The original idea was more decentralized. I initially imagined each MARLIN running a full autonomic manager onboard, including the reasoning component.

That sounded appealing conceptually, but as I started building, the implementation forced a more realistic design. Running an LLM-based agent directly on an edge device introduces compute limits, network dependency, and safety concerns.

Earlier in the project, I was thinking about this in terms of Claude Code-style agentic coding behavior. The important idea was that a coding agent can inspect a repository, reason across files, run commands, and iterate on a goal. In the final prototype, I used Codex as the reasoning tool behind ANCHOR.

The resulting architecture became hybrid. MARLIN keeps local autonomy for geofence detection, battery protection, mode switching, and cached mission state. ANCHOR uses Codex for analyze-and-plan behavior, but Codex is not allowed to directly run arbitrary commands on the MARLIN node.

## Slide 5: Turning the idea into a codebase

Once the architecture became clearer, I organized the prototype into four main areas.

The `shared` layer defines the message contracts: mission configs, commands, snapshots, events, and command responses.

The `marlin` runtime handles local sensing, building snapshots, evaluating mission policy, running Wi-Fi tasks, storing local state, and uploading messages.

The `anchor` runtime handles the API server, fleet state, mission management, command generation, policy validation, and the reasoning engine.

The `web` layer is the operator dashboard. It shows the MARLIN fleet, map position, recent messages, reasoning output, commands, and chat.

Even though this is one repository, ANCHOR and MARLIN are conceptually separate programs. At runtime they communicate through structured HTTP and JSON messages.

## Slide 6: The most important design decision: bound the autonomy

The biggest design decision was bounding the autonomy.

Claude Code and Codex are powerful because they can reason over code and system state. They can plan multi-step work, inspect files, run commands, and explain results. That made Codex useful for ANCHOR because the base station needed more than a simple rule engine.

But that capability creates a safety issue. Just because an agent can run commands does not mean it should have unrestricted control over a remote maritime node.

So the final design uses a constrained command model. MARLIN sends events and snapshots to ANCHOR. ANCHOR builds a structured context packet and invokes Codex. Codex returns recommended actions, but those actions have to pass policy validation. Only then does ANCHOR send a structured command to MARLIN.

MARLIN then executes the command through predefined handlers. This keeps the LLM in the analyze-and-plan part of the loop, while execution remains bounded and auditable.

## Slide 7: The build surfaced practical technical challenges

The project became much more interesting once I started replacing simple mock behavior with more realistic behavior.

One challenge was GPS. During field testing, MARLIN needed to consume a live GPS stream from the mobile hotspot. That required handling live NMEA data instead of just using fixed coordinates.

Another challenge was Wi-Fi scanning. The early version could use mocked scan data, but the field version needed to call the local wireless interface on Linux and return nearby networks to ANCHOR.

Battery state also mattered. In the field test, the Ubuntu laptop battery acted as the MARLIN battery source, so the system could enter low-power behavior based on a real battery percentage.

The disconnect and command-failure scenarios were also useful because they showed the limits of the prototype. Disconnect recovery worked after connectivity returned, but the system does not yet rebuild the network connection by itself. Command-failure observability was weaker than the geofence and battery behavior.

## Slide 8: Running the prototype locally

For controlled testing, I ran the stack locally and used the ANCHOR dashboard to trigger scenarios.

The basic command was:

`python3 scripts/run_stack.py --reset`

That reset the local state, started ANCHOR, started MARLIN, and let me run repeatable tests from the dashboard.

The important part was testing each scenario in two modes: baseline and ANCHOR-managed. In baseline mode, MARLIN could report telemetry, but the operator had to interpret the situation and decide what to do. In ANCHOR-managed mode, MARLIN and ANCHOR together handled more of the response automatically.

That gave me structured run data for low battery, geofence entry, target Wi-Fi detection, disconnect, and command failure.

## Slide 9: Water experiment: Tacoma Foss Harbor

This is the field test portion of the project.

For the water experiment, I ran ANCHOR on my MacBook as the base station and MARLIN on an Ubuntu laptop as the remote node. Both were connected through a mobile hotspot. The hotspot also provided live GPS data to MARLIN.

The goal was to simulate a MARLIN floating through a channel into and out of a geofence. While outside the geofence, MARLIN stayed in passive mode and reported GPS snapshots. When it entered the geofence, MARLIN was supposed to switch to active mode and ANCHOR was supposed to reason about what to do next.

This is where I would like to show the phone video from the boat test.

[Play field-test video here.]

As you watch it, the main thing to notice is that this is no longer just a local mock run. The system is operating with real movement, real GPS, real laptop battery, and real Wi-Fi observations.

## Slide 10: What happened on the water

During the field test, MARLIN started outside the geofence in passive mode. It reported live GPS snapshots back to ANCHOR about once per minute.

When the boat entered the geofence, MARLIN's local mission evaluator detected the position change and switched the node into active mode. That triggered ANCHOR's reasoning path, and Codex recommended Wi-Fi scanning.

Wi-Fi scanning began, and nearby wireless networks appeared in the ANCHOR interface. Later, when the boat exited the geofence, MARLIN returned to passive mode and scanning stopped.

The battery behavior was also important. When the Ubuntu laptop reached 20 percent battery, MARLIN entered low-power mode. Later, when the boat reentered the geofence at around 6 percent battery, scanning did not restart. That showed that low-power protection could override mission activity.

So the field test validated live GPS reporting, geofence-triggered mode changes, Wi-Fi scanning, and low-battery suppression in a real maritime setting.

## Slide 11: Controlled mock tests filled out the scenario matrix

The field test was the strongest real-world validation, but I still needed controlled test data for the paper.

I ran five scenarios in baseline and ANCHOR-managed modes: low battery, geofence entry, target Wi-Fi detection, disconnect, and command failure.

The strongest improvements were low battery, geofence entry, and target Wi-Fi detection. In those cases, ANCHOR-managed mode reduced operator intervention from one intervention to zero.

Disconnect was a little more nuanced. The current prototype does not autonomously recreate a lost network connection. What it does show is graceful local operation and recovery after connectivity returns.

Command failure was the weakest scenario. In both baseline and ANCHOR-managed mode, I still had to manually mark the run as failed because the failed command response did not reliably surface back into the experiment harness.

That limitation is useful because it shows where the prototype is still incomplete.

## Slide 12: LLM usage stayed small in the prototype

Since ANCHOR uses Codex as part of the analyze-and-plan loop, I also looked at LLM usage and cost.

For the exported usage window, from April 5 through May 5, the project recorded 16 model requests using `gpt-5.3-codex`.

Those requests used 4,995 input tokens and 3,028 output tokens, for a total of 8,023 tokens. The corresponding cost export showed a total cost of about five cents.

I do not want to overstate that result because this was a prototype, not a full fleet deployment. But it does show that, at this small scale, the LLM reasoning layer did not require a large amount of usage or cost.

In a larger deployment, cost would depend on the number of nodes, how often reasoning is triggered, and how much context is sent to the model.

## Slide 13: Result: 80% fewer operator interventions

The main quantitative result is that ANCHOR-managed mode reduced operator interventions from five in the baseline runs to one in the managed runs.

Using the reduction formula, that is an 80 percent reduction in human monitoring effort, which exceeds the original 65 percent target.

The strongest evidence came from geofence behavior, low-battery behavior, and the live field test. The prototype showed that MARLIN could enforce local policy and that ANCHOR could add reasoning and coordination from the base station.

The main limitation is command failure. The system still needs better failure reporting and recovery before I would call that part fully self-healing.

Overall, my conclusion is that the fully decentralized vision was too ambitious for this prototype, but the hybrid architecture worked. It preserved local autonomy where it mattered most and used Codex in a bounded way for higher-order reasoning.

That makes ANCHOR and MARLIN a practical demonstration of autonomic computing ideas applied to a remote maritime sensing problem.
