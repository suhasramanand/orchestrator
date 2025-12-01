# UI Screenshots

This directory contains screenshots of the Job Orchestration Platform UI.

## Screenshots Captured

### 1. Jobs List Page (`01-jobs-list.png`)
- Shows the main jobs listing table
- Features:
  - Search bar for filtering by job ID or type
  - Page size selector (10, 20, 30, 50)
  - Job table with columns: Job ID (last 8 digits), Type, Status, Progress, Tasks, Created, Actions
  - Pagination controls
  - Status badges with color coding
  - Progress bars showing completion percentage

### 2. Create Job Form (`02-create-job-form.png`)
- Form for creating new jobs
- Fields:
  - Job Type dropdown (Compute, Data Processing, ML Inference)
  - Number of Tasks input (1-1000)
  - Work Type dropdown (CPU Bound, I/O Bound, Matrix Multiply)
  - Work Duration in seconds
  - Matrix Size (when Matrix Multiply is selected)
- Action buttons: Create Job and Cancel

### 3. Analytics Dashboard (`03-analytics-full.png`)
- Comprehensive analytics dashboard
- Features:
  - Overview statistics cards (Total Jobs, Completed, Failed, Success Rate, Total Tasks, Avg Processing Time)
  - Jobs by Type (Bar Chart)
  - Jobs by Status (Pie Chart)
  - Tasks by Status (Pie Chart)
  - Job Creation Timeline (Line Chart with 7/14/30 day options)
  - Processing Time Statistics (Min, Max, Average, Median)

### 4. Job Detail View (`04-job-detail-view.png`)
- Detailed view of a specific job
- Shows:
  - Job metadata (ID, Type, Status, Created/Started/Completed timestamps)
  - Progress bar with task completion count
  - Tasks table with:
    - Task Index
    - Task ID (last 16 digits)
    - Status
    - Retries
    - Processing Time
    - Started/Completed timestamps

## Screenshot Location

All screenshots are saved in: `/Users/suhasreddybr/distributed-job-orchestration/screenshots/`

## Creating Screen Recordings

### macOS QuickTime Player
1. Open QuickTime Player
2. File > New Screen Recording
3. Click Record and select the area/window
4. Navigate through the UI showing:
   - Jobs list with search/filter
   - Creating a new job
   - Viewing analytics dashboard
   - Viewing job details
5. Stop recording and save

### Using ffmpeg (Command Line)
```bash
# Record screen (requires ffmpeg)
ffmpeg -f avfoundation -i "1:0" -r 30 output.mov

# Record specific window (requires window ID)
ffmpeg -f avfoundation -i "1:0" -vf "crop=1920:1080:0:0" output.mov
```

### Alternative Tools
- **OBS Studio** - Free, open-source screen recorder
- **Loom** - Easy screen recording with sharing
- **ScreenFlow** (macOS) - Professional screen recording
- **Kap** (macOS) - Simple screen recorder

## Recommended Recording Flow

1. **Start at Jobs List** - Show search functionality, pagination
2. **Create a Job** - Fill out form, submit, show success
3. **View Analytics** - Navigate to analytics, show charts updating
4. **View Job Detail** - Click on a job, show task list and progress
5. **Show Real-time Updates** - Wait for tasks to process, show status changes

## UI Features to Highlight

- ✅ Minimalistic, modern design
- ✅ Responsive layout
- ✅ Real-time status updates
- ✅ Search and filtering
- ✅ Comprehensive analytics
- ✅ Clean job/task visualization
- ✅ Status badges with color coding
- ✅ Progress indicators

