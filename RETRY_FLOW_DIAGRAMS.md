# Retry and Failure Handling Flow Diagram

## Overview Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Upload Configuration File                   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Create Ingestion Run │
                    │  Status: PENDING      │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Store File (S3/FS)  │
                    │   Status: STORED      │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Enqueue Parse Task   │
                    │  (Celery Worker)      │
                    └───────────┬───────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                     RETRY & FAILURE HANDLING                      │
│                      (Smart Error Classification)                 │
└───────────────────────────────────────────────────────────────────┘
```

## Detailed Retry Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Parse Task Started                        │
│  • Update status: PARSING                                        │
│  • Set started_at timestamp                                      │
│  • Record task_id                                                │
│  • Initialize heartbeat                                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Retrieve Archive     │
                    │  from Storage         │
                    └───────────┬───────────┘
                                │
                    ┌───────────┴────────────┐
                    │                        │
                    ▼                        ▼
        ┌─────────────────┐      ┌──────────────────┐
        │  Success        │      │  Storage Error   │
        └────────┬────────┘      └────────┬─────────┘
                 │                        │
                 │                        ▼
                 │               ┌──────────────────┐
                 │               │ TransientError   │
                 │               │ Retry in 60s     │
                 │               └────────┬─────────┘
                 │                        │
                 ▼                        ▼
        ┌─────────────────┐      ┌──────────────────┐
        │ Extract Archive │      │ Retry Attempt 1  │
        │                 │      │ Countdown: 60s   │
        └────────┬────────┘      └────────┬─────────┘
                 │                        │
     ┌───────────┴────────────┐           │
     │                        │           │
     ▼                        ▼           │
┌─────────┐         ┌──────────────────┐ │
│ Valid   │         │ Corrupted/       │ │
│ Archive │         │ Invalid Format   │ │
└────┬────┘         └────────┬─────────┘ │
     │                       │           │
     │                       ▼           │
     │              ┌──────────────────┐ │
     │              │ PermanentError   │ │
     │              │ NO RETRY         │ │
     │              │ Status: FAILED   │ │
     │              └──────────────────┘ │
     │                                   │
     ▼                                   ▼
┌─────────────────┐          ┌──────────────────┐
│ Parse .conf     │          │ Retry Attempt 2  │
│ Files           │          │ Countdown: 180s  │
│ • Update        │          └────────┬─────────┘
│   heartbeat     │                   │
│   every 30s     │                   │
└────────┬────────┘                   │
         │                            ▼
         │                   ┌──────────────────┐
         │                   │ Retry Attempt 3  │
         │                   │ Countdown: 600s  │
         │                   └────────┬─────────┘
         │                            │
         │                            ▼
         │                   ┌──────────────────┐
         │                   │ Max Retries      │
         │                   │ Exhausted        │
         │                   │ Status: FAILED   │
         │                   └──────────────────┘
         │
         ▼
┌─────────────────┐
│ Create Stanzas  │
│ • Check for     │
│   duplicates    │
│   (idempotent)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Commit to DB    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update Run      │
│ • Status:       │
│   COMPLETE      │
│ • completed_at  │
│ • metrics       │
└─────────────────┘
```

## Error Classification Decision Tree

```
                    ┌─────────────┐
                    │   Error     │
                    │  Occurred   │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
    ┌─────────────────┐      ┌─────────────────┐
    │ Data/Input      │      │ Infrastructure  │
    │ Related?        │      │ Related?        │
    └────────┬────────┘      └────────┬────────┘
             │                        │
             ▼                        ▼
    ┌─────────────────┐      ┌─────────────────┐
    │ PermanentError  │      │ TransientError  │
    │                 │      │                 │
    │ Examples:       │      │ Examples:       │
    │ • Malformed     │      │ • Network       │
    │   archive       │      │   timeout       │
    │ • No files      │      │ • DB conn       │
    │ • Invalid       │      │   error         │
    │   format        │      │ • Storage       │
    │                 │      │   unavailable   │
    └────────┬────────┘      └────────┬────────┘
             │                        │
             ▼                        ▼
    ┌─────────────────┐      ┌─────────────────┐
    │ NO RETRY        │      │ RETRY WITH      │
    │                 │      │ BACKOFF         │
    │ • Mark FAILED   │      │                 │
    │ • Log error     │      │ • 60s delay     │
    │ • Store trace   │      │ • 180s delay    │
    │                 │      │ • 600s delay    │
    │                 │      │ • Max 3 tries   │
    └─────────────────┘      └─────────────────┘
```

## Idempotency Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Task Retry Scenario                           │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Check Run Status     │
                    └───────────┬───────────┘
                                │
                    ┌───────────┴────────────┐
                    │                        │
                    ▼                        ▼
        ┌─────────────────┐      ┌──────────────────┐
        │ Status:         │      │ Status:          │
        │ COMPLETE        │      │ PARSING          │
        └────────┬────────┘      └────────┬─────────┘
                 │                        │
                 ▼                        ▼
        ┌─────────────────┐      ┌──────────────────┐
        │ Return Early    │      │ Process Files    │
        │ already_        │      └────────┬─────────┘
        │ completed       │               │
        └─────────────────┘               │
                                          ▼
                              ┌──────────────────────┐
                              │ For Each Stanza:     │
                              │ Check if exists      │
                              │ by:                  │
                              │ • run_id             │
                              │ • file_id            │
                              │ • name               │
                              │ • source_path        │
                              └─────────┬────────────┘
                                        │
                            ┌───────────┴────────────┐
                            │                        │
                            ▼                        ▼
                ┌─────────────────┐      ┌──────────────────┐
                │ Already Exists  │      │ New Stanza       │
                │ SKIP            │      │ INSERT           │
                └─────────────────┘      └──────────────────┘
                                                    │
                                                    ▼
                                        ┌──────────────────┐
                                        │ No Duplicates!   │
                                        │ Safe Retry       │
                                        └──────────────────┘
```

## Heartbeat Mechanism

```
┌─────────────────────────────────────────────────────────────────┐
│                    Long-Running Task                             │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Task Starts          │
                    │  last_heartbeat = now │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Process File 1       │
                    │  (Check heartbeat)    │
                    └───────────┬───────────┘
                                │
                    ┌───────────┴────────────┐
                    │                        │
                    ▼                        ▼
        ┌─────────────────┐      ┌──────────────────┐
        │ >30s since      │      │ <30s since       │
        │ last beat?      │      │ last beat?       │
        └────────┬────────┘      └────────┬─────────┘
                 │                        │
                 ▼                        │
        ┌─────────────────┐              │
        │ Update          │              │
        │ last_heartbeat  │              │
        │ in DB           │              │
        └────────┬────────┘              │
                 │                        │
                 └────────────┬───────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Process File 2   │
                    │ (Check again)    │
                    └────────┬─────────┘
                             │
                             ▼
                          ... continues ...
                             │
                             ▼
                    ┌──────────────────┐
                    │ Task Completes   │
                    │ completed_at =   │
                    │ now              │
                    └──────────────────┘
```

## Metrics Collection Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Task Execution                              │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                    ┌───────────┴────────────┐
                    │                        │
                    ▼                        ▼
        ┌─────────────────┐      ┌──────────────────┐
        │ Success Path    │      │ Failure Path     │
        └────────┬────────┘      └────────┬─────────┘
                 │                        │
                 ▼                        ▼
    ┌────────────────────┐    ┌─────────────────────┐
    │ Collect Metrics:   │    │ Collect Metrics:    │
    │ • files_parsed     │    │ • duration_seconds  │
    │ • stanzas_created  │    │ • retry_count       │
    │ • duration_seconds │    │ • error_type        │
    │ • parse_errors     │    │                     │
    │ • retry_count      │    │                     │
    └────────┬───────────┘    └─────────┬───────────┘
             │                          │
             ▼                          ▼
    ┌────────────────────┐    ┌─────────────────────┐
    │ Store in           │    │ Store in            │
    │ run.metrics JSON   │    │ run.metrics JSON    │
    └────────┬───────────┘    └─────────┬───────────┘
             │                          │
             └────────────┬─────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │ Available via:        │
              │ • /v1/worker/runs/    │
              │   {id}/status         │
              │ • /v1/worker/metrics  │
              └───────────────────────┘
```

## API Query Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              Developer/Monitoring Query                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                    ┌───────────┴────────────┐
                    │                        │
                    ▼                        ▼
        ┌─────────────────┐      ┌──────────────────┐
        │ GET /v1/worker/ │      │ GET /v1/worker/  │
        │ runs/{id}/      │      │ metrics          │
        │ status          │      │                  │
        └────────┬────────┘      └────────┬─────────┘
                 │                        │
                 ▼                        ▼
    ┌────────────────────┐    ┌─────────────────────┐
    │ Returns:           │    │ Returns:            │
    │ • status           │    │ • status_counts     │
    │ • task_id          │    │ • retry_stats       │
    │ • retry_count      │    │ • avg_duration      │
    │ • error_message    │    │ • recent_failures   │
    │ • error_traceback  │    │                     │
    │ • timestamps       │    │                     │
    │ • metrics          │    │                     │
    └────────────────────┘    └─────────────────────┘
```
