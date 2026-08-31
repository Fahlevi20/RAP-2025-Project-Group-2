from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.globals import set_verbose
import os
import pathlib
import time
import subprocess
from typing import Tuple
from geometry_msgs.msg import Twist, TwistStamped
from std_msgs.msg import Bool
from nav2_msgs.action import NavigateToPose
import rclpy
from rclpy.action import ActionClient
from rclpy.parameter import Parameter

node = None
vel_publisher = None
explore_publisher = None
navigate_to_pose_action_client = None


def execute_ros_command(command: str) -> Tuple[bool, str]:
    """
    Execute a ROS2 command.

    :param command: The ROS2 command to execute.
    :return: A tuple containing a boolean indicating success and the output of the command.
    """

    # Validate the command is a proper ROS2 command
    cmd = command.split(" ")

    if len(cmd) < 2:
        raise ValueError(f"'{command}' is not a valid ROS2 command.")
    if cmd[0] != "ros2":
        raise ValueError(f"'{command}' is not a valid ROS2 command.")

    try:
        output = subprocess.check_output(command, shell=True).decode()
        return True, output
    except Exception as e:
        return False, str(e)


# Helper function to get the maps directory
def _get_maps_dir() -> str:
    """Gets the absolute path to the 'maps' directory in the rosa_summit package, creates it if it doesn't exist."""

    maps_dir = "/home/ros/rap/Gruppe2/maps"
    pathlib.Path(maps_dir).mkdir(parents=True, exist_ok=True)
    return maps_dir


# Hardcoded locations
LOCATIONS = {
    "gym": {
        "position": {"x": 1.9517535073729964, "y": 4.359393291484201, "z": 0.0},
        "orientation": {
            "x": 1.6302566310137402e-08,
            "y": 2.9703213238180324e-08,
            "z": -0.07945176214102775,
            "w": 0.9968387118750377,
        },
    },
    "kitchen": {
        "position": {"x": 7.353217566768062, "y": -3.458078519447155, "z": 0.0},
        "orientation": {
            "x": 1.611930208234276e-08,
            "y": 2.980589390984495e-08,
            "z": -0.07325043342926793,
            "w": 0.997313578571165,
        },
    },
    "living room": {
        "position": {"x": 1.084137940689, "y": -0.383112079564818, "z": 0.0},
        "orientation": {
            "x": 3.316520260505064e-08,
            "y": 6.931688679143018e-09,
            "z": -0.8089064668855616,
            "w": 0.5879373502599718,
        },
    },
    "office": {
        "position": {"x": -4.9521764504716765, "y": -3.573205806403106, "z": 0.0},
        "orientation": {
            "x": -3.238093524948138e-08,
            "y": 9.961584542476143e-09,
            "z": 0.9923116132365216,
            "w": -0.1237645435329962,
        },
    },
    "bedroom": {
        "position": {"x": -4.002267652240865, "y": -0.060121871401907084, "z": 0.0},
        "orientation": {
            "x": -2.1636165143756515e-08,
            "y": 2.6069771799291994e-08,
            "z": 0.8980250477792399,
            "w": 0.43994433007039957,
        },
    },
}


@tool
def send_vel(velocity: float) -> str:
    """
    Sets the forward velocity of the robot.

    :param velocity: the velocity at which the robot should move
    """
    global vel_publisher, node
    msg = TwistStamped()
    msg.header.stamp = node.get_clock().now().to_msg()
    msg.twist.linear.x = velocity
    vel_publisher.publish(msg)

    return "Velocity set to %s" % velocity


@tool
def stop() -> str:
    """
    Stops or halts the robot by setting its velocity to zero

    """
    global vel_publisher, node
    msg = TwistStamped()
    msg.header.stamp = node.get_clock().now().to_msg()
    vel_publisher.publish(msg)
    return "Robot stopped"


@tool
def toggle_auto_exploration(resume_exploration: bool) -> str:
    """
    Starts or stops the autonomous exploration.

    :param resume_exploration: True to start/resume exploration, False to stop/pause exploration.
    """
    global explore_publisher
    msg = Bool()
    msg.data = resume_exploration
    explore_publisher.publish(msg)

    if resume_exploration:
        return "Autonomous exploration started/resumed."
    else:
        return "Autonomous exploration stopped/paused."


@tool
def navigate_to_pose(
    x: float, y: float, z_orientation: float, w_orientation: float
) -> str:
    """
    Moves the robot to an absolute position on the map.

    :param x: The x coordinate of the target position.
    :param y: The y coordinate of the target position.
    :param z_orientation: The z component of the target orientation (quaternion).
    :param w_orientation: The w component of the target orientation (quaternion).
    """
    global navigate_to_pose_action_client, node

    goal_msg = NavigateToPose.Goal()
    goal_msg.pose.header.frame_id = "map"
    goal_msg.pose.header.stamp = node.get_clock().now().to_msg()
    goal_msg.pose.pose.position.x = x
    goal_msg.pose.pose.position.y = y
    goal_msg.pose.pose.orientation.z = z_orientation
    goal_msg.pose.pose.orientation.w = w_orientation

    navigate_to_pose_action_client.send_goal_async(goal_msg)
    return f"Navigation goal sent to x: {x}, y: {y}, orientation_z: {z_orientation}, orientation_w: {w_orientation}."


@tool
def navigate_relative(
    x: float, y: float, z_orientation: float, w_orientation: float
) -> str:
    """
    Moves the robot relative to its current position using the robot's local coordinate frame.

    In the robot's coordinate system (base_link):
    - Positive X: Move forward
    - Negative X: Move backward
    - Positive Y: Move to the left
    - Negative Y: Move to the right

    :param x: The x coordinate of the target position relative to the robot (forward/backward).
    :param y: The y coordinate of the target position relative to the robot (left/right).
    :param z_orientation: The z component of the target orientation (quaternion) relative to the robot.
    :param w_orientation: The w component of the target orientation (quaternion) relative to the robot.
    """
    global navigate_to_pose_action_client, node

    goal_msg = NavigateToPose.Goal()
    goal_msg.pose.header.frame_id = "base_link"
    goal_msg.pose.header.stamp = node.get_clock().now().to_msg()
    goal_msg.pose.pose.position.x = x
    goal_msg.pose.pose.position.y = y
    goal_msg.pose.pose.orientation.z = z_orientation
    goal_msg.pose.pose.orientation.w = w_orientation

    navigate_to_pose_action_client.send_goal_async(goal_msg)
    return f"Relative navigation goal sent to x: {x}, y: {y}, orientation_z: {z_orientation}, orientation_w: {w_orientation}."


@tool
def save_map(map_name: str) -> str:
    """
    Saves the current map from the /summit/map topic to .yaml and .pgm files
    in the 'maps' directory of the 'rosa_summit' package.

    :param map_name: The name for the map (e.g., 'my_lab_map'). Do not include file extensions.
    """
    maps_dir = _get_maps_dir()
    if not os.path.isdir(maps_dir):
        return f"Error: Maps directory {maps_dir} could not be accessed or created."

    filepath_prefix = os.path.join(maps_dir, map_name)

    cmd = f"ros2 run nav2_map_server map_saver_cli -f '{filepath_prefix}' --ros-args -r map:=/summit/map"
    success, output = execute_ros_command(cmd)
    if success:
        if "Map saved to" in output:
            return f"Map successfully saved as {map_name} in {maps_dir}"
        else:
            return f"Map saving process initiated for {map_name} in {maps_dir}. Output: {output}"
    else:
        return f"Failed to save map {map_name} in {maps_dir}. Error: {output}"


@tool
def list_saved_maps() -> str:
    """
    Lists all saved maps in the 'maps' directory of the 'rosa_summit' package.
    Returns a list of map names (without .yaml extension).
    """
    maps_dir = _get_maps_dir()
    if not os.path.isdir(maps_dir):
        return "Maps directory not found or is not a directory."

    try:
        files = os.listdir(maps_dir)
        map_files = [
            f[:-5]
            for f in files
            if f.endswith(".yaml") and os.path.isfile(os.path.join(maps_dir, f))
        ]
        if not map_files:
            return "No saved maps found in the maps directory."
        return f"Available maps: {', '.join(map_files)}"
    except Exception as e:
        return f"Error listing maps: {e}"


@tool
def get_location_names() -> str:
    """
    Returns a list of available location names.
    """
    return f"Available locations: {', '.join(LOCATIONS.keys())}"


@tool
def navigate_to_location_by_name(location_name: str) -> str:
    """
    Moves the robot to a predefined location by its name.

    :param location_name: The name of the location to navigate to (e.g., 'kitchen', 'gym').
    """
    global navigate_to_pose_action_client, node
    location_name_lower = location_name.lower()
    if location_name_lower not in LOCATIONS:
        return f"Location '{location_name}' not found. Available locations are: {', '.join(LOCATIONS.keys())}"

    loc_data = LOCATIONS[location_name_lower]
    pos = loc_data["position"]
    orient = loc_data["orientation"]

    goal_msg = NavigateToPose.Goal()
    goal_msg.pose.header.frame_id = "map"
    goal_msg.pose.header.stamp = node.get_clock().now().to_msg()
    goal_msg.pose.pose.position.x = pos["x"]
    goal_msg.pose.pose.position.y = pos["y"]
    goal_msg.pose.pose.orientation.z = orient["z"]
    goal_msg.pose.pose.orientation.w = orient["w"]

    navigate_to_pose_action_client.send_goal_async(goal_msg)
    return f"Navigation goal sent to location '{location_name}'. Position: {pos}, Orientation: {orient}."


SYSTEM_PROMPT = """You are Summit, a helpful robot assistant in a simulated ROS2 environment.

You have access to the following tools and MUST use them to control the robot:

- send_vel(velocity: float) - Set forward velocity in m/s. Example: send_vel(0.5)
- stop() - Stop the robot immediately
- toggle_auto_exploration(resume_exploration: bool) - Start (True) or stop (False) autonomous exploration
- navigate_to_pose(x: float, y: float, z_orientation: float, w_orientation: float) - Navigate to absolute map position
- navigate_relative(x: float, y: float, z_orientation: float, w_orientation: float) - Move relative to current position
- save_map(map_name: str) - Save current SLAM map
- list_saved_maps() - List all saved maps
- get_location_names() - Get list of known locations
- navigate_to_location_by_name(location_name: str) - Navigate to a named location (gym, kitchen, living room, office, bedroom)

IMPORTANT: You MUST call the appropriate tool for every user request. Do NOT just describe what you would do - actually invoke the tool. After calling a tool, briefly confirm what you did."""

TOOLS = [
    send_vel,
    stop,
    toggle_auto_exploration,
    navigate_to_pose,
    navigate_relative,
    save_map,
    list_saved_maps,
    get_location_names,
    navigate_to_location_by_name,
]


def main():
    global node, vel_publisher, explore_publisher, navigate_to_pose_action_client
    set_verbose(False)
    print("Hi from rosa_summit.")

    rclpy.init()
    sim_time_param = Parameter("use_sim_time", rclpy.Parameter.Type.BOOL, True)
    node = rclpy.create_node("rosa_summit_node", parameter_overrides=[sim_time_param])

    vel_publisher = node.create_publisher(TwistStamped, "/cmd_vel", 10)
    explore_publisher = node.create_publisher(Bool, "/summit/explore/resume", 10)
    navigate_to_pose_action_client = ActionClient(
        node, NavigateToPose, "/navigate_to_pose"
    )

    try:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            try:
                key_path = "/home/ros/rap/Gruppe2/api-key.txt"
                with open(key_path, "r") as f:
                    api_key = f.read().strip().split("\n")[-1]
            except Exception as e:
                print(f"Error reading API key: {e}")
                return

        llm = ChatOpenAI(
            model="inclusionai/ling-3.0-flash-fin:free",
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=api_key,
            temperature=0,
        )
        llm_with_tools = llm.bind_tools(TOOLS)
        print("Using OpenRouter Free Model (Ling 3.0 Flash)")
    except Exception as e:
        print(f"Error initializing LLM: {e}")
        return

    print("Type 'exit' or 'quit' to end the program")
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    try:
        while True:
            msg = input("Enter your request: ")
            if msg.lower() in ["exit", "quit"]:
                break

            try:
                t0 = time.time()
                print("Request sent...")
                messages.append(HumanMessage(content=msg))
                response = llm_with_tools.invoke(messages)
                elapsed = time.time() - t0
                print(f"[TIME] {elapsed:.2f}s")

                if response.tool_calls:
                    for tc in response.tool_calls:
                        print(f"[TOOL CALLED] {tc['name']}({tc['args']})")
                        tool_fn = next((t for t in TOOLS if t.name == tc['name']), None)
                        if tool_fn:
                            result = tool_fn.invoke(tc['args'])
                            print(f"[RESULT] {result}")
                else:
                    print(f"[RESPONSE] {response.content}")

                messages = [SystemMessage(content=SYSTEM_PROMPT)]
            except Exception as e:
                print(f"An error occurred: {e}")
    except KeyboardInterrupt:
        print("\nProgram terminated by user")

    print("Bye from rosa_summit.")


if __name__ == "__main__":
    main()
