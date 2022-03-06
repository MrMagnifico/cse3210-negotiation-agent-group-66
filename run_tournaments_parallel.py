import json
import os
from cgi import test
from multiprocessing import Process

from utils.runners import run_tournament
from utils.summary_info import print_party_data

# Settings to run a tournament:
#   We need to specify the classpath all agents that will participate in the tournament
#   We need to specify duos of preference profiles that will be played by the agents
#   We need to specify a deadline of amount of rounds we can negotiate before we end without agreement
tournament_settings = {
    "agents": [
        #        "agents.boulware_agent.boulware_agent.BoulwareAgent",
        #        "agents.conceder_agent.conceder_agent.ConcederAgent",
        #        "agents.hardliner_agent.hardliner_agent.HardlinerAgent",
        #        "agents.linear_agent.linear_agent.LinearAgent",
        "agents.random_agent.random_agent.RandomAgent",
        #        "agents.stupid_agent.stupid_agent.StupidAgent",
        #        "agents.template_agent.template_agent.TemplateAgent",
        #        "agents.custom_agents.custom_agent_0.CustomAgent",
        #        "agents.randomp.randomparty.RandomParty.RandomParty",
        "agents.ponpokoagent.ponpoko.ponpoko.PonPokoParty"
    ],
    "profile_sets": [
        ["domains/domain00/profileA.json", "domains/domain00/profileB.json"],
        ["domains/domain01/profileA.json", "domains/domain01/profileB.json"],
    ],
    "deadline_rounds":
    200,
    "ponpoko_params": {},
    "no_warning": 1
}


def run_test_tournament(tournament_settings, test_freq, gen_type, test_sample):
    tournament_settings["ponpoko_params"]["patternChangeDelay"] = test_freq
    tournament_settings["ponpoko_params"]["generatorType"] = gen_type

    # run a session and obtain results in dictionaries
    tournament, results_summaries = run_tournament(tournament_settings)

    # save the tournament settings for reference
    with open(f"results/tournament-test-({test_freq})-({test_sample}).json",
              "w") as f:
        f.write(json.dumps(tournament, indent=2))
    # save the result summaries
    with open(
            f"results/results_summaries-test-({test_freq})-({gen_type})-({test_sample}).json",
            "w") as f:
        f.write(json.dumps(results_summaries, indent=2))


def analyse_ponpoko_results(test_frequencies, test_samples):
    print("+++++++++++++++ PONPOKO RESULTS ANALYSIS +++++++++++++++")
    for type_ in test_types:
        for curr_freq in test_frequencies:
            for curr_sample in range(test_samples):
                print(
                    f"++++++++++ FREQUENCY {curr_freq} - SAMPLE {curr_sample} ++++++++++"
                )
                file_name = f"results/results_summaries-test-({curr_freq})-({type_})-({curr_sample}).json"
                with open(file_name) as file:
                    content = ''.join(file.readlines())
                    data = json.JSONDecoder().decode(content)
                    print_party_data(data, "PonPokoParty")


if __name__ == "__main__":
    # create results directory if it does not exist
    if not os.path.exists("results"):
        os.mkdir("results")

    test_frequencies = [-1]
    test_samples = 5
    test_types = range(1, 6)
    process_list = []

    for type_ in test_types:
        for curr_freq in test_frequencies:
            for curr_sample in range(test_samples):
                test_process = Process(target=run_test_tournament,
                                       args=(tournament_settings, curr_freq,
                                             type_, curr_sample))
                test_process.start()
                process_list.append(test_process)

    for process in process_list:
        process.join()

    analyse_ponpoko_results(test_frequencies, test_samples)
