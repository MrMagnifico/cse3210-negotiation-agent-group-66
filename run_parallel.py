import json
import statistics
from pathlib import Path
from multiprocessing import Process

from utils.plot_trace import plot_trace
from utils.runners import run_session

SAMPLES = 10
domains = [
    "domain00", "domain01", "domain02", "domain03", "domain04",
    "domain05", "domain06", "domain07", "domain08", "domain09"
]
opponents = [
    "agents.boulware_agent.boulware_agent.BoulwareAgent",
    "agents.conceder_agent.conceder_agent.ConcederAgent",
    "agents.ponpoko_base_agent.ponpoko.ponpoko.PonPokoParty"
]
ponpoko_params = {
    "patternChangeFrequency": -1
}

def run_sessions(domain, opponent):
    # Create settings and generate results
    agents = [
        "agents.ponpokoagent.ponpoko.ponpoko.PonPokoParty",
        opponent
    ]
    profiles = [
        f"domains/{domain}/profileA.json",
        f"domains/{domain}/profileB.json"
    ]
    settings = {
        "agents": agents,
        "profiles": profiles,
        "deadline_rounds": 200,
        "ponpoko_params": ponpoko_params
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

if __name__ == "__main__":
    process_list = []
    for domain in domains:
        for opponent in opponents:
            run_process = Process(
                target=run_sessions,
                args=(domain, opponent))
            run_process.start()
            process_list.append(run_process)
    for process in process_list:
        process.join()

    analyse_results()
