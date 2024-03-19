class ResultText:
    def print_stage_summary(self, stage, average_health, average_type_health):
        print(f"\nStage {stage}: Average Network Health = {average_health}")
        print("Average Health of Node Types:")
        for node_type, health in average_type_health.items():
            print(f"  {node_type}: {health}")

    def print_kauffman_parameters(self, K, MAX_K, N, P):
        print(f"\nKauffman Network Parameters:")
        print(f"N (Total Nodes): {N}")
        print(f"K (Average Inputs per Node): {K}")
        print(f"K (Max Inputs per Node): {MAX_K}")
        print(f"P (Bias in Boolean Functions): {P}")

    def print_attractor_summary(self, attractor_counts, runs_with_attractor, runs_no_attractor):
        print()
        print("Significant Attractors and their occurrence counts:")
        # Sorting attractors by their count in descending order
        sorted_attractors = sorted(attractor_counts.items(), key=lambda item: item[1], reverse=True)
        for attractor_states, count in sorted_attractors:
            print(f"Count: {count}, States: {len(attractor_states)}")
            state = 1
            for attractor_state in attractor_states:
                print(f"State {state}: {attractor_state}")
                state = state + 1
        print()
        print(f"Number of attractors: {len(attractor_counts)}")
        print(f"Percentage of runs with attractors: {runs_with_attractor / (runs_with_attractor + runs_no_attractor)}")


class NullResultText:
    def print_stage_summary(self, stage, average_health, average_type_health):
        pass

    def print_kauffman_parameters(self, K, MAX_K, N, P):
        pass

    def print_attractor_summary(self, attractor_counts, runs_with_attractor, runs_no_attractor):
        pass
