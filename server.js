import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import * as z from "zod/v4";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const bridgePath = path.join(__dirname, "bridge", "mt5_bridge.py");
const pythonBin = process.env.PYTHON_BIN || (process.platform === "win32" ? "py" : "python");
const defaultSymbol = process.env.MT5_SYMBOL || "XAUUSD_l";

const TIMEFRAMES = ["M1", "M2", "M3", "M4", "M5", "M6", "M10", "M12", "M15", "M20", "M30", "H1", "H2", "H3", "H4", "H6", "H8", "H12", "D1", "W1", "MN1"];
const timeframeSchema = z.enum(TIMEFRAMES);

function jsonToolResult(data) {
  return {
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }]
  };
}

function runBridge(action, payload = {}) {
  return new Promise((resolve, reject) => {
    const args = [];
    if (process.platform === "win32" && pythonBin.toLowerCase() === "py") {
      args.push("-3");
    }
    args.push(bridgePath, action, JSON.stringify(payload));

    const child = spawn(pythonBin, args, {
      cwd: __dirname,
      windowsHide: true,
      env: process.env,
      stdio: ["ignore", "pipe", "pipe"]
    });

    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", chunk => { stdout += chunk; });
    child.stderr.on("data", chunk => { stderr += chunk; });

    child.on("error", error => {
      reject(new Error(`Failed to start Python bridge: ${error.message}`));
    });

    child.on("close", code => {
      if (code !== 0) {
        reject(new Error(stderr.trim() || stdout.trim() || `MT5 bridge exited with code ${code}`));
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(new Error(`Invalid JSON from MT5 bridge: ${error.message}. Output: ${stdout.slice(0, 500)}`));
      }
    });
  });
}

async function execute(action, payload) {
  try {
    return jsonToolResult(await runBridge(action, payload));
  } catch (error) {
    return {
      content: [{ type: "text", text: error instanceof Error ? error.message : String(error) }],
      isError: true
    };
  }
}

const server = new McpServer({
  name: "pouria-mt5-mcp",
  version: "0.1.0"
});

server.registerTool("mt5_status", {
  title: "MT5 Status",
  description: "Check whether the local MetaTrader 5 terminal and Python integration are available. Read-only.",
  inputSchema: {}
}, async () => execute("status", { symbol: defaultSymbol }));

server.registerTool("get_symbol_info", {
  title: "Get Symbol Info",
  description: "Return trading/specification information for an MT5 symbol. Read-only.",
  inputSchema: {
    symbol: z.string().min(1).default(defaultSymbol)
  }
}, async ({ symbol }) => execute("symbol_info", { symbol }));

server.registerTool("get_tick", {
  title: "Get Latest Tick",
  description: "Return the latest MT5 tick for a symbol, including bid, ask, last and timestamp. Read-only.",
  inputSchema: {
    symbol: z.string().min(1).default(defaultSymbol)
  }
}, async ({ symbol }) => execute("tick", { symbol }));

server.registerTool("get_candles", {
  title: "Get Candles",
  description: "Return recent OHLC candles from MT5. By default only closed candles are returned; current forming candle is excluded.",
  inputSchema: {
    symbol: z.string().min(1).default(defaultSymbol),
    timeframe: timeframeSchema.default("M5"),
    count: z.number().int().min(1).max(5000).default(500),
    closed_only: z.boolean().default(true)
  }
}, async ({ symbol, timeframe, count, closed_only }) => execute("candles", { symbol, timeframe, count, closed_only }));

server.registerTool("get_market_snapshot", {
  title: "Get Multi-Timeframe Snapshot",
  description: "Return latest tick plus recent closed candles for multiple MT5 timeframes in one read-only call.",
  inputSchema: {
    symbol: z.string().min(1).default(defaultSymbol),
    timeframes: z.array(timeframeSchema).min(1).max(8).default(["H1", "M15", "M5", "M1"]),
    bars_per_timeframe: z.number().int().min(10).max(1000).default(300),
    closed_only: z.boolean().default(true)
  }
}, async ({ symbol, timeframes, bars_per_timeframe, closed_only }) => execute("snapshot", {
  symbol,
  timeframes,
  bars_per_timeframe,
  closed_only
}));

server.registerTool("get_account_info", {
  title: "Get Account Info",
  description: "Return non-credential MT5 account metrics such as balance, equity, margin and leverage. Read-only.",
  inputSchema: {}
}, async () => execute("account_info", {}));

server.registerTool("get_positions", {
  title: "Get Open Positions",
  description: "Return current open MT5 positions, optionally filtered by symbol. Read-only; does not place, modify or close orders.",
  inputSchema: {
    symbol: z.string().min(1).optional()
  }
}, async ({ symbol }) => execute("positions", { symbol: symbol || null }));

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("pouria-mt5-mcp running on stdio (read-only)");
}

main().catch(error => {
  console.error("MCP server fatal error:", error);
  process.exit(1);
});
