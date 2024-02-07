def print_stage_summary(stage, average_health, average_type_health):
    print(f"\nStage {stage}: Average Network Health = {average_health}")
    print("Average Health of Node Types:")
    for node_type, health in average_type_health.items():
        print(f"  {node_type}: {health}")
