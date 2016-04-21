# roBOB (robot-benchmark)

![robob](https://raw.githubusercontent.com/wavesoft/robo-benchmark/master/doc/robob.png)

**roBob** is python tool that simplifies the collection of measurements over repetitive tasks, and the automatic creation of reports. 

Do you have to run some benchmarks? Do you need to run some tasks over night and collect the numbers? Are you using custom solutions to achieve this? Robob helps you achieve this in every environment! It launches your application on a virtual terminal, starts your application, cralws it's output, collects numbers and creates reports for you!

It uses a powerful, extensible, human-readable YAML ruleset for defining your specifications.

## Installing

Robob has a few requirements. To install them you can use pip:

```
pip install -r requirements.txt
```

## Usage

To launch a benchmark you only need to specify the path to the specifications file you want to use:

```
robob.py benchmarks/mybenchmark.yaml
```

### Example

The following benchmark demonstrates how to use **roBob** to collect bandwidth measurements between two nodes for different TCP window sizes

```yaml

# The test cases
test-cases:
    window-size: [ 64, 128, 256, 512, 1024, 2048 ]

# Which nodes takes place in this benchmark
nodes:

    - name: node1
      host: 192.168.1.1
      access:
          - class: robob.access.ssh
            username: user
            password: secret

    - name: node2
      host: 192.168.1.2
      access:
          - class: robob.access.ssh
            username: user
            password: secret

# Which applications takes pace in this benchmark
applications:

    - name: server
      binary: /usr/bin/iperf
      args: [ "-y", "C", "-s", "-w", "${window-size}" ]

    - name: client
      binary: /usr/bin/iperf
      args: [ "-y", "C", "-c", "${REMOTE}", "-w", "${window-size}" ]

# Which parser to use for analyzing this output
parsers:
    
    - name: iperf
      class: robob.parser.grid
      separator: ","
      match:
        - name: bw_in
          line: 0
          col: 7
        - name: bw_out
          line: 0
          col: 8

# Which streams to open (here is the actual work)
streams:
    
    - node: node1 # Start on node1 ..
      app: server # A server application ..
      parser: iperf # And parse it's output using the 'iperf' CSV parser

    - node: node2 # Also start on node2 ..
      app: client # A client application ..
      delay: 1 # With an 1 second delay ..
      variables: # That connects to the IP address of the node2
        REMOTE: "${node.node2.host}"

```

