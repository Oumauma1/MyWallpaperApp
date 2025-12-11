# Copilot Instructions for MyWallpaperApp

## Project Overview

MyWallpaperApp is a Windows desktop application that enables users to set dynamic video wallpapers on Windows 11. The app allows users to schedule different MP4 videos to play as wallpapers at specific times throughout the day (e.g., sunrise/sunset themes) and includes performance optimizations to pause playback when other applications are maximized.

## Technology Stack

- **Python 3.x**: Primary programming language
- **PyQt6**: GUI framework for the main application window and video playback
  - `QtWidgets`: UI components (buttons, lists, time pickers)
  - `QtMultimedia`: Video and audio playback
  - `QtCore`: Timer functionality and core utilities
- **pywin32**: Windows API integration for:
  - Window management and manipulation
  - Desktop wallpaper embedding using WorkerW windows
  - Foreground window state detection

## Project Structure

```
MyWallpaperApp/
├── main.py                  # Main application entry point with GUI
├── wallpaper_manager.py     # Windows-specific wallpaper management
└── requirements.txt         # Python dependencies
```

### Key Components

#### main.py - VideoWallpaperApp
The main application class that provides:
- Video playlist management with scheduled trigger times
- Time-based wallpaper switching logic
- Performance optimization (pauses when apps are maximized)
- PyQt6-based user interface
- Video playback controls with looping

**Key Features:**
- Add MP4 videos to a playlist
- Assign trigger times (HH:mm format) to each video
- Toggle wallpaper mode on/off
- Automatic time-based video switching
- Performance optimization (auto-pause when maximized windows detected)

#### wallpaper_manager.py - WallpaperManager
Windows-specific implementation that:
- Uses Windows API to embed application windows into the desktop
- Finds and manages WorkerW windows (Windows' desktop background layer)
- Detects when foreground applications are maximized
- Handles screen resolution and window positioning

## Platform Requirements

- **Operating System**: Windows 11 (or Windows 10 with WorkerW support)
- **Python Version**: Python 3.7+ (required for PyQt6)
- The application is **Windows-only** due to its reliance on Win32 APIs and Windows' WorkerW window architecture

## Code Architecture & Design Patterns

### Video Scheduling Algorithm
The app uses a "most recent past time" algorithm:
- At any given time, play the video whose scheduled time is the most recent in the past
- Example: If it's 13:00 and videos are scheduled for 08:00 and 18:00, play the 08:00 video
- If current time is before all scheduled times, play the video with the latest time from the previous day

### Performance Optimization
- Uses a 1-second polling timer to check if foreground windows are maximized
- Automatically pauses video playback to save system resources
- Resumes playback when desktop becomes visible again

### WorkerW Window Technique
The application uses Windows' undocumented WorkerW window system:
1. Send message 0x052C to Progman to spawn WorkerW windows
2. Find the WorkerW window that serves as the desktop background layer
3. Set the video window as a child of this WorkerW window
4. The video then appears behind desktop icons as a true wallpaper

## Development Guidelines

### Code Style
- **Comments**: Code includes Chinese comments for developer reference
- **Variable naming**: Use descriptive English names (e.g., `is_wallpaper_mode`, `check_schedule`)
- **UI text**: User-facing text is in Chinese (target audience)

### Error Handling
- Display user-friendly message boxes for errors
- Validate playlist is not empty before enabling wallpaper mode
- Handle window enumeration failures gracefully

### State Management
- `is_wallpaper_mode`: Boolean flag for current mode
- `playlist`: List of dictionaries with 'path' and 'time' keys
- Persistent timers for schedule checking and performance monitoring

## Testing Approach

Currently, the project does not have automated tests. Testing is manual:
1. Launch the application: `python main.py`
2. Test video file selection and playlist management
3. Test time scheduling functionality
4. Test wallpaper mode toggle
5. Verify performance optimization by maximizing windows
6. Verify time-based switching by setting multiple scheduled videos

## Running the Application

### Installation
```bash
pip install -r requirements.txt
```

### Execution
```bash
python main.py
```

### User Workflow
1. Click "添加 MP4 视频" to add video files
2. Select a video from the list
3. Set a trigger time using the time picker
4. Click "更新选中视频的触发时间"
5. Toggle "开启/关闭 动态壁纸模式" to activate
6. Videos will automatically switch based on scheduled times

## Important Considerations for AI Assistance

1. **Windows API Changes**: The WorkerW technique is undocumented and may break with Windows updates
2. **Performance**: Video decoding is CPU-intensive; maintain the auto-pause feature
3. **File Paths**: Always use absolute paths for video files to avoid issues
4. **Thread Safety**: PyQt6 signals/slots handle threading; avoid manual thread management
5. **Timers**: Two separate timers (1s for optimization, 10s for scheduling) balance responsiveness and resource usage
6. **Window Handles**: The `winId()` method provides native window handles for Win32 API calls

## Future Enhancement Ideas

- Add support for image wallpapers (not just videos)
- Implement a system tray icon for background operation
- Add volume control for wallpaper audio
- Support for multiple monitor setups
- Configuration file persistence (save/load playlists)
- Video preview thumbnails in the playlist

## Dependencies

See `requirements.txt` for exact package versions. Key dependencies:
- PyQt6: GUI framework and multimedia support
- pywin32: Windows API access for wallpaper management

When updating dependencies, ensure compatibility with Windows 11 and test the WorkerW window functionality thoroughly.
