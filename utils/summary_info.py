import json


def print_party_data(data, party):
    print(f"=============\n{party}\n=============")
    values = [
        summary for summary in data
        if summary['agent_1'] == party or summary['agent_2'] == party
    ]
    total_length = len(values)
    total_agreed = len(
        [summary for summary in values if summary['result'] == 'agreement'])
    print(total_length, total_agreed)
    if total_length != 0:
        ratio = round((total_agreed / total_length) * 100)
    else:
        ratio = 100

    print(f"Succeeded: {ratio}%\nFailed: {100 - ratio}%")

    print("\n-------------\nAs first negotating party\n-------------")
    first_agent = [
        summary for summary in values if summary['agent_1'] == party
    ]
    first_values = sum([summary['utility_1'] for summary in first_agent])
    first_average = first_values / len(first_agent)
    print(f"Average utility: {first_average}")

    first_agreed_agent = [
        summary for summary in values if summary['utility_1'] != 0.0
    ]
    first_agreed_values = sum(
        [summary['utility_1'] for summary in first_agreed_agent])
    first_agreed_average = first_agreed_values / len(first_agreed_agent)
    print(f"Average agreed utility: {first_agreed_average}")

    print("\n-------------\nAs second negotating party\n-------------")
    second_agent = [
        summary for summary in values if summary['agent_2'] == party
    ]
    second_values = sum([summary['utility_2'] for summary in second_agent])
    second_average = second_values / len(second_agent)
    print(f"Average utility: {second_average}")

    second_agreed_agent = [
        summary for summary in values if summary['utility_2'] != 0.0
    ]
    second_agreed_values = sum(
        [summary['utility_2'] for summary in second_agreed_agent])
    second_agreed_average = second_agreed_values / len(second_agreed_agent)

    print(f"Average agreed utility: {second_agreed_average}")

    print("\n-------------\nTotal\n-------------")
    average_total = (first_average + second_average) / 2
    average_agreed_total = (first_agreed_average + second_agreed_average) / 2
    print(f"Average total utility: {average_total}")
    print(f"Average agreed total utility: {average_agreed_total}")

    nash_list = [summary['nash_product'] for summary in values]
    welfare_list = [summary['social_welfare'] for summary in values]
    average_nash = sum(nash_list) / len(nash_list)
    average_welfare = sum(welfare_list) / len(welfare_list)
    print(f"Average Nash Product: {average_nash}")
    print(f"Social welfare: {average_welfare}")
    print()
    return average_total, average_nash, average_welfare


with open('results/results_summaries.json') as f:
    content = ''.join(f.readlines())
    data = json.JSONDecoder().decode(content)

    result = {}
    for party in [
            "BoulwareAgent", "ConcederAgent", "HardlinerAgent", "LinearAgent",
            "RandomAgent", "StupidAgent", "TemplateAgent", "CustomAgent",
            "RandomParty", "PonPokoParty"
    ]:
        result[party] = print_party_data(data, party)

    print("=============\nFinal\n=============")
    average_utility = sum([x[0] for x in result.values()]) / len(result)
    average_nash = sum([x[1] for x in result.values()]) / len(result)
    average_welfare = sum([x[2] for x in result.values()]) / len(result)
    print(f"Average utility: {average_utility}")
    print(f"Average nash: {average_nash}")
    print(f"Average welfare: {average_welfare}\n")

    sort = reversed(sorted(result, key=lambda k: result[k][0]))

    index = 0
    print("Party\t\t\t\t Utility\t\t\t Nash Product\t\t\t Welfare")
    for party in sort:
        value = round(result[party][0], 4)
        relative = round(average_utility - value, 4)
        percentage = 100 - round((value / average_utility) * 100)

        nash = round(result[party][1], 4)
        nash_relative = round(average_nash - nash, 4)

        welfare = round(result[party][2], 4)
        welfare_relative = round(average_welfare - welfare, 4)

        print(
            f"[{index}] {party}:\t\t {value} ({relative}, {percentage}%)"
            f"\t\t {nash}({nash_relative})\t\t\t{welfare} ({welfare_relative})"
        )
        index += 1
