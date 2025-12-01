# Distributed Job Orchestration Platform: Development Documentation

For visual architecture diagrams, see [ARCHITECTURE_DIAGRAM.md](./ARCHITECTURE_DIAGRAM.md)

## Executive Summary

This document describes the development process, technical challenges, and solutions for a distributed job orchestration system. The system uses AWS serverless services for orchestration and messaging, combined with Kubernetes for compute execution. This project was built to explore distributed systems patterns and gain hands-on experience with cloud-native technologies.

## Project Overview

The system allows users to submit computational jobs through a web interface. Jobs are broken down into individual tasks that get sent to an SQS queue. Kubernetes workers poll the queue, process tasks, and update the backend with results. The frontend shows job status and task progress in real-time.

## Architecture and Technology Stack

The platform is built using a microservices architecture with clear separation of concerns. The backend API is implemented in Python using FastAPI, providing RESTful endpoints for job and task management. The database layer uses SQLAlchemy ORM with support for both PostgreSQL in production and SQLite for local development. The worker components are containerized Python applications that poll SQS queues and process tasks asynchronously.

The frontend is a React application built with TypeScript and Vite, providing a responsive user interface for job submission and monitoring. Infrastructure as Code is managed through Terraform configurations for AWS resources, while Kubernetes manifests handle container orchestration. Local development leverages Docker Compose for service dependencies and LocalStack for AWS service emulation.

The messaging layer uses AWS SQS for task distribution, with LocalStack providing local SQS functionality during development. Kubernetes deployments manage worker scaling and resource allocation. The system is designed to be cloud-agnostic for the compute layer while leveraging AWS services for orchestration and messaging.

## Development Approach

Development started with the backend API and database schema, since that's the foundation everything else depends on. The FastAPI endpoints were built first, then tested with curl before building the frontend. The worker logic was developed separately and tested by running it locally before deploying to Kubernetes.

SQLite was used initially because it requires no setup and works immediately. This made it much faster to iterate on the database schema and API logic. PostgreSQL was added later when we needed to test with a more realistic database. LocalStack was integrated early because SQS is central to the system's operation.

The Kubernetes integration came last and was the most challenging part. Getting Docker images built, loaded into kind, and configured correctly took significant time. The network connectivity issues between LocalStack and the kind cluster weren't anticipated and required several iterations to resolve.

## Core Functionality Implementation

The job creation workflow begins when a user submits a job through the frontend interface. The backend API receives the job request, validates parameters, and creates a corresponding database record. The system then generates the specified number of tasks, each representing a unit of work to be processed.

Tasks are immediately enqueued to the SQS queue with all necessary metadata including task ID, job ID, task index, and processing parameters. The backend updates the job status to ENQUEUED, indicating that tasks are ready for processing. This design ensures that task creation and enqueueing are atomic operations, preventing orphaned tasks.

Worker pods running in Kubernetes continuously poll the SQS queue using long polling to minimize empty responses and reduce API calls. When messages are received, workers extract task information and begin processing. The processing logic simulates various types of computational work including CPU-bound operations, I/O-bound operations, and matrix multiplication tasks.

During task processing, workers update the backend API to mark tasks as running, then execute the actual work, and finally report completion or failure. The backend aggregates task statuses to update overall job status, automatically transitioning jobs to COMPLETED when all tasks finish successfully.

## Critical Issues Encountered

### Issue One: Task Enqueueing Failure

The first major issue discovered was that tasks were being created in the database but not sent to the SQS queue. This meant workers were polling an empty queue while tasks remained unprocessed in the database. The root cause was in the job service implementation where task creation and SQS enqueueing were separate operations without proper error handling.

The job service was creating tasks and updating the database, but the SQS enqueueing logic was not being called. This was a critical oversight that prevented the entire distributed processing system from functioning. Workers would start successfully, connect to SQS, but find no messages to process.

### Issue Two: Network Connectivity Problems

A significant challenge emerged with network connectivity between Kubernetes pods and LocalStack. The LocalStack container was running on the host machine's Docker network, but the kind cluster operates on a separate network. This network isolation prevented worker pods from reaching LocalStack's SQS endpoint.

Initial attempts to use localhost or host.docker.internal failed because kind pods run in a different network namespace. The solution required creating a Kubernetes Service and Endpoints resource that explicitly mapped the LocalStack container's IP address to a service name accessible within the cluster.

Additionally, LocalStack needed to be connected to the kind network to ensure proper routing. This involved using docker network connect to bridge the networks, allowing pods to reach the LocalStack container through the service endpoint.

### Issue Three: Worker Pod Restart Loops

Worker pods were experiencing CrashLoopBackOff states due to failed health check probes. The deployment configuration included liveness and readiness probes that attempted to verify worker process health using the ps command. However, the minimal Python base image did not include the ps utility, causing all health checks to fail.

Kubernetes interpreted these failed health checks as container failures and repeatedly restarted the pods. This prevented workers from maintaining stable connections to SQS and processing tasks consistently. The constant restarts also made debugging difficult as logs were frequently truncated.

### Issue Four: API Connectivity from Kubernetes

Workers running in Kubernetes pods could not reach the backend API running on the host machine. The configuration used host.docker.internal which works for Docker containers but has inconsistent support in kind clusters depending on the host operating system.

The ConfigMap initially contained an incorrect API URL pointing to a non-existent backend-service. This was a configuration error that prevented all API calls from workers. Even after correcting the URL, network routing issues persisted due to kind's network architecture.

### Issue Five: Message Deletion Logic Error

A critical bug was discovered in the message deletion logic. The worker code was deleting SQS messages even when API calls to update task status failed. This meant that if the backend API was unreachable or returned errors, tasks would be lost permanently as their messages were removed from the queue.

The original implementation deleted messages in both success and failure paths, assuming that failed tasks should be removed to prevent infinite retries. However, this violated the principle of idempotency and prevented proper error recovery. Messages should only be deleted after successful processing and status confirmation.

## Solutions Implemented

### Solution for Task Enqueueing

The fix involved modifying the job service to explicitly enqueue tasks to SQS immediately after database creation. We added a loop that iterates through all created tasks and sends each one to the SQS queue using the SQS service. Error handling was added to log failures without blocking the overall job creation process.

The SQS service was enhanced to properly handle LocalStack endpoints by extracting the base URL from the queue URL. This ensures that boto3 clients are configured with the correct endpoint for local development. The service also includes fallback logic for missing configuration values.

### Solution for Network Connectivity

To resolve the network connectivity issues, we implemented a multi-step approach. First, we identified LocalStack's IP address on the kind network using docker network inspect. Then we created a Kubernetes Endpoints resource that explicitly maps this IP to a service named localstack.

The Kubernetes Service resource provides DNS resolution within the cluster, allowing pods to reference localstack by name. The Endpoints resource ensures that DNS lookups resolve to the correct IP address. This approach is more reliable than using host.docker.internal which has platform-specific limitations.

We also ensured LocalStack is connected to the kind network using docker network connect. This bridges the networks and allows proper routing between the cluster and the LocalStack container. The endpoint IP is periodically verified and updated if LocalStack's IP changes.

### Solution for Health Check Failures

The health check probes were completely removed from the deployment configuration. Since workers run as long-lived processes that continuously poll SQS, traditional health checks are unnecessary. The workers handle their own error recovery and logging, making external health checks redundant.

Removing the probes eliminated the restart loops and allowed workers to run stably. We rely on Kubernetes' natural pod lifecycle management and the workers' internal error handling rather than external health checks. This approach is appropriate for worker-style applications that don't expose HTTP endpoints.

### Solution for API Connectivity

The API connectivity issue was addressed by updating the ConfigMap with the correct API base URL. We standardized on host.docker.internal for local development, which works on Docker Desktop for Mac and Windows. For Linux environments, alternative approaches like using the kind node's IP address would be necessary.

The worker code was enhanced with better error handling for API connection failures. Workers now log detailed error messages when API calls fail, making debugging easier. The timeout values were adjusted to prevent hanging requests while still allowing for network latency.

### Solution for Message Deletion

The message deletion logic was completely refactored to follow proper idempotency principles. Messages are now only deleted after successful confirmation from the backend API. If the API call fails, the message remains in the queue and becomes visible again after the visibility timeout expires.

For exception cases, we added conditional deletion that only occurs if the failure marking was successful. This prevents message loss during transient failures. The error handling now distinguishes between processing failures and API communication failures, applying appropriate recovery strategies for each.

## Technical Implementation Details

### Database Schema Design

The database schema uses two primary tables: jobs and tasks. The jobs table stores high-level job information including status, task counts, and metadata. The tasks table contains individual task records with status, retry counts, and processing results.

Status fields use enumerated types to ensure data integrity. Job statuses include PENDING, CREATING_TASKS, ENQUEUED, RUNNING, COMPLETED, and FAILED. Task statuses include PENDING, ENQUEUED, RUNNING, COMPLETED, FAILED, and RETRYING.

The schema includes timestamps for created_at, updated_at, started_at, and completed_at to track when things happen. Parameters are stored as JSON strings because SQLite doesn't have native JSON support, and this approach works for both SQLite and PostgreSQL.

### API Endpoint Design

The API uses standard REST patterns. Jobs are created with POST /api/v1/jobs and listed with GET /api/v1/jobs. Tasks can be accessed through /api/v1/jobs/{job_id}/tasks or directly by task ID.

Workers call three endpoints to update task status: /running, /complete, and /failed. These endpoints take minimal data to keep the requests small. The complete endpoint takes a result object and processing time, while the failed endpoint just takes an error message.

Pagination was added to the job list endpoint because testing with many jobs made the response too large. The API returns page number, page size, total count, and total pages so the frontend can build pagination controls.

### Worker Implementation

Workers are implemented as long-running Python processes that continuously poll SQS queues. The polling uses long polling with WaitTimeSeconds set to 20 seconds, reducing empty responses and API call frequency. When messages are received, workers parse the JSON body and extract task metadata.

Task processing has try-catch blocks around the main logic to catch exceptions. Workers update task status at three points: when starting, when completing, and when failing. Each update is logged so we can trace what happened if something goes wrong.

The worker configuration is managed through environment variables injected via Kubernetes ConfigMaps and Secrets. This allows for environment-specific configuration without rebuilding container images. Sensitive values like AWS credentials are stored in Kubernetes Secrets.

### Frontend Architecture

The React frontend is split into components for job listing, job creation, and job details. API calls are in a separate service file to keep the components clean. This structure makes it easier to change the API implementation later if needed.

The job list polls the API every few seconds to get updated statuses. This was added after noticing that jobs would complete but the UI wouldn't show it until a manual refresh. The job detail view shows all tasks for a job with their individual statuses and processing times.

Error handling shows basic error messages to users when API calls fail. There's no sophisticated retry logic yet, but the error messages at least tell users what went wrong. The UI is basic but functional, tested mainly in Chrome during development.

## Testing and Validation

Testing was done primarily through manual integration testing during development. The backend API was tested using curl commands and the frontend interface. SQLite was used initially for quick iteration, then switched to PostgreSQL to verify the same code works with a production-like database.

LocalStack was essential for testing SQS functionality without AWS credentials. This allowed testing queue operations, message formats, and worker polling behavior locally. The kind cluster was used to test Kubernetes deployments and verify that pods could connect to services correctly.

Most debugging happened by examining logs from worker pods and the backend API. The structured logging made it easier to trace issues through the system. Network connectivity problems were particularly challenging to debug and required testing connectivity from within pods using kubectl exec commands.

The frontend was tested manually in Chrome and Firefox. The auto-refresh functionality was added after noticing that job status wasn't updating without manual page refreshes. Performance testing was informal, mainly verifying that multiple jobs could be processed concurrently without issues.

## Deployment Considerations

The current setup runs entirely locally using Docker Compose for PostgreSQL and kind for Kubernetes. This approach was chosen to avoid AWS costs during development and to make the system runnable without cloud credentials.

For production deployment, several changes would be necessary. The backend would need to be containerized and deployed to Kubernetes or a serverless platform. The current implementation runs as a single process, which works for development but would need load balancing and multiple replicas for production.

Worker autoscaling based on SQS queue depth would be ideal, but the current deployment uses a fixed number of replicas. Implementing horizontal pod autoscaling would require adding metrics collection and configuring the autoscaler, which wasn't done for this project.

Monitoring is currently limited to log inspection. A production system would need metrics collection, alerting, and potentially distributed tracing. The structured logging format used makes it easier to add log aggregation tools later, but no monitoring stack was integrated during development.

## Lessons Learned

The biggest lesson was that network connectivity in containerized environments is more complex than expected. What works for Docker containers doesn't necessarily work for Kubernetes pods, even when using the same underlying technology. The LocalStack and kind integration required learning about Kubernetes Services and Endpoints, which wasn't initially planned.

Error handling became more important as the system grew. Early versions had minimal error handling, which made debugging very difficult when things went wrong. Adding structured logging with context information made it much easier to trace issues through the system.

The message deletion bug was a good reminder about idempotency. It's easy to assume operations will succeed, but in distributed systems, failures are common. Only deleting messages after successful confirmation prevents data loss, even if it means some messages get processed multiple times.

The health check issue was frustrating because it seemed like the pods were failing when they were actually working fine. This taught me that default Kubernetes configurations aren't always appropriate for every application type. Sometimes it's better to remove health checks entirely rather than trying to make them work.

Configuration management through ConfigMaps seemed straightforward but caused several issues. A typo in the API URL prevented workers from connecting to the backend, and it took a while to realize the configuration was wrong rather than the code. This highlighted the importance of validating configuration values.

## Future Enhancements

Several enhancements could improve the platform further. Implementing AWS Step Functions for actual orchestration would provide more sophisticated workflow management and better integration with other AWS services. Currently, Step Functions integration is stubbed out for local development.

Adding retry logic with exponential backoff for API calls would improve resilience to transient failures. Dead letter queue handling would provide better visibility into permanently failed tasks. Implementing task prioritization and scheduling would enable more sophisticated job management.

Adding monitoring would help understand system behavior in production. Prometheus and Grafana could provide dashboards showing job processing rates and error rates. Distributed tracing would be useful for understanding where time is spent when jobs take longer than expected.

Security enhancements could include authentication and authorization for API endpoints, encryption at rest for sensitive data, and network policies for Kubernetes pods. These would be essential for production deployments handling sensitive workloads.

## Conclusion

The system successfully processes distributed workloads by combining AWS SQS for task distribution with Kubernetes workers for execution. The development process involved solving several non-trivial integration challenges, particularly around network connectivity between containers and Kubernetes clusters.

The most significant learning from this project was understanding how different network namespaces interact in containerized environments. The LocalStack and kind integration required careful configuration of Kubernetes Services and Endpoints to bridge network boundaries. This experience highlighted the importance of understanding network fundamentals when working with distributed systems.

The error handling and idempotency patterns implemented were learned through trial and error. Initially, messages were being deleted prematurely, which led to data loss. Fixing this required understanding SQS visibility timeouts and implementing proper confirmation workflows before message deletion. These patterns are now well-documented in the codebase for future reference.

