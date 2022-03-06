# Negotiating Agent GrugAgent

GrugAgent is a modern negotiating agent based on the winner of
the 2017 edition of the Automated Negotiating Agent Competition held
by the Delft University of Technology. It has been made as the first
assignment of the CSE3210 Collaborative Artificial Intelligence
elective. It has been written by Valentijn van de Beek, William
Narchi, and Emirhan Demir. This guide assumes that you are using
the version hosted on github.com, otherwise the normal installation
instructions for Python based agents apply. For the Tomcat server
the same principles mostly apply, but the settings need to be set
manually. These are described below but are not tested due to a bug
with the SSL certificate used in the tomcat server.

## Resources

[Negotiating Agents (Catholijn M. Jonker, Koen V. Hindriks, Pascal Wiggers, Joost Broekens)](https://www.semanticscholar.org/paper/Negotiating-Agents-Jonker-Hindriks/34081e82d0575854fcbadd3d31183d3fafcab67f)
[Bayesian learning in negotiation (Dajun Zeng, Katia Sycara)](https://www.semanticscholar.org/paper/Bayesian-learning-in-negotiation-Zeng-Sycara/3146e6b8fa9470749397c2bff1d5f8910ef47a90)
[Multi-Issue Automated Negotiations Using Agents(K. Chari, M. Agrawal)](https://www.semanticscholar.org/paper/Multi-Issue-Automated-Negotiations-Using-Agents-Chari-Agrawal/50044ef3ed085117a25988d654261fc2cf7475e1)

# Directory overview

- directories:
    - `agents`: Contains directories with the agents. The
      `ponpokoagent/ponpoko` directory contains the template for this
      assignment.
	- `ponpokoagent/ponpoko/ponpoko.py` is the file containing the
      code for the agent including the opponent modeling.
	- `ponpokoagent/ponpoko/patterns.py` contains the generation which
      provides the patterns. It contains all the code for the standard
	  pattern, custom patterns and generating new patterns.
    - `domains`: Contains the domains which are problems over which
      the agents are supposed to negotiate.
    - `utils`: Arbitrary utilities (don't use).
- files:
    - `grugagent.py`: Main interface to test agents.
	- `run_parallel.py`: Command-line program to run
      tournaments in parallel and allows you to set the options for
      the agent using switches
    - `requirements.txt`: Python dependencies for your agent.
    - `requirements_allowed.txt`: Additional dependencies that you are
      allowed to use (ask TA's if you need unlisted packages).

## Quickstart
- Create a python environment: `python -m venv .py`
- Load the python enviornment: `source .py/bin/activate`
- Install the packages: `pip install --trusted-host tracinsy.ewi.tudelft.nl -r requirements.txt`
- Run the default tournaments: `python run_parallel.py`

When the program finishes running you can find the output in
results/`[domain]`. In that directory there is the general summary, a
figure with the normal distribution (provided `--matplotlib` is given)
and a JSON file detailing each run of the program. It is recommended
that the files are parsed using a tool such as
`[jq](https://stedolan.github.io/jq/).`

## Commandline arguments
GrugAgent contains a large variety of options which control the usage
and result of the agent. These can be changed manually in the code or,
more conviently, by using the switches provided by
`run_parallel.py`. You can always check what it accepts by passing it
the `-h` switch, but a more full explanation is given below.

### Options
- `samples`: Amount of times that each tournament is repeated. These
  are aggregated together at the end and are used to calculate
  interesting statistical data about the run.
- `frequency`: Number of turns before the agent switches to a
  different pattern. Corresponds to the `patternChangeDelay` setting
  parameter.
- `fallback-tol`: Defines the maximum difference between the chosen
  bid compared the median of all the bids. Corresponds to the
  `fallbackBidUtilRange` setting parameter.
- `types`: Allows the user to change between the different operating
  modes of PonPoko. They are described in detail below. This value
  is the same as the `generatorType` setting parameter and is a
  number between 1 and 5.
- `domains`: A list of integers between 0 and 9 which indicate which
  domains the tournaments are run on.
- `agents`: List of agents that are used as opponents in the
  tournament.
- `matplotlib`: Switch which generates a figure with the normal
  distribution defined by the output the aggregated samples.
- `opponent-epsilon-higher`: Change required before the opponent is
  classified as a hardliner. Called `opponentEpsilonLower` in the
  settings.
- `opponent-epsiolon-lower`: Change requried before the opponent is
  classified as a conceder. Corresponds to the `opponentEpsilonLower`
  setting parameter.

### Agents available
These are the agents which are available to be used in the
tournaments, more could be added easily by adding them to the
`agents/` directory.

- `BoulwareAgent`: Adjustable hardliner agent
- `ConcederAgent`: Conceder agent
- `Hardlineragent`: Hardliner agent
- `LinearAgent`: An agent that uses a linear formula to accept or
  reject bids
- `RandomAgent`: Randomly accepts or rejects bids
- `StupidAgent`: Always accepts the first bid
- `TemplateAgent`: Base agent provided by the university
- `CustomAgent`: Template agent provided by the university
- `RandomParty`: Version of the random agent
- `PonPokoParty`: Base PonPokoAgent

### PonPoko operator modes
In this project the goal was to find improvements which would cause
measurable better utility gain over the standard PonPokoAgent. To do
so four additional modes are added which represent different
modifications of the agent.

1. `standard`: Based directly on the ANAC 2017 paper and uses the base
   patterns
2. `opponent`: Version of Pon Poko with frequency opponent modeling
3. `random`: Randomly generates the parameter of the patterns
4. `mutation`: Uses mutation rules to change the operators used in the
   patterns
5. `generation`: Mutates the operators and uses random numbers for the
   parameters.

### More information

[More documentation can be found
here](https://tracinsy.ewi.tudelft.nl/pubtrac/GeniusWebPython/wiki/WikiStart). Part
of this documentation was written for the Java version of GeniusWeb,
but classes and functionality are left identical as much as possible.
