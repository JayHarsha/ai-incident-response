package com.incidentplatform.mcp;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/mcp")
@Slf4j
public class McpController {

    private final McpToolService toolService;

    public McpController(McpToolService toolService) {
        this.toolService = toolService;
    }

    /**
     * Single endpoint for all MCP JSON-RPC 2.0 messages (Streamable HTTP transport).
     * Handles: initialize, notifications/initialized, tools/list, tools/call
     */
    @SuppressWarnings("unchecked")
    @PostMapping(consumes = "application/json", produces = "application/json")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        String method = (String) request.get("method");
        Object id = request.get("id");

        // Notifications have no id and expect no response body
        if (method != null && method.startsWith("notifications/")) {
            return ResponseEntity.ok(Map.of());
        }

        try {
            return switch (method != null ? method : "") {
                case "initialize" ->
                    // Return Mcp-Session-Id header as required by the Streamable HTTP transport spec
                    ResponseEntity.ok()
                            .header("Mcp-Session-Id", UUID.randomUUID().toString())
                            .body(Map.of(
                                    "jsonrpc", "2.0",
                                    "id", id,
                                    "result", Map.of(
                                            "protocolVersion", "2024-11-05",
                                            "serverInfo", Map.of("name", "incident-service", "version", "1.0.0"),
                                            "capabilities", Map.of("tools", Map.of())
                                    )
                            ));
                case "tools/list" -> respond(id, Map.of("tools", toolService.definitions()));
                case "tools/call" -> {
                    Map<String, Object> params = (Map<String, Object>) request.get("params");
                    String toolName = (String) params.get("name");
                    Map<String, Object> args = (Map<String, Object>) params.getOrDefault("arguments", Map.of());
                    String text = toolService.execute(toolName, args);
                    yield respond(id, Map.of("content", List.of(Map.of("type", "text", "text", text))));
                }
                default -> error(id, -32601, "Method not found: " + method);
            };
        } catch (Exception e) {
            log.error("MCP tool execution failed for method={}: {}", method, e.getMessage());
            return error(id, -32603, e.getMessage());
        }
    }

    /** Client may DELETE the session to signal it's done — stateless server just acknowledges. */
    @DeleteMapping
    public ResponseEntity<Void> deleteSession(
            @RequestHeader(value = "Mcp-Session-Id", required = false) String sessionId) {
        log.debug("MCP session terminated: {}", sessionId);
        return ResponseEntity.ok().build();
    }

    private ResponseEntity<Map<String, Object>> respond(Object id, Map<String, Object> result) {
        return ResponseEntity.ok(Map.of("jsonrpc", "2.0", "id", id, "result", result));
    }

    private ResponseEntity<Map<String, Object>> error(Object id, int code, String message) {
        return ResponseEntity.ok(Map.of(
                "jsonrpc", "2.0",
                "id", id != null ? id : 0,
                "error", Map.of("code", code, "message", message)
        ));
    }
}
