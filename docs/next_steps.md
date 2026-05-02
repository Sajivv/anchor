# Next Steps

## Must Have Before Real Testing

1. Simulate disconnect behavior cleanly
- MARLIN should keep cached mission config
- queue outbound data while disconnected
- replay queued data on reconnect

2. Finalize scenario runs cleanly
- define when a run ends
- compute success/failure
- summarize event/command counts

3. Track intervention counts
- baseline vs `anchor_managed`
- manual operator actions per run

4. Add export-friendly summaries
- easy to turn runs into graphs/tables
- likely JSON or CSV-friendly summaries

## Nice to Have

- chat-driven mission config editing
- cleaner dashboard summaries for commands and node health
- more realistic mock Wi-Fi targets and battery changes

## Suggested Build Order

1. run finalization and per-run metrics
2. disconnect/reconnect validation
3. intervention counting
4. result export
5. graphs and paper results
