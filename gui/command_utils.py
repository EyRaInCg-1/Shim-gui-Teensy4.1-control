import time
import re


# Serial command builders
def Ichannel_info(b_num: int, c_num: int) -> str:
    return f"Ichannel,{b_num},{c_num}\n"

def give_one_current(b_num: int, c_num: int, I_num: float) -> str:
    return f"Track,{b_num},{c_num},{I_num}\n"


# Extra current plan, stored in groups of 64 values
extra_current_plan = [0.0] * 64  # Starts with one group of 64 zeros
extra_plan_index = 0  # Index of the next group to apply


def apply_next_extra_group(ser, console=None, channel_widgets=None):
    global extra_current_plan, extra_plan_index

    if not ser or not ser.is_open:
        raise ValueError("Serial port not connected")

    start = extra_plan_index * 64
    end = start + 64
    group = extra_current_plan[start:end]

    # Pad with zeros if fewer than 64 values
    if len(group) < 64:
        group += [0.0] * (64 - len(group))

    for i in range(64):
        b = i // 8
        c = i % 8
        value = group[i]

        cmd = give_one_current(b, c, value)
        ser.write(cmd.encode())
        time.sleep(0.002)

        # Update each channel's input box (LED / labels are left unchanged)
        if channel_widgets and i < len(channel_widgets):
            channel_widgets[i].input_set.setText(f"{value:.3f}")

    if console:
        console.append(f">>> Applied extra_current_plan group {extra_plan_index + 1}")

    extra_plan_index += 1


def reset_extra_plan_index(ser=None, channel_widgets=None):
    """
    Reset the group index to 0; optionally send the 'Z' command to zero all
    currents and clear the input boxes in the GUI.
    """
    global extra_plan_index
    extra_plan_index = 0

    if ser and ser.is_open:
        ser.write(b"Z\n")  # Global zero command

    if channel_widgets:
        for widget in channel_widgets:
            widget.input_set.setText("0.000")


def load_extra_plan_from_file(path: str) -> int:
    """
    Load a current plan from a TXT file (64 values per group) into
    extra_current_plan. Returns the number of values loaded.
    """
    global extra_current_plan, extra_plan_index

    try:
        with open(path, "r") as f:
            values = []
            for line in f:
                parts = re.split(r'[,\s]+', line.strip())
                for val in parts:
                    if val:
                        values.append(float(val))

        extra_current_plan[:] = values
        extra_plan_index = 0  # Back to group 1
        return len(values)

    except Exception as e:
        raise RuntimeError(f"Failed to load: {e}")


def apply_prev_extra_group(ser, console=None, channel_widgets=None):
    global extra_current_plan, extra_plan_index

    if not ser or not ser.is_open:
        raise ValueError("Serial port not connected")

    if extra_plan_index <= 1:
        extra_plan_index = 0
    else:
        extra_plan_index -= 2  # Step back two groups, since apply adds 1

    apply_next_extra_group(ser, console=console, channel_widgets=channel_widgets)
