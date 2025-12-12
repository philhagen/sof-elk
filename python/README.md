# SOF-ELK Python Package

This package provides Python-based support utilities and management tools for the SOF-ELK® appliance. It is designed to replace and extend legacy shell and Ruby scripts, offering a more robust and maintainable codebase.

## Directory Structure

*   `src/sof_elk/`: The main package source code.
    *   `lib/`: Core libraries and data structures (e.g., dictionary lookups, ECS definitions).
    *   `utils/`: Utility modules for specific tasks (e.g., firewall management, CSV conversion, system configuration).
    *   `management/`: Management modules (e.g., git updates, elasticsearch maintenance).
    *   `cli.py`: The main command-line interface entry point.

## Usage

The package exposes a command-line interface (CLI) to interact with various system components.

### Running the CLI

You can run the CLI using the package entry point:

```bash
python3 -m sof_elk.cli [subcommand] [arguments]
```

### Available Modules

### Available Modules

#### Management (`sof_elk.management`)
Core administrative tools for maintaining the SOF-ELK appliance.
*   **elasticsearch**: Index management (freeze, thaw, clear, list) and comprehensive cluster maintenance.
*   **kibana**: Dashboard loading, object management, and configuration application.
*   **git**: Repository updates, branch switching, and upstream verification.
*   **logstash**: Plugin management and updates.
*   **vm**: Version checking and update notification.

#### Utils (`sof_elk.utils`)
*   **csv**: Convert CSV files to JSON.
*   **firewall**: Manage system firewall rules (wrapper around `firewall-cmd`).
*   **login**: Display the SOF-ELK welcome message and check for updates.
*   **nfdump**: Process Netflow data using `nfdump`.
*   **system**: Manage system configurations like keyboard layout.

#### Library (`sof_elk.lib`)
*   **dictionaries**: Manage and query YAML-based dictionaries for protocol and service lookups.
*   **ecs**: Definitions for Elastic Common Schema (ECS) fields.

#### API (`sof_elk.api`)
Low-level clients for interacting with backend services.
*   **client**: Resilient HTTP client factory.
*   **elasticsearch**: `ElasticsearchManagement` class for tasks like force merging and template management.
*   **kibana**: `KibanaClient` for saved object manipulation and data view management.

## Usage Examples

### Management Commands

**Clear Index Data**
```bash
# Clear all data from the syslog index
python3 -m sof_elk.cli management clear --index syslog
```

**Freeze an Index**
```bash
# Freeze an index, delete the source, and rename it
python3 -m sof_elk.cli management freeze --action freeze --index "syslog-2023.01" --delete --newindex "syslog-frozen-2023.01"
```

**Update Repository**
```bash
# Check for updates and pull if available
python3 -m sof_elk.cli management update
```

## Development

All Python code is located in `src/`. The package follows a modular structure where `cli.py` dynamically loads available components.
