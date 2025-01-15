class AbstractResultText:
    def print_stage_summary(self, stage, average_type_health):
        pass

    def print_kauffman_parameters(self, K, MAX_K, N, P):
        pass

    def print_attractor_summary(
        self, attractors, runs_with_attractor, runs_no_attractor
    ):
        pass


class ResultText(AbstractResultText):
    def print_stage_summary(self, stage, average_type_health):
        print(f"\nStage {stage}")
        print("Average Health of Node Types:")
        for node_type, health in average_type_health.items():
            print(f"  {node_type}: {health}")

    def print_kauffman_parameters(self, K, MAX_K, N, P):
        print(f"\nKauffman Network Parameters:")
        print(f"N (Total Nodes): {N}")
        print(f"K (Average Inputs per Node): {K}")
        print(f"K (Max Inputs per Node): {MAX_K}")
        print(f"P (Bias in Boolean Functions): {P}")

    def print_attractor_summary(
        self, attractors, runs_with_attractor, runs_no_attractor
    ):
        print()
        print(f"Number of attractors: {attractors.count()}")
        print(
            f"Percentage of runs with attractors: {runs_with_attractor / (runs_with_attractor + runs_no_attractor)}"
        )
