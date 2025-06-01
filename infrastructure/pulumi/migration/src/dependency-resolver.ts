/**
 * Dependency Resolver for Pulumi Migration Framework
 * Handles dependency graph construction and topological sorting
 */

import {
    ResourceMapping,
    DependencyGraph,
    DependencyNode,
} from "./types";
import { Logger } from "./logger";

export class DependencyResolver {
    private logger: Logger;

    constructor(logger?: Logger) {
        this.logger = logger || new Logger("DependencyResolver");
    }

    /**
     * Build dependency graph from resource mappings
     */
    buildGraph(mappings: ResourceMapping[]): DependencyGraph {
        const graph: DependencyGraph = {
            nodes: new Map(),
            edges: new Map(),
        };

        // First pass: Create all nodes
        for (const mapping of mappings) {
            const nodeId = this.getResourceId(mapping);
            const node: DependencyNode = {
                resource: mapping.source,
                dependencies: mapping.dependencies || [],
                dependents: [],
                level: -1, // Will be calculated later
            };
            graph.nodes.set(nodeId, node);
            graph.edges.set(nodeId, new Set());
        }

        // Second pass: Build edges and dependents
        for (const mapping of mappings) {
            const nodeId = this.getResourceId(mapping);
            const node = graph.nodes.get(nodeId)!;

            for (const depId of mapping.dependencies) {
                // Add edge from this node to dependency
                graph.edges.get(nodeId)!.add(depId);

                // Add this node as dependent of the dependency
                const depNode = graph.nodes.get(depId);
                if (depNode) {
                    depNode.dependents.push(nodeId);
                } else {
                    this.logger.warn(`Dependency not found: ${depId} for resource ${nodeId}`);
                }
            }
        }

        // Calculate levels
        this.calculateLevels(graph);

        this.logger.info(`Built dependency graph with ${graph.nodes.size} nodes`);
        return graph;
    }

    /**
     * Calculate levels for each node (distance from root nodes)
     */
    private calculateLevels(graph: DependencyGraph): void {
        const visited = new Set<string>();
        const queue: string[] = [];

        // Find root nodes (no dependencies)
        for (const [nodeId, edges] of graph.edges.entries()) {
            if (edges.size === 0) {
                const node = graph.nodes.get(nodeId)!;
                node.level = 0;
                queue.push(nodeId);
            }
        }

        // BFS to calculate levels
        while (queue.length > 0) {
            const currentId = queue.shift()!;
            if (visited.has(currentId)) continue;
            visited.add(currentId);

            const currentNode = graph.nodes.get(currentId)!;
            
            // Process dependents
            for (const dependentId of currentNode.dependents) {
                const dependentNode = graph.nodes.get(dependentId)!;
                dependentNode.level = Math.max(
                    dependentNode.level,
                    currentNode.level + 1
                );
                queue.push(dependentId);
            }
        }
    }

    /**
     * Detect cycles in the dependency graph
     */
    detectCycles(graph: DependencyGraph): string[][] {
        const cycles: string[][] = [];
        const visited = new Set<string>();
        const recursionStack = new Set<string>();
        const path: string[] = [];

        const dfs = (nodeId: string): boolean => {
            visited.add(nodeId);
            recursionStack.add(nodeId);
            path.push(nodeId);

            const edges = graph.edges.get(nodeId) || new Set();
            for (const neighbor of edges) {
                if (!visited.has(neighbor)) {
                    if (dfs(neighbor)) {
                        return true;
                    }
                } else if (recursionStack.has(neighbor)) {
                    // Found a cycle
                    const cycleStart = path.indexOf(neighbor);
                    const cycle = path.slice(cycleStart);
                    cycles.push([...cycle, neighbor]);
                    this.logger.error(`Cycle detected: ${cycle.join(" -> ")} -> ${neighbor}`);
                    return true;
                }
            }

            path.pop();
            recursionStack.delete(nodeId);
            return false;
        };

        // Check each unvisited node
        for (const nodeId of graph.nodes.keys()) {
            if (!visited.has(nodeId)) {
                dfs(nodeId);
            }
        }

        return cycles;
    }

    /**
     * Perform topological sort on the graph
     */
    topologicalSort(graph: DependencyGraph): string[] {
        const result: string[] = [];
        const visited = new Set<string>();
        const tempVisited = new Set<string>();

        const visit = (nodeId: string): void => {
            if (tempVisited.has(nodeId)) {
                throw new Error(`Circular dependency detected at ${nodeId}`);
            }
            if (visited.has(nodeId)) {
                return;
            }

            tempVisited.add(nodeId);

            const edges = graph.edges.get(nodeId) || new Set();
            for (const neighbor of edges) {
                visit(neighbor);
            }

            tempVisited.delete(nodeId);
            visited.add(nodeId);
            result.push(nodeId);
        };

        // Visit all nodes
        for (const nodeId of graph.nodes.keys()) {
            if (!visited.has(nodeId)) {
                visit(nodeId);
            }
        }

        // Reverse to get correct order (dependencies first)
        return result.reverse();
    }

    /**
     * Get resources grouped by level
     */
    getLevels(graph: DependencyGraph): Map<number, string[]> {
        const levels = new Map<number, string[]>();

        for (const [nodeId, node] of graph.nodes.entries()) {
            const level = node.level;
            if (!levels.has(level)) {
                levels.set(level, []);
            }
            levels.get(level)!.push(nodeId);
        }

        // Sort levels by key
        const sortedLevels = new Map(
            Array.from(levels.entries()).sort((a, b) => a[0] - b[0])
        );

        this.logger.info(`Resources grouped into ${sortedLevels.size} levels`);
        return sortedLevels;
    }

    /**
     * Find all dependencies of a resource (transitive)
     */
    findAllDependencies(graph: DependencyGraph, resourceId: string): Set<string> {
        const dependencies = new Set<string>();
        const visited = new Set<string>();

        const traverse = (nodeId: string): void => {
            if (visited.has(nodeId)) return;
            visited.add(nodeId);

            const edges = graph.edges.get(nodeId) || new Set();
            for (const dep of edges) {
                dependencies.add(dep);
                traverse(dep);
            }
        };

        traverse(resourceId);
        return dependencies;
    }

    /**
     * Find all dependents of a resource (transitive)
     */
    findAllDependents(graph: DependencyGraph, resourceId: string): Set<string> {
        const dependents = new Set<string>();
        const visited = new Set<string>();

        const traverse = (nodeId: string): void => {
            if (visited.has(nodeId)) return;
            visited.add(nodeId);

            const node = graph.nodes.get(nodeId);
            if (node) {
                for (const dependent of node.dependents) {
                    dependents.add(dependent);
                    traverse(dependent);
                }
            }
        };

        traverse(resourceId);
        return dependents;
    }

    /**
     * Check if adding a dependency would create a cycle
     */
    wouldCreateCycle(
        graph: DependencyGraph,
        from: string,
        to: string
    ): boolean {
        // Temporarily add the edge
        const edges = graph.edges.get(from);
        if (!edges) return false;

        edges.add(to);

        // Check for cycles
        const cycles = this.detectCycles(graph);

        // Remove the temporary edge
        edges.delete(to);

        return cycles.length > 0;
    }

    /**
     * Get resource ID from mapping
     */
    private getResourceId(mapping: ResourceMapping): string {
        return `${mapping.source.type}:${mapping.source.name}`;
    }

    /**
     * Visualize the dependency graph (returns DOT format)
     */
    visualize(graph: DependencyGraph): string {
        const lines: string[] = ["digraph DependencyGraph {"];
        lines.push('  rankdir=LR;');
        lines.push('  node [shape=box];');

        // Group by levels
        const levels = this.getLevels(graph);
        for (const [level, nodes] of levels.entries()) {
            lines.push(`  subgraph cluster_${level} {`);
            lines.push(`    label="Level ${level}";`);
            lines.push(`    color=gray;`);
            
            for (const nodeId of nodes) {
                const node = graph.nodes.get(nodeId)!;
                const label = nodeId.replace(/:/g, '\\n');
                lines.push(`    "${nodeId}" [label="${label}"];`);
            }
            
            lines.push('  }');
        }

        // Add edges
        for (const [from, edges] of graph.edges.entries()) {
            for (const to of edges) {
                lines.push(`  "${from}" -> "${to}";`);
            }
        }

        lines.push('}');
        return lines.join('\n');
    }

    /**
     * Generate dependency report
     */
    generateReport(graph: DependencyGraph): string {
        const levels = this.getLevels(graph);
        const report = {
            summary: {
                totalResources: graph.nodes.size,
                totalDependencies: Array.from(graph.edges.values())
                    .reduce((sum, edges) => sum + edges.size, 0),
                levels: levels.size,
                rootResources: Array.from(graph.nodes.entries())
                    .filter(([_, node]) => node.level === 0)
                    .map(([id, _]) => id),
            },
            levels: Array.from(levels.entries()).map(([level, resources]) => ({
                level,
                resourceCount: resources.length,
                resources,
            })),
            complexResources: Array.from(graph.nodes.entries())
                .filter(([_, node]) => node.dependencies.length > 3)
                .map(([id, node]) => ({
                    resource: id,
                    dependencyCount: node.dependencies.length,
                    dependencies: node.dependencies,
                })),
        };

        return JSON.stringify(report, null, 2);
    }
}