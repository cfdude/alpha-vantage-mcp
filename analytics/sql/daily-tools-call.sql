-- Daily tools/call count
-- Shows total MCP tool calls by date
SELECT 
    DATE(created_at) as date,
    COUNT(*) as daily_tool_calls
FROM mcp_analytics.mcp_logs 
WHERE method = 'tools/call'
GROUP BY DATE(created_at)
ORDER BY date DESC;