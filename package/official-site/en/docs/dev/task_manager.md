# Task Management Module Design Document

## 1. Overall Architecture

The task management module adopts a typical **Producer-Consumer** model, using the database (PostgreSQL) as a persistent task queue. The architecture mainly consists of the following three core components:

*   **Producer (TaskManager)**: Runs in the API service process, responsible for receiving user requests or system triggered events, generating tasks and writing them to the database.
*   **Task Queue (Database Table)**: The `Task` table acts as the queue, storing task type, status, priority, payload parameters, and other information.
*   **Consumer (TaskWorker)**: Runs in an independent background process, polling the database to get pending tasks, allocating resources for execution, and updating task status.

### Architecture Diagram

```mermaid
graph TD
    Client[Client/API] -->|Request Task| TM[TaskManager (Producer)]
    TM -->|Write (PENDING)| DB[(PostgreSQL Task Table)]
    
    TW[TaskWorker (Consumer)] -->|Poll| DB
    TW -->|Lock (PROCESSING)| DB
    
    subgraph Execution Pools
        TW -->|IO Task| ThreadPool[ThreadPoolExecutor]
        TW -->|CPU Task| ProcessPool[ProcessPoolExecutor]
    end
    
    ThreadPool -->|Result| ResultQueue[Result Queue]
    ProcessPool -->|Result| ResultQueue
    
    ResultQueue -->|Batch Update| DB
```

## 2. Producer & Consumer Coordination Mechanism

### Producer (TaskManager)
*   **Entry**: `package/server/app/service/task_manager.py`
*   **Responsibilities**:
    *   Receive task creation requests from business logic.
    *   Assign default priority based on task type.
    *   Support single or batch addition of tasks to the database, status initialized to `PENDING`.
    *   Manage system-level status (such as pausing certain categories of tasks).

### Consumer (TaskWorker)
*   **Entry**: `package/server/app/service/task_worker.py`
*   **Responsibilities**:
    *   **Polling**: `worker_loop` continuously checks for tasks with status `PENDING` in the database.
    *   **Locking**: When acquiring a task, immediately update status to `PROCESSING` to prevent multi-instance concurrent duplicate execution (although current design tends to single Worker instance).
    *   **Dispatching**: Submit tasks to the corresponding execution pool (process pool or thread pool) based on task type.
    *   **Result Handling**: Asynchronously wait for task completion, put results into memory queue `result_queue`.
    *   **Status Synchronization**: `result_loop` consumes results from the queue, batch updates task status in the database (success deletes, failure marks), and triggers subsequent associated tasks (such as triggering OCR and face recognition after image processing is complete).

## 3. Task Priority Implementation

Task priority is implemented through the `priority` field (integer) in the `Task` table, where larger values indicate higher priority.

*   **Default Priority**: The system defines a `DEFAULT_PRIORITIES` dictionary to automatically assign priorities to different types of tasks.
    *   `SCAN_FOLDER` (10): Highest priority, user-perceived scanning operation.
    *   `PROCESS_BASIC` (9): Basic processing.
    *   `GENERATE_THUMBNAIL` (8): Thumbnail generation, affecting frontend display.
    *   `EXTRACT_METADATA` (5): Metadata extraction.
    *   `RECOGNIZE_FACE` / `OCR` (1): Background AI analysis, low priority.
*   **Scheduling Logic**: When the consumer polls the database, it uses the `ORDER BY priority DESC, created_at ASC` statement to ensure high-priority tasks are taken out first, and tasks with the same priority are First In First Out (FIFO).

## 4. Task Status Management

Tasks transition between the following states during their lifecycle (defined in `TaskStatus` Enum):

1.  **PENDING**: Initial state, task created but not yet executed.
2.  **PROCESSING**: Executing. Worker sets this status immediately after taking out the task.
3.  **COMPLETED**: Execution successful. Usually, the record is deleted from the database after completion to keep the table lightweight.
4.  **FAILED**: Execution failed. Record retained in the database with error information for troubleshooting.

**Startup Recovery Mechanism**:
When the service starts, `TaskWorker` executes `_recover_unfinished_tasks`, resetting all tasks in `PROCESSING` status to `PENDING`. This is to handle cases where tasks are stuck in "Processing" due to service crash.

## 5. Task Allocation & Concurrency Model

### Execution Allocation
`TaskWorker` internally maintains two execution pools to optimize resource usage:
1.  **ProcessPoolExecutor**: Used for **CPU-intensive** tasks (such as image processing, thumbnail generation).
    *   Default Worker count: `os.cpu_count()`.
2.  **ThreadPoolExecutor**: Used for **IO-intensive** tasks (such as file scanning, network requests, OCR/AI model calls if GIL is released internally).
    *   Default Worker count: `max_concurrent_tasks * 2`.

### Concurrency Control
The system supports two concurrency modes, switched via the `Fast Mode` switch:

1.  **Normal Mode**:
    *   Strictly limit total concurrency (`config.task.max_concurrent_tasks`).
    *   Does not distinguish task types, as long as current active tasks do not reach the limit, new tasks can be pulled.

2.  **Fast Mode**:
    *   **Smart Scheduling**: Distinguishes `CPU_TASKS` and `IO_TASKS`.
    *   Allows CPU tasks to fill CPU cores.
    *   Additionally allows a certain number (e.g., 10) of IO tasks to execute concurrently.
    *   Purpose: Maximize hardware resource utilization, avoid blocking CPU calculation due to IO waiting.

## 6. Sequential Execution & Concurrent Execution

*   **Concurrent Execution**:
    *   Most peer tasks are executed concurrently. For example, thumbnail generation for 100 batch uploaded images will proceed simultaneously according to concurrency limits.
    *   Tasks of different types (such as scanning and face recognition) can also execute concurrently as long as resources allow and are not paused.

*   **Sequential Execution (Logical Order)**:
    *   Although the Worker itself pulls concurrently, business logic sequentiality is achieved through **Task Chaining**.
    *   **Example**: Image Import Flow
        1.  `PROCESS_BASIC` (Concurrent) -> Upon completion
        2.  Auto generate `EXTRACT_METADATA` (High Priority)
        3.  Auto generate `RECOGNIZE_FACE` (Low Priority)
        4.  Auto generate `OCR` (Low Priority)
    *   This mechanism ensures that AI analysis dependent on images is not executed before basic image info is entered into the database, and also achieves task decoupling.

## 7. Exception Handling Mechanism

1.  **Task Level Capture**: Each task execution is encapsulated in `execute_task_wrapper`, and any uncaught exceptions will be intercepted at this layer.
    *   After exception capture, task status is updated to `FAILED`, error stack is recorded to log, and error info saved to database.
2.  **Process Level Fault Tolerance**: Worker main loop contains broad `try-except` blocks, ensuring that severe errors of a single task or database connection jitter will not cause the entire Worker process to crash. Worker will sleep and retry after error.
3.  **Timeout Handling**: Relying on Future's timeout mechanism (currently code mainly relies on Python's concurrency library management).

## 8. Performance Optimization Strategies

1.  **Batch Processing**:
    *   **Batch Insert**: `add_tasks` uses `bulk_save_objects` to reduce database round trips.
    *   **Batch Update**: `result_loop` accumulates a certain number of results (or after timeout) to flush to database at once, reducing database write lock competition under high concurrency.
2.  **Resource Isolation**: Distinguish CPU and IO thread pools to prevent massive IO tasks from blocking CPU-intensive task execution channels.
3.  **Resource Auto Release**:
    *   Worker has idle detection mechanism. If queue is idle for more than 30 seconds, thread pool and process pool will be automatically closed to release system memory and handle resources, and rebuilt when new tasks arrive.
4.  **Fast Mode**: Dynamically adjust concurrency limit to maximize throughput based on task type characteristics (CPU vs IO).
5.  **Delete on Completion**: Successful tasks are directly deleted from database to prevent `Task` table from infinite expansion affecting query performance.
