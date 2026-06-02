# ROSA Summit — LLM-Controlled Robot (ROS2 Jazzy)

Voice/text control of a Summit XL robot in Gazebo using LLM tool calling via [OpenRouter](https://openrouter.ai/) (free model: NVIDIA Nemotron 3 Super 120B).

## Prerequisites

- Docker with NVIDIA GPU support (`nvidia-container-toolkit`)
- An [OpenRouter API key](https://openrouter.ai/keys) (free tier works)

## Quick Start

### 1. Build the Docker image

```bash
git clone https://github.com/Fahlevi20/RAP-2025-Project-Group-2.git
cd RAP-2025-Project-Group-2
docker build -t rap-gruppe2:latest .
```

Or use the retry script:

```bash
./docker_build.sh
```

### 2. Run the container

```bash
docker run -it --rm \
    --gpus all \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -e NVIDIA_DRIVER_CAPABILITIES=all \
    -e DISPLAY=$DISPLAY \
    -e XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR \
    --device /dev/dri \
    --name robotcontrol \
    rap-gruppe2:latest \
    /bin/bash
```

### 3. Set your OpenRouter API key

Edit the key file inside the container:

```bash
echo "your-openrouter-api-key" > /home/ros/rap/Gruppe2/api-key.txt
```

Or set as environment variable:

```bash
export OPENROUTER_API_KEY="your-openrouter-api-key"
```

### 4. Launch the simulation

**Terminal 1** — Start Gazebo + Nav2:

```bash
source /home/ros/colcon_ws/install/setup.bash
ros2 launch rosa_summit summit.launch.py
```

With SLAM (mapping mode):

```bash
ros2 launch rosa_summit summit.launch.py slam:=True
```

### 5. Run the LLM agent

**Terminal 2** — Open a new shell into the container:

```bash
docker exec -it robotcontrol bash
source /home/ros/colcon_ws/install/setup.bash
ros2 run rosa_summit rosa_summit
```

You'll see:

```
Hi from rosa_summit.
Using NVIDIA Nemotron 3 Super (free) via ChatOpenRouter
Type 'exit' or 'quit' to end the program
Enter your request:
```

### 6. Control the robot

Type natural language commands:

```
Enter your request: move forward 0.1 m/s
[TOOL CALLED] send_vel({'velocity': 0.1})
[RESULT] Velocity set to 0.1
```

## Available Commands

| Command | Example |
|---------|---------|
| `send_vel(velocity)` | "move forward at 0.5 m/s" |
| `stop()` | "stop" |
| `toggle_auto_exploration(bool)` | "start exploring" / "stop exploring" |
| `navigate_to_pose(x, y, z, w)` | "go to position x 1.5 y -2.0" |
| `navigate_relative(x, y, z, w)` | "move 1 meter forward" |
| `save_map(name)` | "save the map as my_map" |
| `list_saved_maps()` | "show saved maps" |
| `get_location_names()` | "what are the known locations?" |
| `navigate_to_location_by_name(name)` | "go to kitchen" |

## Project Structure

```
├── Dockerfile              # Container build
├── init.sh                 # Environment setup (deps, build)
├── rosa_summit/
│   └── rosa_summit.py      # LLM agent with tool calling
├── launch/
│   └── summit.launch.py    # Gazebo + Nav2 launch
├── world/
│   ├── empty.world         # Lightweight empty world
│   └── small_house.world   # AWS small house world
├── maps/                   # Saved SLAM maps
└── demo/                   # Demo videos
```

## LLM Configuration

The agent uses `langchain-openrouter` with `bind_tools()` for proper function calling. Model can be changed in `rosa_summit.py`:

```python
llm = ChatOpenRouter(
    model="nvidia/nemotron-3-super-120b-a12b:free",
    temperature=0,
)
```

Any OpenRouter model that supports tool calling will work.

## Demo

- [Mapping demo](./demo/mapping.mp4)
- [Navigation demo](./demo/navigation.mp4)

## License

MIT — see [LICENSE](./LICENSE).

## Credits

Based on [mikelikesrobots/RAP-2025-Project-Group-2](https://github.com/mikelikesrobots/RAP-2025-Project-Group-2).
