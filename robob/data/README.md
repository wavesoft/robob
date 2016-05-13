
# Data Directory

This directory exposes various YAML fragments that you can use in your specifications document. 

## Streamlets

Streamlets are code fragments that run in parallel with your stream and collect additional information about the runing process. To use the stock streamlets you have to load them like this:

```yaml
-load:
    ${robob.streamlets}/uptime.yaml
```

