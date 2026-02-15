def power_produced(fusion_output: int) -> int:
    return max(0, int(fusion_output)) * 2

def heat_per_tick(fusion_output: int) -> int:
    return max(0, int(fusion_output))

def heat_on_output_increase(old_output: int, new_output: int) -> int:
    return max(0, int(new_output) - int(old_output))
