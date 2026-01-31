# Debug Operations in Kubernetes

Kubernetes provides several commands to help you troubleshoot and debug issues with your pods and containers. This reference page describes common debugging operations and the commands you can use to diagnose problems in your cluster.

## Prerequisites

- A running Kubernetes cluster
- kubectl command-line tool installed and configured
- Basic familiarity with Kubernetes pods and containers

## Common Debug Commands

### List Pods

Use the `kubectl get pods` command to retrieve a list of all pods in a namespace along with their current status. 

```shell
kubectl get pods --namespace <namespace-name>
```

**Output:**

```shell
NAME                     READY   STATUS    RESTARTS   AGE
nginx-6799fc88d8-zqm8j   1/1     Running   0          24h
redis-584c7b8dd-xkwvp    1/1     Running   1          12h
```

This command displays: 
- **NAME**: The pod name
- **READY**: The number of containers ready versus the total number of containers
- **STATUS**: The current phase of the pod (Running, Pending, Failed, etc.)
- **RESTARTS**: The number of times the pod has restarted
- **AGE**:  How long the pod has been running

### View Pod Logs

Use the `kubectl logs` command to view the logs from a specific container.  This helps you diagnose issues by examining application output and error messages.

```shell
kubectl logs <pod-name> --namespace <namespace-name>
```

For pods with multiple containers, specify the container name:

```shell
kubectl logs <pod-name> --container <container-name> --namespace <namespace-name>
```

Add the `--previous` flag to view logs from a crashed or restarted container:

```shell
kubectl logs <pod-name> --previous --namespace <namespace-name>
```

### Debug with Ephemeral Containers

The `kubectl debug` command creates a copy of a pod with additional debugging tools.  This is useful when your container image lacks debugging utilities or when you need to troubleshoot a container that is crash-looping.

```shell
kubectl debug <pod-name> --image=<debug-image> --target=<container-name>
```

**Note:** The ephemeral debug container persists even if the target container terminates, allowing you to inspect the state after a crash.

## kubectl CLI

The kubectl command-line tool communicates with the Kubernetes API server to manage cluster resources. You can use kubectl to create, inspect, update, and delete Kubernetes objects.

For a complete list of available commands, review the [kubectl command reference](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands).

## Resources

- [kubectl Command Reference](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands)
- [Debug Running Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/)
- [Kubernetes Overview](https://kubernetes.io/docs/concepts/overview/)