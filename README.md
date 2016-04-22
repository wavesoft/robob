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

Let's say that you are curious to measure the bandwidth between some machines for different TCP window sizes. You could start by defining your `metrics` and your `test-case`:

```yaml
metrics:
  - name: bandwidth
    units: "MB/s"

test-case:
  window_size: [ 64, 128, 256, 512, 1024, 2048 ]
```

Then you should provide some details about the machines you will run your measurements on:

```yaml
nodes:
  - name: node1
    host: 192.168.1.1

  - name: node2
    host: 192.168.1.2
```

Then we need to know to to get a shell on these machines. Since they are obviously not the machine you will be running the test on, you could use `ssh` to access them:

```yaml
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
```

Allright, we know what we need to measure and where to perform the measurements. Now we need to know what we are going to run. I would suggest iperf for this particular case:

```yaml
apps:
  - name: iperf_server
    binary: /usr/bin/iperf
    args: [ "-y", "C", "-s" ]

  - name: iperf_client
    binary: /usr/bin/iperf
    args: [ "-y", "C", "-c", "192.168.1.1" ]
```

But it's command-line must change now for every test. And this hard-coded IP address does not look like a good idea. Thankfully you can use `${macros}` in roBob:

```yaml
apps:
  - name: iperf_server
    binary: /usr/bin/iperf
    args: [ "-y", "C", "-s", "-w", "${window-size}" ]

  - name: iperf_client
    binary: /usr/bin/iperf
    args: [ "-y", "C", "-c", "${remote}", "-w", "${window-size}" ]
```

The `${remote}` macro is not yet defined, but don't worry about it yet. The `${window-size}` macro will change with the current value of the window size for every test.

Now there is one last piece left: We need to tell roBob how to parse iperf's output. Having a look on a typical `iperf -y C` output (using CSV-like representation) we see the following:

```
~$ iperf -s -y C
20160422110043,192.168.1.1,5001,192.168.1.2,34198,4,0.0-10.0,41106931712,32865303629
```

That's qutie simple. It's a comma-separated list of the following values: _Timestamp_, _Source IP_, _Source Port_, _Remote IP_, _Remote Port_, _ID_, _Interval_, _Transfer Bytes_ and _Bandwidth (Bytes/sec)_. We are interested on the 9th value.

We now need to define a `parser` that is capable of understanding this output. There are various parsers available in robob, with the most important being `robob.parser.regex` and the `robob.parser.split`. Since the iperf output is quite simple to parse we don't need to mess with regular expressions. So we can use the simple splitter:

```yaml
parsers:
  - name: iperf_parser
    class: robob.parser.split
    separator: ","            # Split on commas
    match:
      - col: 8                # Get the 9th column (0=first)
        name: bandwidth       # And put it on the bandwidth metric
```

And we need to attach this parser to the application:

```yaml
apps:
  - name: iperf_server
    binary: /usr/bin/iperf
    args: [ "-y", "C", "-s", "-w", "${window-size}" ]
    parser: iperf_parser

  - name: iperf_client
    binary: /usr/bin/iperf
    args: [ "-y", "C", "-c", "${remote}", "-w", "${window-size}" ]
    parser: iperf_parser
```

Now that we have everything defined, we just need to put them together. When a test is started, roBob is openning one or more `streams` to the nodes and it launches your application.

In our example, we have two streams (one for the server and one for the client). Just to be safe, we are going to add some delay before starting the client in order to make sure the server is running first:

```yaml
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
```

Now we can save our specifications and start the benchmark!

```
~$ robob.py iperf.yaml
```

