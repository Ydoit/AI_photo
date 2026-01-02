# 任务管理模块设计文档

## 1. 整体架构

任务管理模块采用典型的 **生产者-消费者 (Producer-Consumer)** 模型，利用数据库（PostgreSQL）作为持久化任务队列。该架构主要包含以下三个核心组件：

*   **生产者 (TaskManager)**: 运行在 API 服务进程中，负责接收用户请求或系统触发的事件，生成任务并写入数据库。
*   **任务队列 (Database Table)**: `Task` 表充当队列，存储任务的类型、状态、优先级、负载参数等信息。
*   **消费者 (TaskWorker)**: 运行在独立的后台进程中，轮询数据库获取待处理任务，分配资源执行，并更新任务状态。

### 架构图示

```mermaid
graph TD
    Client[客户端/API] -->|请求任务| TM[TaskManager (Producer)]
    TM -->|写入 (PENDING)| DB[(PostgreSQL Task Table)]
    
    TW[TaskWorker (Consumer)] -->|轮询 (Poll)| DB
    TW -->|锁定 (PROCESSING)| DB
    
    subgraph Execution Pools
        TW -->|IO任务| ThreadPool[ThreadPoolExecutor]
        TW -->|CPU任务| ProcessPool[ProcessPoolExecutor]
    end
    
    ThreadPool -->|结果| ResultQueue[Result Queue]
    ProcessPool -->|结果| ResultQueue
    
    ResultQueue -->|批处理更新| DB
```

## 2. 生产者与消费者协同机制

### 生产者 (TaskManager)
*   **入口**: `package/server/app/service/task_manager.py`
*   **职责**:
    *   接收业务逻辑的任务创建请求。
    *   根据任务类型分配默认优先级。
    *   支持单个或批量添加任务到数据库，状态初始化为 `PENDING`。
    *   管理系统级状态（如暂停某些类别的任务）。

### 消费者 (TaskWorker)
*   **入口**: `package/server/app/service/task_worker.py`
*   **职责**:
    *   **轮询 (Polling)**: `worker_loop` 持续检查数据库中状态为 `PENDING` 的任务。
    *   **锁定 (Locking)**: 获取任务时，立即将状态更新为 `PROCESSING`，防止多实例并发重复执行（尽管当前设计倾向于单 Worker 实例）。
    *   **分发 (Dispatching)**: 根据任务类型将任务提交给相应的执行池（进程池或线程池）。
    *   **结果处理**: 异步等待任务完成，将结果放入内存队列 `result_queue`。
    *   **状态同步**: `result_loop` 从队列消费结果，批量更新数据库中的任务状态（成功删除，失败标记），并触发后续关联任务（如图片处理完成后触发 OCR 和人脸识别）。

## 3. 任务优先级实现

任务优先级通过 `Task` 表中的 `priority` 字段（整数）实现，数值越大优先级越高。

*   **默认优先级**: 系统定义了 `DEFAULT_PRIORITIES` 字典，自动为不同类型的任务分配优先级。
    *   `SCAN_FOLDER` (10): 最高优先级，用户感知的扫描操作。
    *   `PROCESS_BASIC` (9): 基础处理。
    *   `GENERATE_THUMBNAIL` (8): 缩略图生成，影响前端展示。
    *   `EXTRACT_METADATA` (5): 元数据提取。
    *   `RECOGNIZE_FACE` / `OCR` (1): 后台AI分析，低优先级。
*   **调度逻辑**: 消费者在轮询数据库时，使用 `ORDER BY priority DESC, created_at ASC` 语句，确保高优先级任务先被取出，同优先级任务先进先出 (FIFO)。

## 4. 任务状态管理

任务在其生命周期中会在以下状态间流转（定义在 `TaskStatus` 枚举中）：

1.  **PENDING**: 初始状态，任务已创建但未被执行。
2.  **PROCESSING**: 正在执行中。Worker 取出任务后立即设置此状态。
3.  **COMPLETED**: 执行成功。通常在完成后会从数据库中删除记录，以保持表轻量。
4.  **FAILED**: 执行出错。记录保留在数据库中，并附带错误信息供排查。

**启动恢复机制**:
服务启动时，`TaskWorker` 会执行 `_recover_unfinished_tasks`，将所有处于 `PROCESSING` 状态的任务重置为 `PENDING`。这是为了处理服务意外崩溃导致任务卡在“处理中”的情况。

## 5. 任务分配与并发模型

### 执行分配
`TaskWorker` 内部维护了两种执行池来优化资源使用：
1.  **ProcessPoolExecutor**: 用于 **CPU 密集型** 任务（如图片处理、缩略图生成）。
    *   默认 Worker 数：`os.cpu_count()`。
2.  **ThreadPoolExecutor**: 用于 **IO 密集型** 任务（如文件扫描、网络请求、OCR/AI 模型调用如果内部已释放 GIL）。
    *   默认 Worker 数：`max_concurrent_tasks * 2`。

### 并发控制
系统支持两种并发模式，通过 `Fast Mode` 开关切换：

1.  **普通模式 (Normal Mode)**:
    *   严格限制总并发数 (`config.task.max_concurrent_tasks`)。
    *   不区分任务类型，只要当前活跃任务数未达上限，即可拉取新任务。

2.  **极速模式 (Fast Mode)**:
    *   **智能调度**: 区分 `CPU_TASKS` 和 `IO_TASKS`。
    *   允许 CPU 任务跑满 CPU 核心数。
    *   额外允许一定数量（如 10 个）的 IO 任务并发执行。
    *   目的：最大化利用硬件资源，避免因 IO 等待阻塞 CPU 计算。

## 6. 顺序执行与并发执行

*   **并发执行**:
    *   绝大多数同级任务是并发执行的。例如，批量上传的 100 张图片，会根据并发限制同时进行缩略图生成。
    *   不同类型的任务（如扫描和人脸识别）也可以并发执行，只要资源允许且未被暂停。

*   **顺序执行 (逻辑上的顺序)**:
    *   虽然 Worker 本身并发拉取，但通过 **任务链 (Task Chaining)** 实现了业务逻辑的顺序性。
    *   **示例**: 图片导入流程
        1.  `PROCESS_BASIC` (并发) -> 完成后
        2.  自动生成 `EXTRACT_METADATA` (高优先级)
        3.  自动生成 `RECOGNIZE_FACE` (低优先级)
        4.  自动生成 `OCR` (低优先级)
    *   这种机制确保了在图片基础信息入库前，不会先执行依赖图片的 AI 分析，同时也实现了任务的解耦。

## 7. 异常处理机制

1.  **任务级捕获**: 每个任务的执行都封装在 `execute_task_wrapper` 中，任何未捕获的异常都会被在此层拦截。
    *   异常被捕获后，任务状态更新为 `FAILED`，并将错误堆栈记录到日志，错误信息保存到数据库。
2.  **进程级容错**: Worker 主循环包含宽泛的 `try-except` 块，确保单个任务的严重错误或数据库连接抖动不会导致整个 Worker 进程崩溃。Worker 会在出错后休眠重试。
3.  **超时处理**: 也就是依赖 Future 的超时机制（目前代码中主要依赖 Python 的并发库管理）。

## 8. 性能优化策略

1.  **批处理 (Batch Processing)**:
    *   **批量插入**: `add_tasks` 使用 `bulk_save_objects` 减少数据库往返。
    *   **批量更新**: `result_loop` 会积攒一定数量的结果（或超时后）一次性刷新到数据库，减少高并发下的数据库写锁竞争。
2.  **资源隔离**: 区分 CPU 和 IO 线程池，防止大量 IO 任务阻塞 CPU 密集型任务的执行通道。
3.  **资源自动释放**:
    *   Worker 设有空闲检测机制。如果队列空闲超过 30 秒，会自动关闭线程池和进程池，释放系统内存和句柄资源，待有新任务时再重建。
4.  **极速模式 (Fast Mode)**: 动态调整并发上限，根据任务类型特性（CPU vs IO）最大化吞吐量。
5.  **完成即删除**: 成功的任务直接从数据库删除，防止 `Task` 表无限膨胀影响查询性能。
