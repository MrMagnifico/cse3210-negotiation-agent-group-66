import argparse
import json
import statistics
from multiprocessing import Process
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

from utils.plot_trace import plot_trace
from utils.runners import run_session

MATPLOTLIB = False
TYPES = {
    "standard": 1,
    "opponent": 2,
    "random": 3,
    "mutation": 4,
    "operation": 5
}

DOMAINS = [
    "domain00", "domain01", "domain02", "domain03", "domain04", "domain05",
    "domain06", "domain07", "domain08", "domain09"
]

AGENTS = [
    "agents.boulware_agent.boulware_agent.BoulwareAgent",
    "agents.conceder_agent.conceder_agent.ConcederAgent",
    "agents.hardliner_agent.hardliner_agent.HardlinerAgent",
    "agents.linear_agent.linear_agent.LinearAgent",
    "agents.random_agent.random_agent.RandomAgent",
    "agents.stupid_agent.stupid_agent.StupidAgent",
    "agents.template_agent.template_agent.TemplateAgent",
    "agents.custom_agents.custom_agent_0.CustomAgent",
    "agents.randomp.randomparty.RandomParty.RandomParty",
    "agents.ponpokoagent.ponpoko.ponpoko.PonPokoParty"
]

PARAMS = {
    "patternChangeDelay": -1,
    "generatorType": 1,
    "fallbackBidUtilRange": 0.05,
    "opponentEpsilon": 0.25
}

SAMPLES = 5

parser = argparse.ArgumentParser(description="Generate metrics for the agent")


def save_as_image(title, values, file_):
    def _plot_norm(name, s):
        mu = s['mean']
        sigma = s['stdev']
        x = np.linspace(0.0, 1.0, 100)
        y = norm.pdf(x, mu, sigma)
        plt.plot(x, y, label=name)

    for name, items in values.items():
        if "util" in name:
            _plot_norm(name, items)

    plt.title(title)
    plt.xlabel('Value')
    plt.ylabel('Probability Density')
    plt.legend()
    plt.savefig(file_)
    plt.clf()
    plt.cla()
    plt.close()


def run_sessions(domain, opponent):
    # Create settings and generate results
    agents = ["agents.ponpokoagent.ponpoko.ponpoko.PonPokoParty", opponent]
    profiles = [
        f"domains/{domain}/profileA.json", f"domains/{domain}/profileB.json"
    ]
    settings = {
        "agents": agents,
        "profiles": profiles,
        "deadline_rounds": 200,
        "ponpoko_params": PARAMS
    }

    # Create results dir
    agent_name = opponent.split(".")[-1]
    res_dir = f"results/{domain}/AgentGrug_{agent_name}"
    Path(res_dir).mkdir(parents=True, exist_ok=True)

    for run in range(SAMPLES):
        results_trace, results_summary = run_session(settings)

        # Write raw results and plot
        plot_trace(results_trace, f"{res_dir}/trace_plot_(run-{run}).html")
        with open(f"{res_dir}/results_trace_(run-{run}).json", "w") as f:
            f.write(json.dumps(results_trace, indent=2))
        with open(f"{res_dir}/results_summary_(run-{run}).json", "w") as f:
            f.write(json.dumps(results_summary, indent=2))


def analyse_results():
    for domain in domains:
        for opponent in opponents:
            agent_name = opponent.split(".")[-1]
            res_dir = f"results/{domain}/AgentGrug_{agent_name}"

            # Aggregate results summaries
            offer_nums = []
            grug_utils = []
            opponent_utils = []
            nash_products = []
            social_welfares = []
            results = []
            for sample in range(SAMPLES):
                file_name = f"{res_dir}/results_summary_(run-{sample}).json"
                with open(file_name, "r") as file:
                    data = file.read()
                    json_data = json.loads(data)
                    offer_nums.append(json_data["num_offers"])
                    grug_utils.append(json_data["utility_1"])
                    opponent_utils.append(json_data["utility_2"])
                    nash_products.append(json_data["nash_product"])
                    social_welfares.append(json_data["social_welfare"])
                    results.append(json_data["result"])

            # Write results aggreggate to JSON file
            summary = {
                "offers": {
                    "mean": statistics.mean(offer_nums),
                    "stdev": statistics.stdev(offer_nums)
                },
                "grug_util": {
                    "mean": statistics.mean(grug_utils),
                    "stdev": statistics.stdev(grug_utils)
                },
                "opponent_util": {
                    "mean": statistics.mean(opponent_utils),
                    "stdev": statistics.stdev(opponent_utils)
                },
                "nash_product": {
                    "mean": statistics.mean(nash_products),
                    "stdev": statistics.stdev(nash_products)
                },
                "social_welfare": {
                    "mean": statistics.mean(social_welfares),
                    "stdev": statistics.stdev(social_welfares)
                },
                "success_rate": results.count("agreement") / len(results)
            }
            with open(f"{res_dir}/RESULTS_SUMMARY_AGGREGATE.json", "w") as f:
                f.write(json.dumps(summary, indent=2))
            if MATPLOTLIB:
                save_as_image(f"{agent_name} - {domain}", summary,
                              f"{res_dir}/RESULTS_SUMMARY.png")

def parser_init():
    parser.add_argument(
        "--samples",
        metavar='N',
        type=int,
        help="Number of samples",
        default=5)
    parser.add_argument(
        "--frequency",
        metavar='M',
        type=int,
        help="Rate of change of the pattern, -1 for every session",
        default=-1)
    parser.add_argument(
        "--fallback-tol",
        metavar='X.X',
        type=float,
        help="Distance from utility range media for fallback bid",
        default=0.05
    )
    parser.add_argument(
        "--type",
        choices=['standard', 'opponent', 'random', 'mutation', 'generation'],
        help="PonPokoGeneration type to use",
        default='standard')
    parser.add_argument(
        "--domains",
        nargs='*',
        help="List of domains to use",
        default=['0', '1'])
    parser.add_argument(
        "--agents",
        nargs='*',
        help="List of agents to use",
        default=['BoulwareAgent', 'PonPokoParty', 'ConcederAgent'])
    parser.add_argument(
        '--matplotlib',
        action='store_true',
        help="Whether to generate an image")
    parser.add_argument(
        "--opponent-epsilon",
        metavar='Y.Y',
        type=float,
        help="Inter-bid change to classify opponent as conceder or hardliner",
        default=0.25
    )

if __name__ == "__main__":
    parser_init()
    args = parser.parse_args()
    
    SAMPLES = args.samples

    domains = ["domain0" + x for x in args.domains]
    samples = args.samples
    opponents = [
        agent for agent in AGENTS if agent.split(".")[-1] in args.agents
    ]
    ponpoko_params = {
        "patternChangeDelay": args.frequency,
        "generatorType": TYPES[args.type],
        "fallbackBidUtilRange": args.fallback_tol,
        "opponentEpsilon": args.opponent_epsilon
    }
    PARAMS = ponpoko_params

    MATPLOTLIB = args.matplotlib

    process_list = []
    for domain in domains:
        for opponent in opponents:
            run_process = Process(target=run_sessions, args=(domain, opponent))
            run_process.start()
            process_list.append(run_process)
    for process in process_list:
        process.join()

    analyse_results()
