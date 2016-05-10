roBOB (robot-benchmark)
=======================

.. image:: https://raw.githubusercontent.com/wavesoft/robob/master/doc/robob.png
  :target: https://github.com/wavesoft/robob
  :align: left

**roBob** is python automation tool that simplifies the collection of measurements over repetitive tasks, and the automatic creation of reports. 

Do you have to run some benchmarks? Do you need to run some tasks over night and collect the numbers? Are you using custom solutions to achieve this? Robob helps you achieve this in every environment! It launches your application on a virtual terminal, starts your application, cralws it's output, collects numbers and creates reports for you!

It uses a powerful, extensible, human-readable YAML ruleset for defining your specifications.

You can learn more on the Wiki Page: https://github.com/wavesoft/robob/wiki !

Installing
----------

Robob is available on PyPI so you can install it with pip:

.. code-block::

    pip install robob

Usage
-----

To launch a benchmark you only need to specify the path to the specifications file you want to use:

.. code-block::

    robob benchmarks/mybenchmark.yaml

Example
^^^^^^^

The following specification file from the Simple Example (https://github.com/wavesoft/robob/wiki/Simple-Example) demonstrates how to use roBob to run iperf between two machines for different window sizes:

.. code-block:: yaml

    # What metrics we will be tracking
    metrics:
      - name: bandwidth
        units: "B/s"

    # Which test cases are we going to run
    test-case:
      window_size: [ 64, 128, 256, 512, 1024, 2048 ]

    # Which nodes are involved on this test
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
              key: /path/to/private_key

    # What application(s) to start
    apps:
      - name: iperf_server
        binary: /usr/bin/iperf
        args: [ "-y", "C", "-s", "-w", "${window-size}" ]
        parser: iperf_parser

      - name: iperf_client
        binary: /usr/bin/iperf
        args: [ "-y", "C", "-c", "${remote}", "-w", "${window-size}" ]
        parser: iperf_parser

    # How to parse their output
    parsers:
      - name: iperf_parser
        class: robob.parser.split
        separator: ","            # Split on commas
        match:
          - col: 8                # Get the 9th column (0=first)
            name: bandwidth       # And put it on the bandwidth metric

    # Which streams to open in order to run the test
    streams:
      - node: node1       # On node 1
        app: iperf_server # Start iperf server

      - node: node2       # On node 2
        app: iperf_client # Start iperf client
        delay: 5s         # After 5 seconds
        # We also need to define the '${remote}' macro
        # to point on the IP address of the server
        define:
          remote: "${node1.host}"

