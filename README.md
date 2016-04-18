# roBOB (robot-benchmark)

**roBOB** is a small python application that simplifies the creation and execution of benchamrks in local and/or remote nodes and automates the collection of results.

It reads rules from a YAML specifications file for how to execute your application and how to analyze it's output. It then connects to the nodes you have specified, executes your command and crawls the output.

## Example

The following benchmark demonstrates how to use **roBOB** to collect bandwidth measurements between two nodes for different TCP window sizes

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

